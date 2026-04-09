#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
SCRIPTS_DIR = ROOT_DIR / 'pipeline_part1' / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

constants_path = SCRIPTS_DIR / 'constants.py'
spec = importlib.util.spec_from_file_location('constants', constants_path)
constants = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(constants)

META_WORDS = set(getattr(constants, '_meta_words', []))
LINK_KEYWORDS = set(getattr(constants, '_link_keywords', []))

WORD_CHARS = 'A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'
BLOCKQUOTE_XML_RE = re.compile(r'<blockquote>(?P<xml>.*?)</blockquote>', re.S)
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<xml>.*?)</blockquote>$', re.M)
TAG_RE = re.compile(r'<[^>]+>')
WORD_RE = re.compile(rf'[{WORD_CHARS}]+(?:-[{WORD_CHARS}]+)*-?')
FORBIDDEN_PATTERNS = [
    re.compile(rf'(?<![{WORD_CHARS}]){re.escape(label)}(?![{WORD_CHARS}])')
    for label in sorted(META_WORDS | LINK_KEYWORDS, key=len, reverse=True)
]


def split_example(blockquote_xml: str) -> tuple[str, str] | None:
    visible = TAG_RE.sub('', blockquote_xml).strip()
    if not visible:
        return None
    all_words = WORD_RE.findall(visible)
    if len(all_words) < 3:
        return None
    if visible[0] in '("«„':
        return None
    if 'или' in visible:
        return None

    first = all_words[0]
    if any(ch in first.lower() for ch in 'фць'):
        return None

    source_words = all_words[:2]
    if not source_words[-1].endswith('-'):
        return None

    first_end = visible.find(source_words[0]) + len(source_words[0])
    second_start = visible.find(source_words[1], first_end)
    if second_start == -1:
        return None
    second_end = second_start + len(source_words[1])
    between = visible[first_end:second_start]
    after_second = visible[second_end:]
    if ',' in between:
        return None
    if after_second.startswith(','):
        return None

    remainder = after_second.lstrip()
    if not remainder:
        return None
    if any(p.search(remainder) for p in FORBIDDEN_PATTERNS):
        return None

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
        description='Dump or apply blockquotes with up to a two-word source whose last source word ends with a hyphen.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_two_word_source_last_hyphen_strict.txt',
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
        print('Rule: 2-word source max; attached trailing hyphen on last source word; no или anywhere; no meta/link-keywords after source; no comma between/after first two source words')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule: 2-word source max; attached trailing hyphen on last source word; no или anywhere; no meta/link-keywords after source; no comma between/after first two source words')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
