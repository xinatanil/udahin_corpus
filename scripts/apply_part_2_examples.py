#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
# Checked-in approvals keep part 2 example conversions deterministic and snapshot-free.
APPROVED_COUNTS_JSON = ROOT_DIR / 'scripts' / 'data' / 'part_2_examples_approved.json'

KYR_TOK = r"[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'-]+"
HYPHEN_WORD_SPACE_RE = re.compile(r"\b[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі]+-\s")
TOKEN_RE = re.compile(r"\S+")
NON_TARGET_RUSSIAN_TOKENS = {"или"}
SOURCE_CHUNK_RE = rf"(?:{KYR_TOK}\s+){{0,5}}{KYR_TOK}-"
SOURCE_CHAIN_RE = re.compile(
    rf"^(?P<source>{SOURCE_CHUNK_RE}(?:\s+или\s+{SOURCE_CHUNK_RE})*)\s+(?P<target>.+)$"
)
RUS_START_RE = re.compile(r"^[а-яё\"«„(]", re.I)
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<text>[^<]+)</blockquote>$', re.M)
EX_BLOCK_RE = re.compile(r'<ex>\s*<source>(.*?)</source>\s*<target>(.*?)</target>\s*</ex>', re.S)


def norm_xml_text(text: str) -> str:
    return text.strip()


def split_example(text: str) -> tuple[str, str]:
    chain_match = SOURCE_CHAIN_RE.match(text)
    if chain_match:
        return chain_match.group('source').strip(), chain_match.group('target').strip()

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


def build_approved_raw_map(approved_pairs: set[tuple[str, str]]) -> dict[str, tuple[str, str]]:
    return {f'{source} {target}': (source, target) for source, target in approved_pairs}


def load_allowed_counts(path: Path) -> Counter[tuple[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f'Approved examples data not found: {path}')
    data = json.loads(path.read_text(encoding='utf-8'))
    counts: Counter[tuple[str, str]] = Counter()
    for source, target, count in data['entries']:
        counts[(norm_xml_text(source), norm_xml_text(target))] = count
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
    allowed_counts = load_allowed_counts(APPROVED_COUNTS_JSON)
    approved_pairs = set(allowed_counts)
    approved_raw_map = build_approved_raw_map(approved_pairs)
    text = input_path.read_text(encoding='utf-8')
    new_text, applied = apply_examples(text, approved_pairs, approved_raw_map, allowed_counts)
    output_path.write_text(new_text, encoding='utf-8')
    print(f'Applied {applied} part 2 example fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
