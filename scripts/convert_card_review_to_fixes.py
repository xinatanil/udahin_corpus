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
TRAILING_RUSSIAN_PAREN_RE = re.compile(r'^(?P<body>.+?)\s+(?P<paren>\((?:о|об|букв\.?|перен\.?|разг\.?|фольк\.?|погов\.?|собир\.?|этн\.?|поэт\.?|прост\.?).*?\))$')
TRAILING_META_MARKERS_RE = re.compile(
    r'^(?P<body>.+?)\s+(?P<meta>(?:погов|фольк|разг|собир|этн|уст|поэт|прост|книжн|обл|редк|шутл|ирон|южн|сев|стих)\.)$',
    re.I,
)
KYR_WORD_RE = r"[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'-]+"
RUS_WORD_RE = r"[А-Яа-яЁё]+"
LEADING_ILI_CHAIN_RE = re.compile(
    rf'^(?P<chain>или(?:\s+{KYR_WORD_RE}){{1,6}})\s+(?P<rest>{RUS_WORD_RE}.*)$'
)
TRAILING_RUSSIAN_GLOSS_RE = re.compile(
    r'^(?P<body>.+?)\s+(?P<gloss>(?:звукоподражание(?:\s+[А-Яа-яЁё]+){0,3}|название(?:\s+[А-Яа-яЁё]+){0,3}))$',
    re.I,
)
LEADING_KYRGYZ_CONTINUATION_RE = re.compile(
    rf'^(?P<cont>(?:{KYR_WORD_RE}\s+){{1,4}}экен)\s+(?P<rest>[А-ЯЁ][^\n]*)$'
)
LEADING_HYPHEN_FORM_RE = re.compile(
    rf'^(?P<form>{KYR_WORD_RE}-)\s+(?P<rest>[А-ЯЁа-яё].*)$'
)
LEADING_GLUE_HYPHEN_FORM_RE = re.compile(
    rf'^(?P<form>{KYR_WORD_RE}-)(?P<rest>[А-ЯЁа-яё].*)$'
)
LEADING_KYRGYZ_TO_RUSSIAN_RE = re.compile(
    rf'^(?P<cont>(?:{KYR_WORD_RE}\s+){{1,5}}(?:калды|болду|экен|дейт|деди|турган|болсо|болбосо|таппай))\s+(?P<rest>[А-ЯЁа-яё].*)$'
)
EXACT_SPLIT_OVERRIDES = {
    'шак түшүптүр пала роса.': ('шак түшүптүр', 'пала роса.'),
    'түндөгү түшүң туш келген сон, что ты видел ночью, исполнился;': ('түндөгү түшүң туш келген', 'сон, что ты видел ночью, исполнился;'),
}
DANGLING_SOURCE_END_RE = re.compile(r',\s*$')
TRAILING_RUSSIAN_WORD_RE = re.compile(
    r'^(?P<body>.+?)\s+(?P<tail>(?:он|она|они|оно|мы|вы|я|ты|как|будто|словно|точно))$',
    re.I,
)
RUSSIAN_ENCLITIC_PARTICLES = {'ка', 'де', 'же', 'бы'}


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


def normalize_trailing_meta_marker(source: str, target: str) -> tuple[str, str]:
    m = TRAILING_META_MARKERS_RE.match(source.strip())
    if not m:
        return source, target
    body = m.group('body').strip()
    meta = m.group('meta').strip()
    if not body:
        return source, target
    return body, f'{meta} {target}'.strip()


def normalize_leading_ili_chain(source: str, target: str) -> tuple[str, str]:
    m = LEADING_ILI_CHAIN_RE.match(target.strip())
    if not m:
        return source, target
    chain = m.group('chain').strip()
    rest = m.group('rest').strip()
    if not rest:
        return source, target
    return f'{source} {chain}'.strip(), rest


def normalize_trailing_russian_gloss(source: str, target: str) -> tuple[str, str]:
    m = TRAILING_RUSSIAN_GLOSS_RE.match(source.strip())
    if not m:
        return source, target
    body = m.group('body').strip()
    gloss = m.group('gloss').strip()
    if not body:
        return source, target
    return body, f'{gloss} {target}'.strip()


def normalize_leading_kyrgyz_continuation(source: str, target: str) -> tuple[str, str]:
    m = LEADING_KYRGYZ_CONTINUATION_RE.match(target.strip())
    if not m:
        return source, target
    cont = m.group('cont').strip()
    rest = m.group('rest').strip()
    if not rest:
        return source, target
    return f'{source} {cont}'.strip(), rest


def normalize_leading_hyphen_form(source: str, target: str) -> tuple[str, str]:
    m = LEADING_HYPHEN_FORM_RE.match(target.strip())
    if not m:
        return source, target
    form = m.group('form').strip()
    rest = m.group('rest').strip()
    if not rest:
        return source, target
    return f'{source} {form}'.strip(), rest


def normalize_leading_glued_hyphen_form(source: str, target: str) -> tuple[str, str]:
    m = LEADING_GLUE_HYPHEN_FORM_RE.match(target.strip())
    if not m:
        return source, target
    form = m.group('form').strip()
    rest = m.group('rest').strip()
    if not rest:
        return source, target
    first_word_match = re.match(r'^([А-ЯЁа-яё]+)', rest)
    if first_word_match and first_word_match.group(1).lower() in RUSSIAN_ENCLITIC_PARTICLES:
        return source, target
    return f'{source} {form}'.strip(), rest


def normalize_leading_kyrgyz_before_russian(source: str, target: str) -> tuple[str, str]:
    m = LEADING_KYRGYZ_TO_RUSSIAN_RE.match(target.strip())
    if not m:
        return source, target
    cont = m.group('cont').strip()
    rest = m.group('rest').strip()
    if not rest:
        return source, target
    return f'{source} {cont}'.strip(), rest


def normalize_trailing_russian_word(source: str, target: str) -> tuple[str, str]:
    m = TRAILING_RUSSIAN_WORD_RE.match(source.strip())
    if not m:
        return source, target
    body = m.group('body').strip()
    tail = m.group('tail').strip()
    if not body:
        return source, target
    return body, f'{tail} {target}'.strip()


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
        atoms = item['atoms']
        placeholders = item['placeholders']
        target_starts_at_atom = decision.get('target_starts_at_atom')
        if target_starts_at_atom is not None:
            if not isinstance(target_starts_at_atom, int):
                continue
            if target_starts_at_atom <= 1 or target_starts_at_atom > len(atoms):
                continue
            source_atoms = atoms[:target_starts_at_atom - 1]
            target_atoms = atoms[target_starts_at_atom - 1:]
            expected_source_last = atoms[target_starts_at_atom - 2]
            expected_target_first = atoms[target_starts_at_atom - 1]
            declared_source_last = decision.get('source_last_atom')
            declared_target_first = decision.get('target_first_atom')
            if declared_source_last != expected_source_last or declared_target_first != expected_target_first:
                print(
                    f"Warning: boundary atom mismatch for {bq_id}: "
                    f"expected ({expected_source_last!r}, {expected_target_first!r}) "
                    f"got ({declared_source_last!r}, {declared_target_first!r})",
                    file=sys.stderr,
                )
                continue
            source = normalize_hyphen_spacing(atoms_to_xml(source_atoms, placeholders).strip())
            target = normalize_hyphen_spacing(atoms_to_xml(target_atoms, placeholders).strip())
        else:
            exact_override = EXACT_SPLIT_OVERRIDES.get(item['plain_text'])
            if exact_override is not None:
                source, target = exact_override
                fixes.append({
                    'action': 'replace_exact_xml',
                    'find_xml': item['blockquote_xml'],
                    'replace_with_xml': ex_xml(source, target),
                    'reason': decision.get('reason', ''),
                    'confidence': decision.get('confidence', 0),
                })
                continue
            source_atom_count = decision.get('source_atom_count')
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
            source, target = normalize_trailing_meta_marker(source, target)
            source, target = normalize_leading_ili_chain(source, target)
            source, target = normalize_trailing_russian_gloss(source, target)
            source, target = normalize_leading_kyrgyz_continuation(source, target)
            source, target = normalize_leading_hyphen_form(source, target)
            source, target = normalize_leading_glued_hyphen_form(source, target)
            source, target = normalize_leading_kyrgyz_before_russian(source, target)
            source, target = normalize_trailing_russian_word(source, target)
            if DANGLING_SOURCE_END_RE.search(source):
                continue
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
