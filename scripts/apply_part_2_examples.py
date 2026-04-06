#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from collections import Counter
import re
import sys
import xml.etree.ElementTree as ET

ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
SNAPSHOT_XML = ROOT_DIR / 'chatGPT_exp' / 'converted_dict.snapshot.xml'

KYR_TOK = r"[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'-]+"
HYPHEN_WORD_SPACE_RE = re.compile(r"\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-\s")
DOUBLE_HYPHEN_WORD_RE = re.compile(r"\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+\b")
TOKEN_RE = re.compile(r"\S+")
NON_TARGET_RUSSIAN_TOKENS = {"или"}
HYPHEN_FORM_RE = re.compile(r"\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-")
LEFT_RE = re.compile(rf"^(?P<left>{KYR_TOK}(?:\s+{KYR_TOK}){{0,5}})\s+(?P<right>.+)$")
RUS_START_RE = re.compile(r"^[а-яё\"«„(]", re.I)
ROMAN_RE = re.compile(r"\b[IVXLCM]+\b")
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<text>[^<]+)</blockquote>$', re.M)
EX_BLOCK_RE = re.compile(r'<ex>\s*<source>(.*?)</source>\s*<target>(.*?)</target>\s*</ex>', re.S)
SKIP_PREFIXES = (
    "(", "[", "см.", "ср.", "то же, что", "иначе", "обычно", "чаще", "иногда",
    "перен.", "уст.", "разг.", "неправ.", "точнее",
)
EXCLUDED_TEXTS = {
    'бөрүнүн жегенинен- м - кырды-кырдысы южн. волк уничтожает больше, чем съедает;',
    'жүгөрү сотолору сүт- камыр болуп жетилгеи початки кукурузы достигли молочно-восковой спелости;',
    'кетер кетпеси - арсар уедет он или нет- неизвестно;',
    'бош жүр- или боштон жүр ходить без дела, бездельничать;',
    'жалаа жап- или жалаа таң клеветать, хулить, возводить ложное обвинение.',
    'кароолго жеткир- или кароол келтир взять на прицел, взять на мушку;',
}

APPROVED_EXTRA_COUNTS: Counter[tuple[str, str]] = Counter({
    ('сөз алыш-', 'взять друг с друга слово:'): 1,
    ('үнүн бас-', 'заставить его замолчать:'): 1,
    ('муштум көрсөт-', 'пригрозить, припугнуть:'): 1,
    ('талоон кой-', 'разграбить: напасть;'): 1,
    ('тамеки чектир-', 'дать покурить или позволить покурить;'): 1,
})


def norm_xml_text(text: str) -> str:
    return text.strip()


def looks_like_reviewed_new_example(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    if text in EXCLUDED_TEXTS:
        return False
    if lowered.startswith(SKIP_PREFIXES):
        return False
    if '(' in text or ')' in text:
        return False
    if ROMAN_RE.search(text):
        return False
    if DOUBLE_HYPHEN_WORD_RE.search(text):
        return False
    if ':' in text[:40]:
        return False
    m = LEFT_RE.match(text)
    if not m:
        return False
    left = m.group('left')
    right = m.group('right').strip()
    if '-' not in left:
        return False
    if not HYPHEN_WORD_SPACE_RE.search(text):
        return False
    if not RUS_START_RE.match(right):
        return False
    return True


def split_example(text: str) -> tuple[str, str]:
    if "или" in text:
        hyphen_forms = list(HYPHEN_FORM_RE.finditer(text))
        if hyphen_forms:
            last = hyphen_forms[-1]
            return text[:last.end()].strip(), text[last.end():].strip()

    split_at = None
    for m in TOKEN_RE.finditer(text):
        token = m.group(0)
        if RUS_START_RE.match(token):
            if token.lower().strip('.,;:!?"«»„') in NON_TARGET_RUSSIAN_TOKENS:
                continue
            left = text[:m.start()].strip()
            if HYPHEN_WORD_SPACE_RE.search(left + " "):
                split_at = m.start()
                break
    if split_at is None:
        raise ValueError(f'Cannot split example candidate: {text}')
    return text[:split_at].strip(), text[split_at:].strip()


def load_snapshot_ex_pairs(snapshot_path: Path) -> list[tuple[str, str]]:
    text = snapshot_path.read_text(encoding='utf-8')
    return [
        (norm_xml_text(source), norm_xml_text(target))
        for source, target in EX_BLOCK_RE.findall(text)
    ]


def load_reviewed_new_pairs(snapshot_path: Path) -> set[tuple[str, str]]:
    root = ET.parse(snapshot_path).getroot()
    pairs: set[tuple[str, str]] = set()
    for elem in root.iter('blockquote'):
        if elem.find('.//wordLink') is not None:
            continue
        text = ''.join(elem.itertext()).strip()
        if looks_like_reviewed_new_example(text):
            pairs.add(split_example(text))
    return pairs


def build_approved_pairs() -> set[tuple[str, str]]:
    if not SNAPSHOT_XML.exists():
        raise FileNotFoundError(f'Snapshot not found: {SNAPSHOT_XML}')
    snapshot_pairs = set(load_snapshot_ex_pairs(SNAPSHOT_XML))
    reviewed_new_pairs = load_reviewed_new_pairs(SNAPSHOT_XML) - snapshot_pairs
    pairs = set(snapshot_pairs)
    pairs.update(reviewed_new_pairs)
    pairs.update(APPROVED_EXTRA_COUNTS)
    return pairs


def build_approved_raw_map(approved_pairs: set[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    return {f'{source} {target}': (source, target) for source, target in approved_pairs}


def build_allowed_counts() -> Counter[tuple[str, str]]:
    if not SNAPSHOT_XML.exists():
        raise FileNotFoundError(f'Snapshot not found: {SNAPSHOT_XML}')
    snapshot_pairs = set(load_snapshot_ex_pairs(SNAPSHOT_XML))
    counts: Counter[tuple[str, str]] = Counter(load_snapshot_ex_pairs(SNAPSHOT_XML))
    for pair in (load_reviewed_new_pairs(SNAPSHOT_XML) - snapshot_pairs):
        counts[pair] += 1
    counts.update(APPROVED_EXTRA_COUNTS)
    return counts


def apply_examples(
    text: str,
    approved_pairs: set[tuple[str, str]],
    approved_raw_map: dict[str, tuple[str, str]],
    allowed_counts: Counter[tuple[str, str]],
) -> tuple[str, int]:
    applied = 0
    applied_counts: Counter[tuple[str, str]] = Counter(
        (norm_xml_text(source), norm_xml_text(target))
        for source, target in EX_BLOCK_RE.findall(text)
    )

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        raw_text = match.group('text').strip()
        if raw_text in approved_raw_map:
            source, target = approved_raw_map[raw_text]
        else:
            try:
                source, target = split_example(raw_text)
            except ValueError:
                return match.group(0)
            if (source, target) not in approved_pairs:
                return match.group(0)
        pair = (source, target)
        if applied_counts[pair] >= allowed_counts[pair]:
            return match.group(0)
        indent = match.group('indent')
        applied += 1
        applied_counts[pair] += 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{source}</source>\n'
            f'{indent}\t<target>{target}</target>\n'
            f'{indent}</ex>'
        )

    return BLOCKQUOTE_RE.sub(repl, text), applied


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: apply_part_2_examples.py <input.xml> <output.xml>', file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    approved_pairs = build_approved_pairs()
    approved_raw_map = build_approved_raw_map(approved_pairs)
    allowed_counts = build_allowed_counts()
    text = input_path.read_text(encoding='utf-8')
    new_text, applied = apply_examples(text, approved_pairs, approved_raw_map, allowed_counts)
    output_path.write_text(new_text, encoding='utf-8')
    print(f'Applied {applied} part 2 example fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
