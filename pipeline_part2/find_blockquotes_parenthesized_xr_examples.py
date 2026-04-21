#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

WORD_CHARS = 'A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'
BLOCKQUOTE_XML_RE = re.compile(r'<blockquote>(?P<xml>.*?)</blockquote>', re.S)
BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<xml>.*?)</blockquote>$', re.M)
TAG_RE = re.compile(r'<[^>]+>')
TOKEN_RE = re.compile(rf'[{WORD_CHARS}\'-]+')


def second_word_ends_with_dash(text: str) -> bool:
    words = re.findall(rf'[{WORD_CHARS}\'-]+', text)
    return len(words) >= 2 and words[1].endswith('-')


def second_word_has_no_dash(text: str) -> bool:
    words = re.findall(rf'[{WORD_CHARS}\'-]+', text)
    return len(words) >= 2 and not words[1].endswith('-')


def has_hyphenated_first_word(text: str) -> bool:
    words = re.findall(rf'[{WORD_CHARS}\'-]+', text)
    if not words:
        return False
    first = words[0].rstrip('-')
    return '-' in first and not first.startswith('-')


RULES = [
    {
        'name': 'second_word_dash',
        'description': 'second visible word ends with a dash',
        'source_target_re': re.compile(
            rf'^(?P<source>[{WORD_CHARS}\'-]+\s+[{WORD_CHARS}\'-]+-)\s+'
            rf'(?P<target>\((?:см\.|ср\.)\s*<wordLink\b.*)$',
            re.S,
        ),
        'visible_predicate': second_word_ends_with_dash,
    },
    {
        'name': 'second_word_plain',
        'description': 'second visible word has no dash',
        'source_target_re': re.compile(
            rf'^(?P<source>[{WORD_CHARS}\'-]+\s+[{WORD_CHARS}\'-]+)\s+'
            rf'(?P<target>\((?:см\.|ср\.)\s*<wordLink\b.*)$',
            re.S,
        ),
        'visible_predicate': second_word_has_no_dash,
    },
    {
        'name': 'hyphenated_first_word',
        'description': 'first visible word is internally hyphenated, optional second source word',
        'source_target_re': re.compile(
            rf'^(?P<source>[{WORD_CHARS}]+\-[{WORD_CHARS}]+-?(?:\s+[{WORD_CHARS}\'-]+-?)?)\s+'
            rf'(?P<target>\((?:см\.|ср\.)\s*<wordLink\b.*)$',
            re.S,
        ),
        'visible_predicate': has_hyphenated_first_word,
    },
]


def match_rule(blockquote_xml: str) -> tuple[dict, tuple[str, str]] | None:
    visible_text = TAG_RE.sub('', blockquote_xml).strip()
    if visible_text.startswith('('):
        return None

    stripped = blockquote_xml.strip()
    for rule in RULES:
        if not rule['visible_predicate'](visible_text):
            continue
        match = rule['source_target_re'].match(stripped)
        if match is None:
            continue
        source = match.group('source').strip()
        tokens = TOKEN_RE.findall(source)
        if len(tokens) > 2:
            continue
        internally_hyphenated = [tok.rstrip('-') for tok in tokens if '-' in tok.rstrip('-')]
        if internally_hyphenated and len(tokens) != 1:
            continue
        return rule, (source, match.group('target').strip())
    return None


def collect_matches(xml: str) -> tuple[list[str], dict[str, int]]:
    matches: list[str] = []
    counts = {rule['name']: 0 for rule in RULES}
    for match in BLOCKQUOTE_XML_RE.finditer(xml):
        blockquote_xml = match.group('xml')
        result = match_rule(blockquote_xml)
        if result is None:
            continue
        rule, _ = result
        counts[rule['name']] += 1
        matches.append(f'<blockquote>{blockquote_xml}</blockquote>')
    return matches, counts


def render_matches(matches: list[str]) -> str:
    return '\n\n'.join(matches) + ('\n' if matches else '')


def apply_splits(xml: str) -> tuple[str, int, dict[str, int]]:
    applied = 0
    counts = {rule['name']: 0 for rule in RULES}

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        blockquote_xml = match.group('xml')
        result = match_rule(blockquote_xml)
        if result is None:
            return match.group(0)
        rule, (source, target) = result
        indent = match.group('indent')
        applied += 1
        counts[rule['name']] += 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{source}</source>\n'
            f'{indent}\t<target>{target}</target>\n'
            f'{indent}</ex>'
        )

    return BLOCKQUOTE_RE.sub(repl, xml), applied, counts


def print_counts(counts: dict[str, int]) -> None:
    for rule in RULES:
        print(f"{rule['name']}: {counts[rule['name']]}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Dump parenthesized xref blockquotes that can likely be converted into <ex> entries.'
    )
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument(
        '--output',
        default='./chatGPT_exp/blockquotes_parenthesized_xr_examples.txt',
        help='Output text file',
    )
    parser.add_argument('--apply-output', help='If set, rewrite matching blockquotes to <ex> in this XML output file')
    args = parser.parse_args()

    input_path = Path(args.input)
    xml = input_path.read_text(encoding='utf-8')

    if args.apply_output:
        out_path = Path(args.apply_output)
        new_xml, applied, counts = apply_splits(xml)
        out_path.write_text(new_xml, encoding='utf-8')

        print(f'Input: {input_path}')
        print('Rule set: parenthesized xref examples')
        print_counts(counts)
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches, counts = collect_matches(xml)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')

    print(f'Input: {input_path}')
    print('Rule set: parenthesized xref examples')
    print_counts(counts)
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
