#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys


ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
MANUAL_MARKDOWN_HTML = ROOT_DIR / 'pipeline_part2' / 'data' / 'manual_markdown.html'
AI_MARKDOWN_XML = ROOT_DIR / 'pipeline_part2' / 'data' / 'ai_markdown.xml'
MANUAL_BLOCKQUOTE_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.S)
BLOCKQUOTE_LINE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<text>.*?)</blockquote>$', re.M)
SEPARATOR = '##'


def load_markdown_pairs(path: Path) -> tuple[list[tuple[str, str, str]], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f'Markdown example file not found: {path}')

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


def apply_markdown_examples(
    xml: str,
    markdown_pairs: list[tuple[str, str, str]],
) -> tuple[str, int, list[str]]:
    pair_map = {raw: (source, target) for raw, source, target in markdown_pairs}
    original_counts = Counter(match.group('text') for match in BLOCKQUOTE_LINE_RE.finditer(xml))
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        raw_text = match.group('text')
        if raw_text not in pair_map:
            return match.group(0)

        source, target = pair_map[raw_text]
        indent = match.group('indent')
        applied += 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{source}</source>\n'
            f'{indent}\t<target>{target}</target>\n'
            f'{indent}</ex>'
        )

    missing = [raw for raw in pair_map if original_counts[raw] == 0]
    return BLOCKQUOTE_LINE_RE.sub(repl, xml), applied, missing


def normalize_collapsed_hyphen_examples(
    xml: str,
    markdown_pairs: list[tuple[str, str, str]],
) -> tuple[str, int]:
    collapsed_map: dict[str, str] = {}
    for raw, source, target in markdown_pairs:
        if not source.endswith("-"):
            continue
        spaced_raw = f"{source} {target}"
        collapsed_raw = f"{source}{target}"
        if collapsed_raw != spaced_raw:
            collapsed_map[collapsed_raw] = spaced_raw

    if not collapsed_map:
        return xml, 0

    normalized = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal normalized
        raw_text = match.group("text")
        replacement = collapsed_map.get(raw_text)
        if replacement is None:
            return match.group(0)
        normalized += 1
        indent = match.group("indent")
        return f"{indent}<blockquote>{replacement}</blockquote>"

    return BLOCKQUOTE_LINE_RE.sub(repl, xml), normalized


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: apply_manual_markdown_examples.py <input.xml> <output.xml>', file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    xml = input_path.read_text(encoding='utf-8')
    sources = [
        ('manual', MANUAL_MARKDOWN_HTML),
        ('ai', AI_MARKDOWN_XML),
    ]

    current_xml = xml
    total_applied = 0
    for label, path in sources:
        pairs, unmarked = load_markdown_pairs(path)
        current_xml, normalized = normalize_collapsed_hyphen_examples(current_xml, pairs)
        if normalized:
            print(f'Normalized {normalized} collapsed hyphen {label} blockquote(s)')
        current_xml, applied, missing = apply_markdown_examples(current_xml, pairs)
        total_applied += applied
        print(f'Applied {applied} {label} markdown example fix(es)')
        if unmarked:
            print(f'WARNING: {len(unmarked)} {label} blockquote(s) without ## separator:')
            for item in unmarked:
                print(f'  - {item}')
        if missing:
            print(f'WARNING: {len(missing)} {label} blockquote(s) with ## not found in XML:')
            for item in missing:
                print(f'  - {item}')

    output_path.write_text(current_xml, encoding='utf-8')
    print(f'Applied {total_applied} markdown example fix(es) in total')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
