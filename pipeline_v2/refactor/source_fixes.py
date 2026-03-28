from __future__ import annotations

import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET


RULES_PATH = Path(__file__).resolve().parents[1] / 'rules' / 'source_fixes.json'


def _text(element: ET.Element) -> str:
    return ''.join(element.itertext()).strip()


def load_source_fix_rules() -> dict:
    with RULES_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)


def split_card_by_rule(root: ET.Element, rule: dict) -> int:
    fixes_applied = 0

    for card in list(root.findall('card')):
        k = card.find('k')
        if k is None or (k.text or '').strip() != rule['match_k']:
            continue

        blockquotes = card.findall('blockquote')
        texts = [_text(bq) for bq in blockquotes]
        if not blockquotes:
            continue
        if not all(required in texts for required in rule['required_blockquotes']):
            continue

        first_bq = next(
            (bq for bq in blockquotes if _text(bq) == rule['rewrite_first_blockquote_from']),
            None,
        )
        second_bq = next(
            (bq for bq in blockquotes if _text(bq) == rule['split_at_blockquote']),
            None,
        )
        if first_bq is None or second_bq is None:
            continue

        k.text = rule['card_k_to']
        first_bq.text = rule['rewrite_first_blockquote_to']

        children = list(card)
        second_index = children.index(second_bq)
        trailing_children = children[second_index + 1:]
        if not trailing_children:
            continue

        new_card = ET.Element('card')
        new_k = ET.SubElement(new_card, 'k')
        new_k.text = rule['new_card_k']
        for child in trailing_children:
            card.remove(child)
            new_card.append(copy.deepcopy(child))

        card.remove(second_bq)

        root.insert(list(root).index(card) + 1, new_card)
        fixes_applied += 1

    return fixes_applied


def apply_source_fixes(root: ET.Element) -> int:
    total = 0
    rules = load_source_fix_rules()
    for rule in rules.get('split_cards', []):
        total += split_card_by_rule(root, rule)
    return total
