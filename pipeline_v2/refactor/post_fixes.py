from __future__ import annotations

import xml.etree.ElementTree as ET


def normalize_homonym_index_colons(root: ET.Element) -> int:
    fixes_applied = 0

    for homonym in root.iter('homonym'):
        homonym_index = homonym.find('homonymIndex')
        if homonym_index is None or not homonym_index.text:
            continue

        text = homonym_index.text.strip()
        if not text.endswith(':'):
            continue

        homonym_index.text = text[:-1].rstrip()
        if homonym.find('collocationIdentifier') is None:
            colloc = ET.Element('collocationIdentifier')
            colloc.text = ':'
            children = list(homonym)
            insert_at = children.index(homonym_index) + 1
            homonym.insert(insert_at, colloc)
        fixes_applied += 1

    return fixes_applied


def fix_baaky_entry(root: ET.Element) -> int:
    fixes_applied = 0

    for card in root.findall('card'):
        k = card.find('k')
        if k is None or (k.text or '').strip() != 'баакы':
            continue

        homonyms = card.findall('homonym')
        if len(homonyms) < 2:
            continue

        first = homonyms[0]
        homonym_index = first.find('homonymIndex')
        if homonym_index is None or (homonym_index.text or '').strip() != 'баакы I':
            continue

        first_trn = first.find('trn')
        if first_trn is not None and ''.join(first_trn.itertext()).strip() == 'бааки':
            first_trn.tag = 'alternativeForm'
            fixes_applied += 1

    return fixes_applied


def apply_post_fixes(root: ET.Element) -> int:
    total = 0
    total += normalize_homonym_index_colons(root)
    total += fix_baaky_entry(root)
    return total
