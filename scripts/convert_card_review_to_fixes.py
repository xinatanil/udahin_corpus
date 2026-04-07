#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from llm_split_utils import (
    atoms_to_xml,
    iter_blockquotes,
    normalize_split_atoms,
)

HYPHEN_INSIDE_WORD_RE = re.compile(r'(?<=\w)\s+-(?=\w)')
HYPHEN_AT_END_RE = re.compile(r'(?<=\w)\s+-$')
TRAILING_RUSSIAN_PAREN_RE = re.compile(r'^(?P<body>.*?)(?:\s+)?(?P<paren>\((?:о|об|букв\.?|перен\.?|разг\.?|фольк\.?|погов\.?|собир\.?|этн\.?|поэт\.?|прост\.?).*?\))$')


def normalize_hyphen_spacing(text: str) -> str:
    text = HYPHEN_INSIDE_WORD_RE.sub('-', text)
    text = HYPHEN_AT_END_RE.sub('-', text)
    return text


def normalize_parenthetical_note(source: str, target: str) -> tuple[str, str]:
    m = TRAILING_RUSSIAN_PAREN_RE.match(source.strip())
    if not m:
        return source, target
    body = m.group('body').strip()
    paren = m.group('paren').strip()
    if not body:
        return source, target
    return body, f'{paren} {target}'.strip()


def ex_xml(source: str, target: str) -> str:
    return (
        '<ex>\n'
        f'\t<source>{source}</source>\n'
        f'\t<target>{target}</target>\n'
        '</ex>'
    )


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: convert_card_review_to_fixes.py <review.json> <approved_fixes.json>', file=sys.stderr)
        return 1

    review_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    card_path = review_path.with_name(review_path.name.removesuffix('.review.json') + '.card.xml')
    if not card_path.exists():
        raise SystemExit(f'Card XML not found: {card_path}')

    data = json.loads(review_path.read_text(encoding='utf-8'))
    card_xml = card_path.read_text(encoding='utf-8')
    blockquotes = {item['blockquote_id']: item for item in iter_blockquotes(card_xml)}

    fixes = []
    seen_ids: set[str] = set()
    for decision in data.get('decisions', []):
        bq_id = decision.get('blockquote_id')
        if not bq_id or bq_id in seen_ids:
            continue
        seen_ids.add(bq_id)
        item = blockquotes.get(bq_id)
        if not item:
            continue
        source_atom_count = decision.get('source_atom_count')
        atoms = item['atoms']
        placeholders = item['placeholders']
        if source_atom_count is None:
            source_token_count = decision.get('source_token_count')
            tokens = item['plain_tokens']
            if not isinstance(source_token_count, int):
                continue
            if source_token_count <= 0 or source_token_count >= len(tokens):
                continue
            source = ' '.join(tokens[:source_token_count]).strip()
            target = ' '.join(tokens[source_token_count:]).strip()
        else:
            if not isinstance(source_atom_count, int):
                continue
            if source_atom_count <= 0 or source_atom_count >= len(atoms):
                continue
            source_atoms = atoms[:source_atom_count]
            target_atoms = atoms[source_atom_count:]
            source_atoms, target_atoms = normalize_split_atoms(source_atoms, target_atoms)
            source = normalize_hyphen_spacing(atoms_to_xml(source_atoms, placeholders).strip())
            target = normalize_hyphen_spacing(atoms_to_xml(target_atoms, placeholders).strip())
        source, target = normalize_parenthetical_note(source, target)
        if not source or not target:
            continue
        fixes.append({
            'action': 'replace_exact_xml',
            'find_xml': item['blockquote_xml'],
            'replace_with_xml': ex_xml(source, target),
            'reason': decision.get('reason', ''),
            'confidence': decision.get('confidence', 0),
        })

    out = {
        'card_headword': data.get('card_headword'),
        'source_review_file': str(review_path),
        'fixes': fixes,
    }
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(fixes)} approved fix(es) to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
