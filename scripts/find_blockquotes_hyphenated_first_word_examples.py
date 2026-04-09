#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

WORD_CHARS = 'A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'
BLOCKQUOTE_XML_RE = re.compile(r'<blockquote>(?P<xml>.*?)</blockquote>', re.S)
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<xml>.*?)</blockquote>$', re.M)
TAG_RE = re.compile(r'<[^>]+>')
IMMEDIATE_XR_RE = re.compile(
    rf'^[{WORD_CHARS}]+\-[{WORD_CHARS}]+-?(?:\s+[{WORD_CHARS}\'-]+-?)?\s+(?:см\.\s*<wordLink\b|то же, что\s*<wordLink\b)'
)
SOURCE_TARGET_RE = re.compile(
    rf'^(?P<source>[{WORD_CHARS}]+\-[{WORD_CHARS}]+-?(?:\s+[{WORD_CHARS}\'-]+-?)?)\s+(?P<target>(?:см\.\s*<wordLink\b|то же, что\s*<wordLink\b).*)$',
    re.S,
)


def has_hyphenated_first_word(text: str) -> bool:
    words = re.findall(rf'[{WORD_CHARS}\'-]+', text)
    if not words:
        return False
    first = words[0].rstrip('-')
    return '-' in first and not first.startswith('-')


def matches_rule(blockquote_xml: str) -> bool:
    visible_text = TAG_RE.sub('', blockquote_xml).strip()
    if visible_text.startswith('('):
        return False
    return has_hyphenated_first_word(visible_text) and IMMEDIATE_XR_RE.match(blockquote_xml.strip()) is not None


def split_example(blockquote_xml: str) -> tuple[str, str] | None:
    match = SOURCE_TARGET_RE.match(blockquote_xml.strip())
    if not match:
        return None
    return match.group('source').strip(), match.group('target').strip()


def collect_matches(xml: str) -> list[str]:
    matches: list[str] = []
    for match in BLOCKQUOTE_XML_RE.finditer(xml):
        blockquote_xml = match.group('xml')
        if matches_rule(blockquote_xml):
            matches.append(f'<blockquote>{blockquote_xml}</blockquote>')
    return matches


def render_matches(matches: list[str]) -> str:
    return '\n\n'.join(matches) + ('\n' if matches else '')


def apply_splits(xml: str) -> tuple[str, int]:
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        blockquote_xml = match.group('xml')
        if not matches_rule(blockquote_xml):
            return match.group(0)
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
        description='Dump or apply blockquotes where the first visible word is internally hyphenated and is immediately followed by a wordLink cross-reference.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_hyphenated_first_word_examples.txt',
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
        print('Rule: first visible word is internally hyphenated, optional second source word, then immediate "см. <wordLink>" or "то же, что <wordLink>"')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: first visible word is internally hyphenated, optional second source word, then immediate "см. <wordLink>" or "то же, что <wordLink>"')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
