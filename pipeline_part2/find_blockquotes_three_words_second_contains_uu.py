#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

WORD_CHARS = 'A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'
BLOCKQUOTE_XML_RE = re.compile(r'<blockquote>(?P<xml>.*?)</blockquote>', re.S)
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<xml>.*?)</blockquote>$', re.M)
TAG_RE = re.compile(r'<[^>]+>')
WORD_RE = re.compile(rf'[{WORD_CHARS}]+(?:-[{WORD_CHARS}]+)*-?')


def split_example(blockquote_xml: str) -> tuple[str, str] | None:
    visible = TAG_RE.sub('', blockquote_xml).strip()
    words = WORD_RE.findall(visible)
    if len(words) != 3:
        return None
    if any(ch in words[0].lower() for ch in 'фцьё'):
        return None
    if 'уу' not in words[1]:
        return None

    first_end = visible.find(words[0]) + len(words[0])
    second_start = visible.find(words[1], first_end)
    if second_start == -1:
        return None
    second_end = second_start + len(words[1])

    source = blockquote_xml[:second_end].strip()
    target = blockquote_xml[second_end:].lstrip()
    if not source or not target:
        return None
    return source, target


def collect_matches(xml: str) -> list[str]:
    matches: list[str] = []
    for match in BLOCKQUOTE_XML_RE.finditer(xml):
        blockquote_xml = match.group('xml')
        if split_example(blockquote_xml) is not None:
            matches.append(f'<blockquote>{blockquote_xml}</blockquote>')
    return matches


def render_matches(matches: list[str]) -> str:
    return '\n'.join(matches) + ('\n' if matches else '')


def apply_splits(xml: str) -> tuple[str, int]:
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        blockquote_xml = match.group('xml')
        split = split_example(blockquote_xml)
        if split is None:
            return match.group(0)
        source, target = split
        indent = match.group('indent')
        applied += 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{source}</source>\n'
            f'{indent}\t<target>{target}</target>\n'
            f'{indent}</ex>'
        )

    return BLOCKQUOTE_RE.sub(repl, xml), applied


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Dump or apply blockquotes with exactly three words where the second word contains "уу".'
    )
    parser.add_argument('--input', default='./pipeline_output/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./pipeline_output/blockquotes_three_words_second_contains_uu.txt',
        help='Output text file',
    )
    parser.add_argument('--apply-output', help='If set, rewrite matching blockquotes to <ex> in this XML output file')
    args = parser.parse_args()

    input_path = Path(args.input)
    xml = input_path.read_text(encoding='utf-8')

    if args.apply_output:
        out_path = Path(args.apply_output)
        new_xml, applied = apply_splits(xml)
        out_path.write_text(new_xml, encoding='utf-8')
        print(f'Input: {input_path}')
        print('Rule: blockquote has exactly 3 words total; second word contains "уу"; first word contains no ф, ц, ь, ё')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: blockquote has exactly 3 words total; second word contains "уу"; first word contains no ф, ц, ь, ё')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
