#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from llm_split_utils import (
    atoms_to_xml,
    deannotate,
    iter_blockquotes,
    normalize_split_atoms,
)

HYPHEN_INSIDE_WORD_RE = re.compile(r'(?<=\w)\s+-(?=\w)')
HYPHEN_AT_END_RE = re.compile(r'(?<=\w)\s+-$')
HYPHEN_BEFORE_OPEN_PAREN_RE = re.compile(r'(?<=\w)\s*-\s*(?=\()')
HYPHEN_BEFORE_ILI_RE = re.compile(r'(?<=\w)\s*-\s*(?=или\b)', re.I)
HYPHEN_BEFORE_CLOSE_PAREN_RE = re.compile(r'(?<=\w)\s*-\s*(?=\))')
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
DANGLING_SOURCE_END_RE = re.compile(r',\s*$')
LEADING_TARGET_COMMA_RE = re.compile(r'^\s*,')
SOURCE_ENDS_OPEN_PUNCT_RE = re.compile(r'[\(«"“„]\s*$')
PLACEHOLDER_RE = re.compile(r'\[\[[^\]]+\]\]')
TRAILING_RUSSIAN_WORD_RE = re.compile(
    r'^(?P<body>.+?)\s+(?P<tail>(?:он|она|они|оно|мы|вы|я|ты|как|будто|словно|точно))$',
    re.I,
)
RUSSIAN_ENCLITIC_PARTICLES = {'ка', 'де', 'же', 'бы'}


def normalize_hyphen_spacing(text: str) -> str:
    text = HYPHEN_INSIDE_WORD_RE.sub('-', text)
    text = HYPHEN_AT_END_RE.sub('-', text)
    text = HYPHEN_BEFORE_OPEN_PAREN_RE.sub('- ', text)
    text = HYPHEN_BEFORE_ILI_RE.sub('- ', text)
    text = HYPHEN_BEFORE_CLOSE_PAREN_RE.sub('-', text)
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


def char_index_inside_placeholder(text: str, idx: int) -> bool:
    for match in PLACEHOLDER_RE.finditer(text):
        if match.start() < idx < match.end():
            return True
    return False


def has_unbalanced_parentheses(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                return True
    return depth != 0


def common_prefix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    idx = 0
    while idx < limit and a[idx] == b[idx]:
        idx += 1
    return idx


def align_char_boundary(text: str, idx: int, target_starts_with: str | None) -> int | None:
    if idx < 0 or idx >= len(text):
        return None
    prefix = (target_starts_with or '').strip()
    if not prefix:
        return idx if not text[idx].isspace() else None
    if not text[idx].isspace() and text[idx:idx + len(prefix)] == prefix:
        return idx
    best_idx = None
    best_score = -1
    for delta in (1, -1, 2, -2, 3, -3):
        alt = idx + delta
        if alt < 0 or alt >= len(text):
            continue
        if text[alt].isspace():
            continue
        if text[alt:alt + len(prefix)] == prefix:
            return alt
        score = common_prefix_len(text[alt:], prefix)
        if score > best_score:
            best_score = score
            best_idx = alt
    if not text[idx].isspace():
        score = common_prefix_len(text[idx:], prefix)
        if score > best_score:
            best_score = score
            best_idx = idx
    if best_idx is not None and best_score >= min(len(prefix), 8):
        return best_idx
    return None


def invalid_simple_boundary(source: str, target: str) -> bool:
    if DANGLING_SOURCE_END_RE.search(source):
        return True
    if SOURCE_ENDS_OPEN_PUNCT_RE.search(source):
        return True
    if LEADING_TARGET_COMMA_RE.search(target):
        return True
    if has_unbalanced_parentheses(source):
        return True
    if has_unbalanced_parentheses(target):
        return True
    return False


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
        placeholders = item['placeholders']
        annotated_text = item['annotated_text']
        target_starts_at_char = decision.get('target_starts_at_char')
        if target_starts_at_char is not None:
            if not isinstance(target_starts_at_char, int):
                continue
            if target_starts_at_char <= 0 or target_starts_at_char >= len(annotated_text):
                continue
            aligned_idx = align_char_boundary(
                annotated_text,
                target_starts_at_char,
                decision.get('target_starts_with'),
            )
            if aligned_idx is None:
                print(
                    f"Warning: char boundary/prefix mismatch for {bq_id}: "
                    f"idx={target_starts_at_char} target_starts_with={decision.get('target_starts_with')!r}",
                    file=sys.stderr,
                )
                continue
            if char_index_inside_placeholder(annotated_text, aligned_idx):
                print(
                    f"Warning: char boundary points inside placeholder for {bq_id}: "
                    f"idx={aligned_idx}",
                    file=sys.stderr,
                )
                continue
            source_annotated = annotated_text[:aligned_idx].rstrip()
            target_annotated = annotated_text[aligned_idx:].lstrip()
            source = deannotate(source_annotated, placeholders).strip()
            target = deannotate(target_annotated, placeholders).strip()
            if invalid_simple_boundary(source, target):
                print(
                    f"Warning: invalid simple boundary for {bq_id}: "
                    f"source={source!r} target={target!r}",
                    file=sys.stderr,
                )
                continue
        else:
            atoms = item['atoms']
            target_starts_at_atom = decision.get('target_starts_at_atom')
            if target_starts_at_atom is not None:
                if not isinstance(target_starts_at_atom, int):
                    continue
                if target_starts_at_atom <= 1 or target_starts_at_atom > len(atoms):
                    continue
                source_atoms = atoms[:target_starts_at_atom - 1]
                target_atoms = atoms[target_starts_at_atom - 1:]
                expected_target_first = atoms[target_starts_at_atom - 1]
                declared_target_first = decision.get('target_first_atom')
                if declared_target_first != expected_target_first:
                    print(
                        f"Warning: boundary atom mismatch for {bq_id}: "
                        f"expected target_first_atom {expected_target_first!r} "
                        f"got {declared_target_first!r}",
                        file=sys.stderr,
                    )
                    continue
                source = normalize_hyphen_spacing(atoms_to_xml(source_atoms, placeholders).strip())
                target = normalize_hyphen_spacing(atoms_to_xml(target_atoms, placeholders).strip())
                if invalid_simple_boundary(source, target):
                    print(
                        f"Warning: invalid simple boundary for {bq_id}: "
                        f"source={source!r} target={target!r}",
                        file=sys.stderr,
                    )
                    continue
            else:
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
                if invalid_simple_boundary(source, target):
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
