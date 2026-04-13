#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys


ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
MANUAL_MARKDOWN_HTML = ROOT_DIR / 'scripts' / 'data' / 'manual_markdown.html'
MANUAL_BLOCKQUOTE_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.S)
BLOCKQUOTE_LINE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<text>.*?)</blockquote>$', re.M)
SEPARATOR = '##'


def load_manual_pairs(path: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f'Manual markdown file not found: {path}')

    text = path.read_text(encoding='utf-8')
    pairs: list[tuple[str, str, str]] = []
    unmarked: list[str] = []
    for match in MANUAL_BLOCKQUOTE_RE.finditer(text):
        blockquote_text = match.group(1)
        if SEPARATOR not in blockquote_text:
            unmarked.append(blockquote_text.strip())
            continue
        source, target = blockquote_text.split(SEPARATOR, 1)
        source = source.strip()
        target = target.strip()
        raw = blockquote_text.replace(SEPARATOR, '', 1)
        pairs.append((raw, source, target))
    return pairs, unmarked


def apply_manual_examples(
    xml: str,
    manual_pairs: list[tuple[str, str, str]],
) -> tuple[str, int, list[str]]:
    allowed_counts = Counter(raw for raw, _, _ in manual_pairs)
    pair_map = {raw: (source, target) for raw, source, target in manual_pairs}
    original_counts = Counter(match.group('text') for match in BLOCKQUOTE_LINE_RE.finditer(xml))
    available_counts = original_counts.copy()
    remaining_allowed = allowed_counts.copy()
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        raw_text = match.group('text')
        if raw_text not in pair_map:
            return match.group(0)
        if remaining_allowed[raw_text] <= 0:
            return match.group(0)
        if available_counts[raw_text] <= 0:
            return match.group(0)

        source, target = pair_map[raw_text]
        indent = match.group('indent')
        applied += 1
        available_counts[raw_text] -= 1
        remaining_allowed[raw_text] -= 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{source}</source>\n'
            f'{indent}\t<target>{target}</target>\n'
            f'{indent}</ex>'
        )

    missing = []
    for raw, count in allowed_counts.items():
        if original_counts[raw] < count:
            missing.extend([raw] * (count - original_counts[raw]))
    return BLOCKQUOTE_LINE_RE.sub(repl, xml), applied, missing


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: apply_manual_markdown_examples.py <input.xml> <output.xml>', file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    manual_pairs, unmarked = load_manual_pairs(MANUAL_MARKDOWN_HTML)
    xml = input_path.read_text(encoding='utf-8')
    new_xml, applied, missing = apply_manual_examples(xml, manual_pairs)
    output_path.write_text(new_xml, encoding='utf-8')

    print(f'Applied {applied} manual markdown example fix(es)')
    if unmarked:
        print(f'WARNING: {len(unmarked)} manual blockquote(s) without ## separator:')
        for item in unmarked:
            print(f'  - {item}')
    if missing:
        print(f'WARNING: {len(missing)} manual blockquote(s) with ## not found in XML:')
        for item in missing:
            print(f'  - {item}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
