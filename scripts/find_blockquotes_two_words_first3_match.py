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
    if len(words) != 2:
        return None

    left = words[0].lower().rstrip('-')
    right = words[1].lower().rstrip('-;,.')
    if len(left) < 3 or len(right) < 3:
        return None
    if left[:3] != right[:3]:
        return None

    first_end = visible.find(words[0]) + len(words[0])
    source = blockquote_xml[:first_end].strip()
    target = blockquote_xml[first_end:].lstrip()
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
        description='Dump or apply two-word blockquotes whose first three letters match.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_two_words_first3_match.txt',
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
        print('Rule: blockquote has exactly 2 words total and the first 3 letters of both words match')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: blockquote has exactly 2 words total and the first 3 letters of both words match')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
