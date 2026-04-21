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
    if '<wordLink ' in blockquote_xml:
        return None

    visible = TAG_RE.sub('', blockquote_xml).strip()
    if not visible or visible.startswith('('):
        return None

    words = WORD_RE.findall(visible)
    if len(words) != 2:
        return None

    first = words[0].rstrip('-')
    if '-' not in first:
        return None

    source = blockquote_xml[: len(words[0])].strip()
    target = blockquote_xml[len(words[0]) :].lstrip()
    if not target:
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
        description='Dump or apply blockquotes that start with an internally hyphenated word and contain exactly two words total.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_starting_with_middle_hyphen_word_two_words_total.txt',
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
        print('Rule: starts with an internal-hyphen word; exactly 2 words total; no wordLink; does not start with (')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: starts with an internal-hyphen word; exactly 2 words total; no wordLink; does not start with (')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
