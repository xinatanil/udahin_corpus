#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import sys

KYR_TOK = r"[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'-]+"
HYPHEN_WORD_SPACE_RE = re.compile(r"\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-\s")
ILI_RE = re.compile(r"\bили\b", re.I)
SPLIT_RE = re.compile(r"^(?P<source>.*?\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-)\s+(?P<target>.+)$")
LEFT_RE = re.compile(rf"^(?P<left>{KYR_TOK}(?:\s+{KYR_TOK}){{0,5}})\s+(?P<right>.+)$")
RUS_START_RE = re.compile(r"^[а-яё\"«„(]", re.I)
ROMAN_RE = re.compile(r"\b[IVXLCM]+\b")
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<text>[^<]+)</blockquote>$', re.M)
SKIP_PREFIXES = (
    "(", "[", "см.", "ср.", "то же, что", "иначе", "обычно", "чаще", "иногда",
    "южн.", "сев.", "перен.", "этн.", "уст.", "разг.", "неправ.", "точнее",
)
META_WORDS = ("фольк.",)
EXCLUDED_TEXTS = {
    'бөрүнүн жегенинен- м - кырды-кырдысы южн. волк уничтожает больше, чем съедает;',
    'жүгөрү сотолору сүт- камыр болуп жетилгеи початки кукурузы достигли молочно-восковой спелости;',
}


def looks_like_example_candidate(text: str) -> bool:
    if not text:
        return False
    if text in EXCLUDED_TEXTS:
        return False
    lowered = text.lower()
    if lowered.startswith(SKIP_PREFIXES):
        return False
    if ILI_RE.search(text):
        return False
    if '(' in text or ')' in text:
        return False
    if ROMAN_RE.search(text):
        return False
    if any(meta in lowered for meta in META_WORDS):
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
    m = SPLIT_RE.match(text)
    if not m:
        raise ValueError(f'Cannot split example candidate: {text}')
    return m.group('source').strip(), m.group('target').strip()


def apply_examples(text: str) -> tuple[str, int]:
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        raw_text = match.group('text').strip()
        if not looks_like_example_candidate(raw_text):
            return match.group(0)
        source, target = split_example(raw_text)
        indent = match.group('indent')
        applied += 1
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
    text = input_path.read_text(encoding='utf-8')
    new_text, applied = apply_examples(text)
    output_path.write_text(new_text, encoding='utf-8')
    print(f'Applied {applied} part 2 example fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
