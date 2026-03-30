#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from rule_loader import load_rule_lines


REPORT_ORDER = [
    'suffix_after_wordlink',
    'split_compound_after_wordlink',
    'ref_tail_after_comma',
    'mixed_altform_ref_colon',
    'comparison_wordlink',
]

COMPARISON_WORDS = load_rule_lines('link_nonrefs_after_sr.txt')


def collapse_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def inline_xml(elem: ET.Element) -> str:
    return collapse_ws(ET.tostring(elem, encoding='unicode'))


def scope_for_element(card: ET.Element, parent: ET.Element) -> dict[str, str]:
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


def build_patterns() -> list[tuple[str, re.Pattern[str], str]]:
    patterns: list[tuple[str, re.Pattern[str], str]] = [
        (
            'suffix_after_wordlink',
            re.compile(r'<wordLink[^>]*/>\s*(?:[IVX]+(?:\s+\d+)?|\d+)(?=[,.;:)])'),
            'wordLink still has a trailing homonym/meaning suffix outside the tag',
        ),
        (
            'split_compound_after_wordlink',
            re.compile(r'<wordLink[^>]*/>(?=[0-9A-Za-zА-Яа-яЁёӨөҮүҢңӘә])'),
            'wordLink is immediately followed by text, likely a split compound reference',
        ),
        (
            'ref_tail_after_comma',
            re.compile(
                r'\((?:см\.|ср\.|прим\.\s*см\.|ещё\s+прим\.\s*см\.)[^)]*<wordLink[^>]*/>[^)]*,\s*[^<(),]+(?:\s+(?:[IVX]+|\d+))?(?=[,.)])'
            ),
            'reference note still has a bare tail after a linked item',
        ),
        (
            'mixed_altform_ref_colon',
            re.compile(r'^\([^)]*;\s*(?:см\.|ср\.)[^)]*\):$'),
            'one line mixes alternative-form text, reference note, and collocation colon',
        ),
    ]

    if COMPARISON_WORDS:
        patterns.append(
            (
                'comparison_wordlink',
                re.compile(
                    r'ср\.\s*<wordLink[^>]*word="(?:' + '|'.join(re.escape(word) for word in COMPARISON_WORDS) + r')"[^>]*/>',
                    re.IGNORECASE,
                ),
                'comparison marker is still linked as if it were a dictionary headword',
            )
        )

    return patterns


def is_fully_linked_mixed_reference(xml: str) -> bool:
    return bool(
        re.search(
            r'\((?:см\.|ср\.)[^)]*<wordLink[^>]*/>\s*,\s*(?:см\.|ср\.)\s*<wordLink[^>]*/>[^)]*\)',
            xml,
        )
    )


def collect_suspicious(tree: ET.ElementTree) -> list[dict[str, str]]:
    root = tree.getroot()
    patterns = build_patterns()
    findings: list[dict[str, str]] = []

    for card in root.findall('card'):
        parent_map = {child: parent for parent in card.iter() for child in parent}
        for elem in card.iter():
            if elem.tag not in {'blockquote', 'xr', 'trn', 'target'}:
                continue

            xml = inline_xml(elem)
            text = collapse_ws(''.join(elem.itertext()))
            for category, pattern, reason in patterns:
                haystack = text if category == 'mixed_altform_ref_colon' else xml
                if not pattern.search(haystack):
                    continue
                if category == 'ref_tail_after_comma' and is_fully_linked_mixed_reference(xml):
                    continue

                parent = parent_map.get(elem, card)
                scope = scope_for_element(card, parent)
                findings.append({
                    'category': category,
                    'reason': reason,
                    'k': scope['k'],
                    'homonymIndex': scope['homonymIndex'],
                    'meaningIndex': scope['meaningIndex'],
                    'scope': scope['scope'],
                    'tag': elem.tag,
                    'text': text,
                    'xml': xml,
                })
                break

    return findings


def write_report(path: Path, findings: list[dict[str, str]]) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for finding in findings:
        grouped[finding['category']].append(finding)

    counts = Counter(finding['category'] for finding in findings)
    lines = [
        f'Suspicious link candidates: {len(findings)}',
        '',
        'These are review hints, not automatic fixes.',
        '',
        'Counts:',
    ]
    for category in REPORT_ORDER:
        lines.append(f'  {category}: {counts.get(category, 0)}')

    for category in REPORT_ORDER:
        bucket = grouped.get(category, [])
        if not bucket:
            continue
        lines.extend(['', '=' * 80, category, '=' * 80, ''])
        for finding in bucket:
            scope_bits = [finding['k']]
            if finding['homonymIndex']:
                scope_bits.append(finding['homonymIndex'])
            if finding['meaningIndex']:
                scope_bits.append(finding['meaningIndex'])
            lines.append(f'scope: {" | ".join(scope_bits)}')
            lines.append(f'tag: {finding["tag"]}')
            lines.append(f'reason: {finding["reason"]}')
            lines.append(f'text: {finding["text"]}')
            lines.append(f'xml: {finding["xml"]}')
            lines.append('')

    path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')


def write_tsv(path: Path, findings: list[dict[str, str]]) -> None:
    fieldnames = ['category', 'reason', 'k', 'homonymIndex', 'meaningIndex', 'scope', 'tag', 'text', 'xml']
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(findings)


def main() -> int:
    if len(sys.argv) < 4:
        print('Usage: python3 report_suspicious_links.py <input.xml> <report.txt> <report.tsv>')
        return 1

    input_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2])
    tsv_path = Path(sys.argv[3])

    tree = ET.parse(input_path)
    findings = collect_suspicious(tree)
    write_report(report_path, findings)
    write_tsv(tsv_path, findings)
    print(f'Suspicious link candidates: {len(findings)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
