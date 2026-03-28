#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CardRecord:
    key: str
    occurrence: int
    index: int
    xml: str

    @property
    def card_id(self) -> str:
        return f'{self.key}#{self.occurrence}'


def canonical_card_xml(card: ET.Element) -> str:
    card_copy = copy.deepcopy(card)
    temp_root = ET.Element('root')
    temp_root.append(card_copy)
    if hasattr(ET, 'indent'):
        ET.indent(temp_root, space='\t', level=0)
    xml = ET.tostring(card_copy, encoding='unicode')
    return xml.strip()


def load_cards(path: Path) -> list[CardRecord]:
    tree = ET.parse(path)
    root = tree.getroot()
    counts: Counter[str] = Counter()
    cards: list[CardRecord] = []

    for index, card in enumerate(root.findall('card')):
        key = card.findtext('k', default='').strip()
        counts[key] += 1
        cards.append(
            CardRecord(
                key=key,
                occurrence=counts[key],
                index=index,
                xml=canonical_card_xml(card),
            )
        )

    return cards


def card_map(cards: list[CardRecord]) -> dict[str, CardRecord]:
    return {card.card_id: card for card in cards}


def print_card_diff(current: CardRecord, candidate: CardRecord, diff_lines: int) -> None:
    print(f'Card changed: {current.card_id}')
    print(f'  current index:   {current.index}')
    print(f'  candidate index: {candidate.index}')
    diff = list(
        difflib.unified_diff(
            current.xml.splitlines(),
            candidate.xml.splitlines(),
            fromfile=f'current:{current.card_id}',
            tofile=f'candidate:{candidate.card_id}',
            lineterm='',
        )
    )
    for line in diff[:diff_lines]:
        print(line)
    if len(diff) > diff_lines:
        print(f'... truncated {len(diff) - diff_lines} more diff lines ...')
    print()


def build_diff_lines(current: CardRecord, candidate: CardRecord, diff_lines: int) -> list[str]:
    diff = list(
        difflib.unified_diff(
            current.xml.splitlines(),
            candidate.xml.splitlines(),
            fromfile=f'current:{current.card_id}',
            tofile=f'candidate:{candidate.card_id}',
            lineterm='',
        )
    )
    if len(diff) <= diff_lines:
        return diff
    return diff[:diff_lines] + [f'... truncated {len(diff) - diff_lines} more diff lines ...']


def print_full_cards(current: CardRecord, candidate: CardRecord) -> None:
    print('Current:')
    print(current.xml)
    print()
    print('Candidate:')
    print(candidate.xml)
    print()


def print_positional_replacement(current: CardRecord, candidate: CardRecord, diff_lines: int) -> None:
    print(f'Position {current.index}: {current.card_id} -> {candidate.card_id}')
    diff = list(
        difflib.unified_diff(
            current.xml.splitlines(),
            candidate.xml.splitlines(),
            fromfile=f'current:{current.card_id}',
            tofile=f'candidate:{candidate.card_id}',
            lineterm='',
        )
    )
    for line in diff[:diff_lines]:
        print(line)
    if len(diff) > diff_lines:
        print(f'... truncated {len(diff) - diff_lines} more diff lines ...')
    print()


def matches_record(record: CardRecord, pattern: re.Pattern[str] | None) -> bool:
    if pattern is None:
        return True
    haystacks = [record.card_id, record.key, record.xml]
    return any(pattern.search(text) for text in haystacks)


def matches_pair(current: CardRecord, candidate: CardRecord, pattern: re.Pattern[str] | None) -> bool:
    return matches_record(current, pattern) or matches_record(candidate, pattern)


def main() -> int:
    parser = argparse.ArgumentParser(description='Compare current and candidate XML by card')
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
    parser.add_argument('--limit', type=int, default=10, help='Max changed cards to print')
    parser.add_argument('--diff-lines', type=int, default=60, help='Max diff lines per changed card')
    parser.add_argument('--ids-only', action='store_true', help='Only print card IDs/positions, not XML diffs')
    parser.add_argument('--grep', help='Only show cards whose ID/key/XML matches this regex')
    parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON')
    parser.add_argument(
        '--view',
        choices=['diff', 'full'],
        default='diff',
        help='How to display card content when not using --ids-only',
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    candidate_path = Path(args.candidate)

    if not current_path.exists():
        print(f'Missing current file: {current_path}', file=sys.stderr)
        return 2
    if not candidate_path.exists():
        print(f'Missing candidate file: {candidate_path}', file=sys.stderr)
        return 2

    current_cards = load_cards(current_path)
    candidate_cards = load_cards(candidate_path)
    grep_pattern = re.compile(args.grep) if args.grep else None

    current_map = card_map(current_cards)
    candidate_map = card_map(candidate_cards)

    current_ids = set(current_map)
    candidate_ids = set(candidate_map)

    removed_ids = sorted(current_ids - candidate_ids)
    added_ids = sorted(candidate_ids - current_ids)
    shared_ids = sorted(current_ids & candidate_ids, key=lambda cid: current_map[cid].index)
    changed_ids = [cid for cid in shared_ids if current_map[cid].xml != candidate_map[cid].xml]
    positional_replacements: list[tuple[CardRecord, CardRecord]] = []

    for current_card, candidate_card in zip(current_cards, candidate_cards):
        if current_card.card_id == candidate_card.card_id:
            continue
        positional_replacements.append((current_card, candidate_card))

    if grep_pattern is not None:
        added_ids = [cid for cid in added_ids if matches_record(candidate_map[cid], grep_pattern)]
        removed_ids = [cid for cid in removed_ids if matches_record(current_map[cid], grep_pattern)]
        changed_ids = [
            cid for cid in changed_ids
            if matches_pair(current_map[cid], candidate_map[cid], grep_pattern)
        ]
        positional_replacements = [
            pair for pair in positional_replacements if matches_pair(pair[0], pair[1], grep_pattern)
        ]

    if args.json:
        payload = {
            'current_cards': len(current_cards),
            'candidate_cards': len(candidate_cards),
            'added_ids': added_ids[:args.limit],
            'removed_ids': removed_ids[:args.limit],
            'changed_cards': [],
            'positional_replacements': [],
        }

        for cid in changed_ids[:args.limit]:
            current = current_map[cid]
            candidate = candidate_map[cid]
            item = {
                'card_id': cid,
                'current_index': current.index,
                'candidate_index': candidate.index,
            }
            if args.view == 'full':
                item['current_xml'] = current.xml
                item['candidate_xml'] = candidate.xml
            elif not args.ids_only:
                item['diff'] = build_diff_lines(current, candidate, args.diff_lines)
            payload['changed_cards'].append(item)

        for current, candidate in positional_replacements[:args.limit]:
            item = {
                'position': current.index,
                'current_card_id': current.card_id,
                'candidate_card_id': candidate.card_id,
            }
            if args.view == 'full':
                item['current_xml'] = current.xml
                item['candidate_xml'] = candidate.xml
            elif not args.ids_only:
                item['diff'] = build_diff_lines(current, candidate, args.diff_lines)
            payload['positional_replacements'].append(item)

        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not added_ids and not removed_ids and not changed_ids and not positional_replacements else 1

    print(f'Current cards:   {len(current_cards)}')
    print(f'Candidate cards: {len(candidate_cards)}')
    print(f'Added cards:     {len(added_ids)}')
    print(f'Removed cards:   {len(removed_ids)}')
    print(f'Changed cards:   {len(changed_ids)}')
    print(f'Position shifts: {len(positional_replacements)}')
    print()

    if added_ids:
        print('Added card IDs:')
        for cid in added_ids[:args.limit]:
            print(f'  {cid}')
        if len(added_ids) > args.limit:
            print(f'  ... and {len(added_ids) - args.limit} more')
        print()

    if removed_ids:
        print('Removed card IDs:')
        for cid in removed_ids[:args.limit]:
            print(f'  {cid}')
        if len(removed_ids) > args.limit:
            print(f'  ... and {len(removed_ids) - args.limit} more')
        print()

    if positional_replacements:
        print('Positional replacements:')
        print()
        for current_card, candidate_card in positional_replacements[:args.limit]:
            if args.ids_only:
                print(f'Position {current_card.index}: {current_card.card_id} -> {candidate_card.card_id}')
            elif args.view == 'full':
                print(f'Position {current_card.index}: {current_card.card_id} -> {candidate_card.card_id}')
                print_full_cards(current_card, candidate_card)
            else:
                print_positional_replacement(current_card, candidate_card, args.diff_lines)
        if len(positional_replacements) > args.limit:
            print(f'... omitted {len(positional_replacements) - args.limit} more positional replacements ...')
        print()

    if not changed_ids:
        return 0 if not added_ids and not removed_ids and not positional_replacements else 1

    print('Changed cards:')
    print()
    for cid in changed_ids[:args.limit]:
        if args.ids_only:
            print(f'{cid} (current index {current_map[cid].index}, candidate index {candidate_map[cid].index})')
        elif args.view == 'full':
            print(f'Card changed: {cid}')
            print(f'  current index:   {current_map[cid].index}')
            print(f'  candidate index: {candidate_map[cid].index}')
            print_full_cards(current_map[cid], candidate_map[cid])
        else:
            print_card_diff(current_map[cid], candidate_map[cid], args.diff_lines)

    if len(changed_ids) > args.limit:
        print(f'... omitted {len(changed_ids) - args.limit} more changed cards ...')

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
