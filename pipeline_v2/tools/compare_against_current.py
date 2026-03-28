#!/usr/bin/env python3
import argparse
import difflib
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def canonicalize(path: Path) -> str:
    tree = ET.parse(path)
    root = tree.getroot()
    if hasattr(ET, 'indent'):
        ET.indent(tree, space='\t', level=0)
    return ET.tostring(root, encoding='unicode')


def tag_counts(path: Path) -> Counter:
    tree = ET.parse(path)
    root = tree.getroot()
    return Counter(elem.tag for elem in root.iter())


def print_count_deltas(current: Counter, candidate: Counter) -> None:
    keys = sorted(set(current) | set(candidate))
    deltas = []
    for key in keys:
        delta = candidate[key] - current[key]
        if delta:
            deltas.append((key, delta, current[key], candidate[key]))

    if not deltas:
        print('Tag counts: identical')
        return

    print('Tag count deltas:')
    for key, delta, cur, cand in deltas:
        sign = '+' if delta > 0 else ''
        print(f'  {key}: {cur} -> {cand} ({sign}{delta})')


def main() -> int:
    parser = argparse.ArgumentParser(description='Compare pipeline_v2 output against current converted_dict.xml')
    parser.add_argument(
        '--current',
        default='/Users/xinatanil/Sources/udahin/chatGPT_exp/converted_dict.xml',
        help='Current reference XML',
    )
    parser.add_argument(
        '--candidate',
        default='/Users/xinatanil/Sources/udahin/pipeline_v2/output/converted_dict.xml',
        help='Candidate XML from pipeline_v2',
    )
    parser.add_argument('--diff-lines', type=int, default=80, help='Max unified diff lines to print')
    args = parser.parse_args()

    current = Path(args.current)
    candidate = Path(args.candidate)

    if not current.exists():
        print(f'Missing current file: {current}', file=sys.stderr)
        return 2
    if not candidate.exists():
        print(f'Missing candidate file: {candidate}', file=sys.stderr)
        return 2

    current_bytes = current.read_bytes()
    candidate_bytes = candidate.read_bytes()
    if current_bytes == candidate_bytes:
        print('Files are byte-identical.')
        return 0

    current_xml = canonicalize(current).splitlines()
    candidate_xml = canonicalize(candidate).splitlines()

    if current_xml == candidate_xml:
        print('XML is structurally identical after normalization, but raw files differ.')
        return 0

    print('Files differ.')
    print_count_deltas(tag_counts(current), tag_counts(candidate))
    print('\nFirst diff chunk:')
    diff = list(
        difflib.unified_diff(
            current_xml,
            candidate_xml,
            fromfile=str(current),
            tofile=str(candidate),
            lineterm='',
        )
    )
    for line in diff[: args.diff_lines]:
        print(line)
    if len(diff) > args.diff_lines:
        print(f'... truncated {len(diff) - args.diff_lines} more diff lines ...')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
