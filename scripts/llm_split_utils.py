#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Iterable

BLOCKQUOTE_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.S)
TAG_RE = re.compile(r'<[^>]+>')
WORDLINK_WORD_RE = re.compile(r'\bword="([^"]+)"')
SPACED_DASH_RE = re.compile(r'\s([\-–—])\s')
ATOM_RE = re.compile(r'\[\[[^\]]+\]\]|\w+|[^\w\s]', re.UNICODE)
TRAILING_TARGET_WORDS = {
    'горюя', 'как', 'будто', 'словно', 'точно', 'погов', 'фольк', 'собир',
    'мы', 'он', 'она', 'они', 'оно', 'это', 'этот', 'эта', 'эти',
    'разг', 'кошма', 'лат', 'уст', 'этн',
}
NO_SPACE_BEFORE = {'.', ',', ';', ':', '!', '?', ')', ']', '}', '»', '”', '%'}
NO_SPACE_AFTER = {'(', '[', '{', '«', '„', '“', '-', '—', '–'}
PUNCT_ONLY_RE = re.compile(r'^[.,;:!?]+$')
TARGET_PHRASE_PATTERNS = [
    ['см', '.'],
    ['то', 'же', ',', 'что'],
    ['то', 'же', 'что'],
]


def placeholder_label(tag_xml: str, idx: int) -> str:
    if tag_xml.startswith('<wordLink'):
        m = WORDLINK_WORD_RE.search(tag_xml)
        word = m.group(1) if m else 'wordLink'
        return f'[[WL{idx}|{word}]]'
    m = re.match(r'<([A-Za-z0-9_:-]+)', tag_xml)
    tag = m.group(1) if m else 'TAG'
    return f'[[TAG{idx}|{tag}]]'


def annotate_inner_xml(inner_xml: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    parts: list[str] = []
    last = 0
    idx = 1
    for m in TAG_RE.finditer(inner_xml):
        parts.append(inner_xml[last:m.start()])
        tag_xml = m.group(0)
        placeholder = placeholder_label(tag_xml, idx)
        idx += 1
        placeholders[placeholder] = tag_xml
        parts.append(placeholder)
        last = m.end()
    parts.append(inner_xml[last:])
    text = ''.join(parts).strip()
    dash_idx = 1

    def repl_dash(m: re.Match[str]) -> str:
        nonlocal dash_idx
        dash = m.group(1)
        placeholder = f'[[SPD{dash_idx}|{dash}]]'
        dash_idx += 1
        placeholders[placeholder] = f' {dash} '
        return placeholder

    text = SPACED_DASH_RE.sub(repl_dash, text)
    return text, placeholders


def deannotate(text: str, placeholders: dict[str, str]) -> str:
    out = text
    for placeholder, tag_xml in placeholders.items():
        out = out.replace(placeholder, tag_xml)
    return out


def atomise(text: str) -> list[str]:
    return ATOM_RE.findall(text)


def join_atoms(atoms: Iterable[str]) -> str:
    atoms = list(atoms)
    if not atoms:
        return ''
    out = [atoms[0]]
    ascii_quote_open = atoms[0] == '"'
    for prev, atom in zip(atoms, atoms[1:]):
        prev_is_open_ascii_quote = prev == '"' and ascii_quote_open
        atom_is_closing_ascii_quote = atom == '"' and ascii_quote_open
        atom_is_spaced_dash = atom.startswith('[[SPD')
        prev_is_spaced_dash = prev.startswith('[[SPD')
        if atom == '"':
            ascii_quote_open = not ascii_quote_open
        if (
            atom_is_closing_ascii_quote
            or atom_is_spaced_dash
            or prev_is_spaced_dash
            or atom in NO_SPACE_BEFORE
            or prev_is_open_ascii_quote
            or prev in NO_SPACE_AFTER
        ):
            out.append(atom)
        else:
            out.append(' ' + atom)
    return ''.join(out)


def normalize_split_atoms(source_atoms: list[str], target_atoms: list[str]) -> tuple[list[str], list[str]]:
    src = list(source_atoms)
    tgt = list(target_atoms)
    while True:
        moved = False
        lowered = [a.lower() for a in src]
        for pattern in TARGET_PHRASE_PATTERNS:
            plen = len(pattern)
            for start in range(1, len(src) - plen + 1):
                if lowered[start:start + plen] == pattern:
                    tgt = src[start:] + tgt
                    src = src[:start]
                    moved = True
                    break
            if moved:
                break
        if not moved:
            break
    while src:
        i = len(src)
        while i > 0 and PUNCT_ONLY_RE.fullmatch(src[i - 1]):
            i -= 1
        if i == 0:
            break
        key = src[i - 1].strip('.,:;!?"«»„“').lower()
        if key not in TRAILING_TARGET_WORDS:
            break
        moving = src[i - 1:]
        src = src[:i - 1]
        tgt = moving + tgt
    return src, tgt


def iter_blockquotes(card_xml: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for idx, m in enumerate(BLOCKQUOTE_RE.finditer(card_xml), 1):
        inner_xml = m.group(1).strip()
        blockquote_xml = m.group(0)
        annotated_text, placeholders = annotate_inner_xml(inner_xml)
        atoms = atomise(annotated_text)
        plain_text = re.sub(r'<[^>]+>', '', inner_xml)
        plain_tokens = re.findall(r'\S+', plain_text)
        items.append({
            'blockquote_id': f'bq_{idx}',
            'blockquote_xml': blockquote_xml,
            'inner_xml': inner_xml,
            'annotated_text': annotated_text,
            'placeholders': placeholders,
            'atoms': atoms,
            'plain_text': plain_text,
            'plain_tokens': plain_tokens,
        })
    return items


def atoms_to_xml(atoms: list[str], placeholders: dict[str, str]) -> str:
    return deannotate(join_atoms(atoms), placeholders)
