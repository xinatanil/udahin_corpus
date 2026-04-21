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
TARGET_RE = re.compile(r'^(.+?)\s+см\.\s*(<wordLink\b.*)$', re.S)


def visible_text(xml: str) -> str:
    return re.sub(r'\s+', ' ', TAG_RE.sub(' ', xml)).strip()


def match_rule(blockquote_xml: str) -> bool:
    visible = visible_text(blockquote_xml)
    if not visible or visible.startswith('('):
        return False
    if '<wordLink ' not in blockquote_xml:
        return False
    match = TARGET_RE.match(blockquote_xml.strip())
    if match is None:
        return False
    source_visible = visible_text(match.group(1))
    source_words = WORD_RE.findall(source_visible)
    if len(source_words) != 3:
        return False
    if '(см.' in blockquote_xml.lower():
        return False
    return True


def split_match(blockquote_xml: str) -> tuple[str, str] | None:
    match = TARGET_RE.match(blockquote_xml.strip())
    if match is None:
        return None
    source = match.group(1).strip()
    target = f'см. {match.group(2).strip()}'
    return source, target


def collect_matches(xml: str) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for match in BLOCKQUOTE_XML_RE.finditer(xml):
        blockquote_xml = match.group('xml')
        if match_rule(blockquote_xml):
            split = split_match(blockquote_xml)
            if split is not None:
                matches.append(split)
    return matches


def render_matches(matches: list[tuple[str, str]]) -> str:
    chunks = [f'{source}\n{target}' for source, target in matches]
    return '\n\n'.join(chunks) + ('\n' if chunks else '')


def apply_splits(xml: str) -> tuple[str, int]:
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        blockquote_xml = match.group('xml')
        if not match_rule(blockquote_xml):
            return match.group(0)
        split = split_match(blockquote_xml)
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
        description='Dump blockquotes whose source is exactly three visible words followed by plain см. <wordLink ...>.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_three_word_sm_wordlink.txt',
        help='Output text file',
    )
    parser.add_argument('--apply-output', help='If set, rewrite matching blockquotes to <ex> in this XML output file')
    args = parser.parse_args()

    input_path = Path(args.input)
    xml = input_path.read_text(encoding='utf-8')

    if args.apply_output:
        output_path = Path(args.apply_output)
        new_xml, applied = apply_splits(xml)
        output_path.write_text(new_xml, encoding='utf-8')
        print(f'Input: {input_path}')
        print('Rule: exactly 3 visible source words, then plain см. <wordLink ...>')
        print(f'Applied: {applied}')
        print(f'Output: {output_path}')
        return 0

    output_path = Path(args.output)
    matches = collect_matches(xml)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: exactly 3 visible source words, then plain см. <wordLink ...>')
    print('Format: source line, then target line')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
