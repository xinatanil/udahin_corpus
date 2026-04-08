#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_SCRIPTS = ROOT / 'pipeline_part1' / 'scripts'
sys.path.insert(0, str(PIPELINE_SCRIPTS))
import constants  # type: ignore

BLOCKQUOTE_RE = re.compile(r'^(?P<indent>[ \t]*)<blockquote>(?P<content>.*?)</blockquote>$', re.M)
WS_RE = re.compile(r'\s+')
TAG_RE = re.compile(r'<[^>]+>')

META_LABELS = list(getattr(constants, '_meta_words', []))
ORIGIN_LABELS = [w for w in getattr(constants, '_origin_words', []) if not w.startswith('(')]


def normalize_ws(text: str) -> str:
    return WS_RE.sub(' ', text).strip()


def strip_tags(text: str) -> str:
    return TAG_RE.sub('', text)


def plain_to_content_index(content: str, plain_index: int) -> int:
    plain_pos = 0
    i = 0
    while i < len(content):
        if content[i] == '<':
            j = content.find('>', i)
            if j == -1:
                return i
            i = j + 1
            continue
        if plain_pos >= plain_index:
            return i
        plain_pos += 1
        i += 1
    return len(content)


def last_word_key(text: str) -> str:
    plain = normalize_ws(strip_tags(text))
    words = re.findall(r'[\w-]+', plain, flags=re.UNICODE)
    return words[-1].casefold() if words else ''


def build_excluded_labels(divider: str, ignore_case: bool) -> set[str]:
    labels = set(META_LABELS + ORIGIN_LABELS)
    labels.discard(divider)
    if ignore_case:
        return {label.casefold() for label in labels}
    return labels


def find_split(raw_content: str, divider: str, ignore_case: bool) -> tuple[str, str] | None:
    plain = strip_tags(raw_content)
    haystack = plain.casefold() if ignore_case else plain
    needle = divider.casefold() if ignore_case else divider
    pattern = re.compile(rf'(?<!\S){re.escape(needle)}(?![,;])')
    m = pattern.search(haystack)
    if not m:
        return None

    excluded_labels = build_excluded_labels(divider, ignore_case)
    if any(label in haystack for label in excluded_labels):
        return None

    split_at = plain_to_content_index(raw_content, m.start())
    left = raw_content[:split_at].rstrip()
    right = raw_content[split_at:].lstrip()
    if not left or not right:
        return None
    plain_right = normalize_ws(strip_tags(right))
    divider_key = divider.casefold() if ignore_case else divider
    plain_right_key = plain_right.casefold() if ignore_case else plain_right
    if plain_right_key == divider_key:
        return None
    return left, right


def collect_matches(xml: str, divider: str, ignore_case: bool) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for match in BLOCKQUOTE_RE.finditer(xml):
        split = find_split(match.group('content'), divider, ignore_case)
        if split is not None:
            matches.append(split)
    return matches


def render_matches(matches: list[tuple[str, str]]) -> str:
    ordered = sorted(matches, key=lambda pair: (last_word_key(pair[0]), normalize_ws(strip_tags(pair[0])).casefold()))
    rendered = [f'{left}\n{right}' for left, right in ordered]
    return '\n\n'.join(rendered) + ('\n' if rendered else '')


def apply_splits(xml: str, divider: str, ignore_case: bool) -> tuple[str, int]:
    applied = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal applied
        split = find_split(match.group('content'), divider, ignore_case)
        if split is None:
            return match.group(0)
        left, right = split
        indent = match.group('indent')
        applied += 1
        return (
            f'{indent}<ex>\n'
            f'{indent}\t<source>{left}</source>\n'
            f'{indent}\t<target>{right}</target>\n'
            f'{indent}</ex>'
        )

    return BLOCKQUOTE_RE.sub(repl, xml), applied


def main() -> int:
    parser = argparse.ArgumentParser(description='Find or apply blockquote splits using a divider word.')
    parser.add_argument('word', help='Divider word or substring to search for')
    parser.add_argument('--input', default='./chatGPT_exp/converted_dict.xml', help='Input XML file to scan')
    parser.add_argument('--output', default='./chatGPT_exp/blockquotes_with_matches.txt', help='Output text file for dump mode')
    parser.add_argument('--apply-output', help='If set, rewrite matching blockquotes to <ex> in this XML output file')
    parser.add_argument('--ignore-case', action='store_true', help='Case-insensitive search')
    args = parser.parse_args()

    input_path = Path(args.input)
    xml = input_path.read_text(encoding='utf-8')

    if args.apply_output:
        out_path = Path(args.apply_output)
        new_xml, applied = apply_splits(xml, args.word, args.ignore_case)
        out_path.write_text(new_xml, encoding='utf-8')
        print(f'Input: {input_path}')
        print(f'Word: {args.word}')
        print(f'Applied: {applied}')
        print(f'Output: {out_path}')
        return 0

    matches = collect_matches(xml, args.word, args.ignore_case)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_matches(matches), encoding='utf-8')
    print(f'Input: {input_path}')
    print(f'Word: {args.word}')
    print(f'Matches: {len(matches)}')
    print(f'Output: {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
