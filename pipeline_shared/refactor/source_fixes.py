from __future__ import annotations

import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET


RULES_PATH = Path(__file__).resolve().parents[1] / 'rules' / 'source_fixes.json'


def load_source_fix_rules() -> dict:
    with RULES_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)


def child_text(elem: ET.Element) -> str:
    return ''.join(elem.itertext()).strip()


def apply_split_card_rule(root: ET.Element, rule: dict) -> int:
    applied = 0
    for card in list(root.findall('card')):
        k_elem = card.find('k')
        if k_elem is None or (k_elem.text or '').strip() != rule['match_k']:
            continue

        blockquotes = card.findall('blockquote')
        blockquote_texts = [child_text(bq) for bq in blockquotes]
        required = rule.get('required_blockquotes', [])
        if any(req not in blockquote_texts for req in required):
            continue

        split_idx = None
        for idx, bq in enumerate(blockquotes):
            if child_text(bq) == rule['split_at_blockquote']:
                split_idx = idx
                break
        if split_idx is None:
            continue

        if rule.get('rewrite_first_blockquote_from'):
            first_bq = blockquotes[0] if blockquotes else None
            if first_bq is not None and child_text(first_bq) == rule['rewrite_first_blockquote_from']:
                first_bq.text = rule['rewrite_first_blockquote_to']

        k_elem.text = rule['card_k_to']

        new_card = ET.Element('card')
        new_k = ET.SubElement(new_card, 'k')
        new_k.text = rule['new_card_k']

        moving = blockquotes[split_idx + 1 :]
        for bq in moving:
            card.remove(bq)
            new_card.append(copy.deepcopy(bq))

        split_marker = blockquotes[split_idx]
        card.remove(split_marker)

        card_index = list(root).index(card)
        root.insert(card_index + 1, new_card)
        applied += 1

    return applied


def apply_source_fixes(root: ET.Element) -> int:
    rules = load_source_fix_rules()
    applied = 0

    for rule in rules.get('split_cards', []):
        applied += apply_split_card_rule(root, rule)

    return applied
