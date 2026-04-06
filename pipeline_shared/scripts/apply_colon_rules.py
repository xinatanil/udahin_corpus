#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from constants import metaWord, originWord
from rule_loader import load_rule_lines


def collapse_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_rule_entry(text: str) -> str:
    text = text.strip()
    if text.startswith('blockquote_xml:'):
        text = text.split(':', 1)[1].strip()
    return collapse_ws(text)


def normalize_xml(elem: ET.Element) -> str:
    return collapse_ws(ET.tostring(elem, encoding='unicode'))


def serialize_element_only(elem: ET.Element) -> str:
    raw = ET.tostring(elem, encoding='unicode').strip()
    reparsed = ET.fromstring(raw)
    return ET.tostring(reparsed, encoding='unicode')


META_COLLOCATION_RULES = frozenset(normalize_rule_entry(line) for line in load_rule_lines('colon_meta_collocation.txt'))
XR_COLLOCATION_RULES = frozenset(normalize_rule_entry(line) for line in load_rule_lines('colon_xr_collocation.txt'))
ALTFORM_COLLOCATION_RULES = frozenset(normalize_rule_entry(line) for line in load_rule_lines('colon_altform_collocation.txt'))
COLLOCATION_RULES = frozenset(normalize_rule_entry(line) for line in load_rule_lines('colon_collocation.txt'))
REJECT_RULES = frozenset(normalize_rule_entry(line) for line in load_rule_lines('colon_reject.txt'))

ALL_RULES = (
    META_COLLOCATION_RULES
    | XR_COLLOCATION_RULES
    | ALTFORM_COLLOCATION_RULES
    | COLLOCATION_RULES
    | REJECT_RULES
)

RE_ORIGIN_ONLY = re.compile(f'^{originWord}$')
RE_META_ORIGIN_ONLY = re.compile(f'^(?:{metaWord}|{originWord})$')


def replace_outer_tag(xml: str, new_tag: str) -> str:
    xml = re.sub(r'^<blockquote>', f'<{new_tag}>', xml)
    xml = re.sub(r'</blockquote>$', f'</{new_tag}>', xml)
    return xml


def insert_collocation_identifier(parent: ET.Element, element: ET.Element) -> None:
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    colloc_id.tail = '\n'
    idx = list(parent).index(element)
    parent.insert(idx + 1, colloc_id)


def strip_trailing_colon_from_xml(xml: str, new_tag: str | None = None, replacement: str = '') -> str:
    if new_tag is not None:
        xml = replace_outer_tag(xml, new_tag)
    tag = new_tag or 'blockquote'
    return re.sub(rf':\s*</{tag}>$', f'{replacement}</{tag}>', xml)


def replace_element_from_xml(parent: ET.Element, element: ET.Element, new_xml: str) -> ET.Element:
    replacement = ET.fromstring(new_xml)
    replacement.tail = element.tail
    idx = list(parent).index(element)
    parent.remove(element)
    parent.insert(idx, replacement)
    return replacement


def transform_tree(tree: ET.ElementTree, mode: str = 'all') -> int:
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}
    applied = 0

    for blockquote in list(root.iter('blockquote')):
        normalized = normalize_xml(blockquote)
        if normalized not in ALL_RULES:
            continue

        if normalized in REJECT_RULES:
            continue

        parent = parent_map.get(blockquote)
        if parent is None:
            continue
        original_xml = serialize_element_only(blockquote)

        if normalized in XR_COLLOCATION_RULES:
            if mode not in {'all', 'semantic'}:
                continue
            new_xml = strip_trailing_colon_from_xml(original_xml, new_tag='xr')
            replacement = replace_element_from_xml(parent, blockquote, new_xml)
            insert_collocation_identifier(parent, replacement)
            applied += 1
            continue

        if normalized in ALTFORM_COLLOCATION_RULES:
            if mode not in {'all', 'semantic'}:
                continue
            new_xml = strip_trailing_colon_from_xml(original_xml, new_tag='alternativeForm')
            replacement = replace_element_from_xml(parent, blockquote, new_xml)
            insert_collocation_identifier(parent, replacement)
            applied += 1
            continue

        if normalized in META_COLLOCATION_RULES:
            if mode not in {'all', 'semantic'}:
                continue
            text = collapse_ws(''.join(blockquote.itertext()))
            stripped = text[:-1].rstrip() if text.endswith(':') else text
            new_tag = None
            if len(blockquote) == 0 and RE_META_ORIGIN_ONLY.fullmatch(stripped):
                new_tag = 'origin' if RE_ORIGIN_ONLY.fullmatch(stripped) else 'meta'
            new_xml = strip_trailing_colon_from_xml(original_xml, new_tag=new_tag)
            replacement = replace_element_from_xml(parent, blockquote, new_xml)
            insert_collocation_identifier(parent, replacement)
            applied += 1
            continue

        if normalized in COLLOCATION_RULES:
            if mode not in {'all', 'semantic'}:
                continue
            new_xml = strip_trailing_colon_from_xml(original_xml)
            replacement = replace_element_from_xml(parent, blockquote, new_xml)
            insert_collocation_identifier(parent, replacement)
            applied += 1
            continue

    if hasattr(ET, 'indent'):
        ET.indent(tree, space="\t", level=0)

    return applied


def main() -> int:
    args = sys.argv[1:]
    mode = 'all'
    if len(args) >= 2 and args[0] == '--mode':
        if len(args) < 4:
            print('Usage: python3 apply_colon_rules.py [--mode all|semantic|late] <input.xml> <output.xml>')
            return 1
        mode = args[1]
        args = args[2:]

    if len(args) < 2:
        print('Usage: python3 apply_colon_rules.py [--mode all|semantic|late] <input.xml> <output.xml>')
        return 1
    if mode not in {'all', 'semantic', 'late'}:
        print('Mode must be one of: all, semantic, late')
        return 1

    input_path = Path(args[0])
    output_path = Path(args[1])

    tree = ET.parse(input_path)
    applied = transform_tree(tree, mode=mode)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f'Applied {applied} colon rule(s) [{mode}]')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
