from __future__ import annotations

import xml.etree.ElementTree as ET

from identify_cross_references import transform_plain_reference_xrs


def _first_nonempty_direct_blockquote(parent):
    for child in list(parent):
        if child.tag != 'blockquote':
            continue
        text = ''.join(child.itertext()).strip()
        if text:
            return child
    return None


def collect_shadow_reference_candidates(tree):
    root = tree.getroot()
    candidates = []

    for card_index, card in enumerate(root.findall('card'), 1):
        k_text = (card.findtext('k') or '').strip()

        card_bq = _first_nonempty_direct_blockquote(card)
        if card_bq is not None:
            original = ET.tostring(card_bq, encoding='unicode')
            transformed = transform_plain_reference_xrs(original)
            if transformed != original:
                candidates.append({
                    'scope': 'card',
                    'card_index': card_index,
                    'k': k_text,
                    'text': ''.join(card_bq.itertext()).strip(),
                    'transformed': transformed,
                })

        for meaning in card.findall('./meaning'):
            meaning_index = (meaning.findtext('meaningIndex') or '').strip()
            meaning_bq = _first_nonempty_direct_blockquote(meaning)
            if meaning_bq is None:
                continue

            original = ET.tostring(meaning_bq, encoding='unicode')
            transformed = transform_plain_reference_xrs(original)
            if transformed == original:
                continue

            candidates.append({
                'scope': 'meaning',
                'card_index': card_index,
                'k': k_text,
                'meaning_index': meaning_index,
                'text': ''.join(meaning_bq.itertext()).strip(),
                'transformed': transformed,
            })

    return candidates


def format_shadow_reference_report(candidates):
    lines = [f'Shadow reference candidates: {len(candidates)}', '']
    for candidate in candidates:
        header = f'{candidate["scope"]}: {candidate["k"]}'
        if candidate.get('meaning_index'):
            header += f' [{candidate["meaning_index"]}]'
        lines.append(header)
        lines.append(f'text: {candidate["text"]}')
        lines.append(f'would become: {candidate["transformed"]}')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'
