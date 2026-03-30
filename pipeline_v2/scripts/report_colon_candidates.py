#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from rule_loader import load_rule_lines


SUGGESTION_ORDER = [
    'likely_semicolon_scan_error',
    'likely_altform_collocation',
    'likely_meta_collocation',
    'likely_xr_collocation',
    'likely_collocation',
    'likely_reject',
]

META_PREFIXES = (
    'только ',
    'обычно ',
    'в сочет.',
    'в сочетании',
    'в соединении',
    'в игре',
    'при игре',
    'при определении',
    'при ',
    'употребляется',
    'перен.',
    'в эпосе',
    'на севере',
)

META_SNIPPETS = (
    'в отриц.',
    'в отрицательн',
    'обычно в отриц',
    'только в отриц',
    'только в сочет',
    'обычно в сочет',
    'только с числительным',
    'только в форме',
    'только в соединении',
    'употребляется только',
    'употребляется в',
)

ALTFORM_PREFIXES = (
    '(или ',
    '(неправ.',
    '(точнее ',
    '(в произношении ',
    '(орф.',
    '(при наращении аффиксов ',
)


def collapse_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_rule_entry(text: str) -> str:
    text = text.strip()
    if text.startswith('blockquote_xml:'):
        text = text.split(':', 1)[1].strip()
    return collapse_ws(text)


def inline_xml(elem: ET.Element) -> str:
    return collapse_ws(ET.tostring(elem, encoding='unicode'))


def is_empty_context_xml(xml: str) -> bool:
    return xml in {
        '',
        '<blockquote />',
        '<blockquote/>',
        '<meta />',
        '<meta/>',
        '<origin />',
        '<origin/>',
        '<xr />',
        '<xr/>',
        '<trn />',
        '<trn/>',
    }


def parent_scope(card: ET.Element, parent: ET.Element) -> dict[str, str]:
    scope = {
        'k': collapse_ws(card.findtext('k') or ''),
        'homonymIndex': '',
        'meaningIndex': '',
        'scope': parent.tag,
    }
    if parent.tag == 'homonym':
        scope['homonymIndex'] = collapse_ws(parent.findtext('homonymIndex') or '')
    elif parent.tag == 'meaning':
        scope['meaningIndex'] = collapse_ws(parent.findtext('meaningIndex') or '')
        for homonym in card.findall('./homonym'):
            if parent in homonym.findall('./meaning'):
                scope['homonymIndex'] = collapse_ws(homonym.findtext('homonymIndex') or '')
                break
    return scope


def sibling_context(parent: ET.Element, idx: int) -> tuple[list[str], list[str]]:
    siblings = list(parent)

    def collect(start: int, step: int) -> list[str]:
        collected: list[str] = []
        i = start
        while 0 <= i < len(siblings) and len(collected) < 2:
            xml = inline_xml(siblings[i])
            if not is_empty_context_xml(xml):
                collected.append(xml)
            i += step
        if step < 0:
            collected.reverse()
        return collected

    prev_lines = collect(idx - 1, -1)
    next_lines = collect(idx + 1, 1)
    return prev_lines, next_lines


def suggest_bucket(text: str, blockquote_xml: str) -> tuple[str, str]:
    normalized = collapse_ws(text)
    lowered = normalized.lower()
    word_count = len(lowered.split())

    if word_count >= 18 or len(normalized) >= 140:
        return 'likely_reject', 'long explanatory prose'

    if any(lowered.startswith(prefix) for prefix in ALTFORM_PREFIXES):
        return 'likely_altform_collocation', 'alternative-form note'

    if lowered.startswith('('):
        if lowered.startswith('(см.') or lowered.startswith('(ср.') or '<wordlink' in blockquote_xml.lower():
            return 'likely_xr_collocation', 'parenthesized reference note'
        return 'likely_meta_collocation', 'parenthesized usage note'

    if any(lowered.startswith(prefix) for prefix in META_PREFIXES):
        return 'likely_meta_collocation', 'usage-note prefix'

    if any(snippet in lowered for snippet in META_SNIPPETS):
        return 'likely_meta_collocation', 'usage-note wording'

    if ' см. ' in lowered or ' ср. ' in lowered or '<wordlink' in blockquote_xml.lower():
        return 'likely_xr_collocation', 'inline reference wording'

    if word_count >= 3:
        return 'likely_semicolon_scan_error', 'complete gloss ending with colon'

    return 'likely_collocation', 'short collocation-like header'


def load_classified_rules(rule_dir: Path) -> set[str]:
    names = [
        'colon_semicolon_scan_error.txt',
        'colon_altform_collocation.txt',
        'colon_meta_collocation.txt',
        'colon_xr_collocation.txt',
        'colon_collocation.txt',
        'colon_reject.txt',
    ]
    classified: set[str] = set()
    for name in names:
        for line in load_rule_lines(name):
            classified.add(normalize_rule_entry(line))
    return classified


def collect_candidates(tree: ET.ElementTree, classified_rules: set[str] | None = None) -> list[dict[str, str]]:
    root = tree.getroot()
    candidates: list[dict[str, str]] = []
    classified_rules = classified_rules or set()

    for card_index, card in enumerate(root.findall('card'), 1):
        parents = [card]
        parents.extend(card.findall('./homonym'))
        parents.extend(card.findall('./meaning'))
        for homonym in card.findall('./homonym'):
            parents.extend(homonym.findall('./meaning'))

        for parent in parents:
            children = list(parent)
            for idx, child in enumerate(children):
                if child.tag != 'blockquote':
                    continue
                text = collapse_ws(''.join(child.itertext()))
                if not text.endswith(':'):
                    continue

                xml = inline_xml(child)
                if xml in classified_rules:
                    continue
                suggestion, reason = suggest_bucket(text, xml)
                prev_lines, next_lines = sibling_context(parent, idx)
                scope = parent_scope(card, parent)

                candidates.append({
                    'suggestion': suggestion,
                    'reason': reason,
                    'card_index': str(card_index),
                    'scope': scope['scope'],
                    'k': scope['k'],
                    'homonymIndex': scope['homonymIndex'],
                    'meaningIndex': scope['meaningIndex'],
                    'text': text,
                    'blockquote_xml': xml,
                    'prev2': prev_lines[0] if len(prev_lines) > 0 else '',
                    'prev': prev_lines[1] if len(prev_lines) > 1 else '',
                    'next': next_lines[0] if len(next_lines) > 0 else '',
                    'next2': next_lines[1] if len(next_lines) > 1 else '',
                })

    return candidates


def write_tsv(path: Path, candidates: list[dict[str, str]]) -> None:
    fieldnames = [
        'suggestion',
        'reason',
        'card_index',
        'scope',
        'k',
        'homonymIndex',
        'meaningIndex',
        'text',
        'blockquote_xml',
        'prev2',
        'prev',
        'next',
        'next2',
    ]
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(candidates)


def write_report(path: Path, candidates: list[dict[str, str]], rule_dir: Path) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate['suggestion']].append(candidate)

    counts = Counter(candidate['suggestion'] for candidate in candidates)
    lines = [
        f'Colon-final blockquote candidates: {len(candidates)}',
        '',
        'Suggested rule files:',
        f'  likely_semicolon_scan_error -> {rule_dir / "colon_semicolon_scan_error.txt"}',
        f'  likely_altform_collocation -> {rule_dir / "colon_altform_collocation.txt"}',
        f'  likely_meta_collocation -> {rule_dir / "colon_meta_collocation.txt"}',
        f'  likely_xr_collocation -> {rule_dir / "colon_xr_collocation.txt"}',
        f'  likely_collocation -> {rule_dir / "colon_collocation.txt"}',
        f'  likely_reject -> {rule_dir / "colon_reject.txt"}',
        '',
        'Counts:',
    ]
    for suggestion in SUGGESTION_ORDER:
        lines.append(f'  {suggestion}: {counts.get(suggestion, 0)}')

    for suggestion in SUGGESTION_ORDER:
        bucket = grouped.get(suggestion, [])
        if not bucket:
            continue
        lines.extend(['', '=' * 80, suggestion, '=' * 80, ''])
        for candidate in bucket:
            scope_bits = [candidate['k']]
            if candidate['homonymIndex']:
                scope_bits.append(candidate['homonymIndex'])
            if candidate['meaningIndex']:
                scope_bits.append(candidate['meaningIndex'])
            lines.append(f'scope: {" | ".join(scope_bits)}')
            lines.append(f'reason: {candidate["reason"]}')
            lines.append(f'text: {candidate["text"]}')
            lines.append('context:')
            if candidate['prev2']:
                lines.append(f'  -2: {candidate["prev2"]}')
            if candidate['prev']:
                lines.append(f'  -1: {candidate["prev"]}')
            lines.append(f'  >>: {candidate["blockquote_xml"]}')
            if candidate['next']:
                lines.append(f'  +1: {candidate["next"]}')
            if candidate['next2']:
                lines.append(f'  +2: {candidate["next2"]}')
            lines.append('')

    path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')


def main() -> int:
    if len(sys.argv) < 4:
        print('Usage: python3 report_colon_candidates.py <input.xml> <report.txt> <report.tsv>')
        return 1

    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    tsv_path = Path(sys.argv[3])
    rule_dir = Path(__file__).resolve().parents[1] / 'rules'

    tree = ET.parse(input_path)
    classified_rules = load_classified_rules(rule_dir)
    candidates = collect_candidates(tree, classified_rules)
    write_report(report_path, candidates, rule_dir)
    write_tsv(tsv_path, candidates)
    print(f'Colon candidates: {len(candidates)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
