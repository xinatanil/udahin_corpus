import re
import sys
import xml.etree.ElementTree as ET
from constants import linkKeyword
from reference_utils import render_reference_list


def transform_plain_reference_xrs(content):
    sr_pattern = re.compile(
        r'<blockquote>\s*\(\s*ср\.\s+'
        r'(?P<main>[^<()]+?)'
        r'\s*\)\s*(?P<punct>[.;])?\s*</blockquote>',
        flags=re.M,
    )

    def sr_replacer(match):
        main_rendered = render_reference_list(match.group("main"))
        if not main_rendered:
            return match.group(0)

        punct = match.group("punct") or ""
        return f'<xr>(ср. {main_rendered}){punct}</xr>'

    content = sr_pattern.sub(sr_replacer, content)

    pattern = re.compile(
        r'<blockquote>\s*(?P<prefix>'
        r'то же,\s*что|'
        r'см\.|'
        r'и\.\s*д\.\s*от|'
        r'деепр\.\s*от|'
        r'понуд\.\s*от|'
        r'взаимн\.\s*от|'
        r'страд\.\s*от|'
        r'возвр\.\s*от|'
        r'уподоб\.\s*от|'
        r'парное\s*к|'
        r'многокр\.\s*от|'
        r'отвл\.\s*от|'
        r'уменьш\.\s*от|'
        r'уменьш\.-ласк\.\s*от|'
        r'отриц\.\s*от|'
        r'противоп\.|'
        r'прил\.\s*от|'
        r'уменьш\.\s*к'
        r')\s+'
        r'(?P<main>[^<()]+?)'
        r'(?P<note>\s*\(\s*см\.\s*(?P<note_refs>[^<()]+?)\s*\))?'
        r'(?P<punct>[.;])?\s*</blockquote>',
        flags=re.M,
    )

    def replacer(match):
        main_rendered = render_reference_list(match.group("main"))
        if not main_rendered:
            return match.group(0)

        note = ""
        note_refs = match.group("note_refs")
        if note_refs is not None:
            note_rendered = render_reference_list(note_refs)
            if not note_rendered:
                return match.group(0)
            note = f' (см. {note_rendered})'

        punct = match.group("punct") or ""
        prefix = re.sub(r"\s+", " ", match.group("prefix").strip())
        return f'<xr>{prefix} {main_rendered}{note}{punct}</xr>'

    return pattern.sub(replacer, content)


def transform_content(content):
    content = transform_plain_reference_xrs(content)

    linked_sr_pattern = re.compile(
        r'<blockquote>\s*(\(\s*ср\.\s*(?:<wordLink[^>]*/>\s*(?:,\s*)?)+\s*\))\s*</blockquote>',
        flags=re.M,
    )
    content = linked_sr_pattern.sub(r'<xr>\1</xr>', content)

    linked_sm_pattern = re.compile(
        r'<blockquote>\s*(\(\s*см\.\s*(?:<wordLink[^>]*/>\s*(?:,\s*)?)+\s*\)[.;]?)\s*</blockquote>',
        flags=re.M,
    )
    content = linked_sm_pattern.sub(r'<xr>\1</xr>', content)

    # Find all <blockquote> that consist solely of a cross-reference and replace them with <xr>.
    standalone_pattern = (
        r'<blockquote>\s*('
        r'\(?\s*' + linkKeyword + r'\s*<wordLink[^>]*/>\s*\)?[.,;]?'
        r')\s*</blockquote>'
    )
    content_new = re.sub(standalone_pattern, r'<xr>\1</xr>', content, flags=re.M)

    # Also catch "то же, что <wordLink...>(см. <wordLink...>)." style blockquotes.
    same_as_pattern = (
        r'<blockquote>\s*('
        r'то же,\s*что\s*<wordLink[^>]*/>'
        r'\s*\(\s*см\.\s*<wordLink[^>]*/>\s*\)[.,;]?'
        r')\s*</blockquote>'
    )
    content_new = re.sub(same_as_pattern, r'<xr>\1</xr>', content_new, flags=re.M)
    content_new = re.sub(r'(<xr>то же,\s*что\s*<wordLink[^>]*/>)\(', r'\1 (', content_new)

    # Also catch "то же, что <wordLink...>(ср. <wordLink...>)." style blockquotes.
    same_as_compare_pattern = (
        r'<blockquote>\s*('
        r'то же,\s*что\s*<wordLink[^>]*/>'
        r'\s*\(\s*ср\.\s*<wordLink[^>]*/>\s*\)[.,;]?'
        r')\s*</blockquote>'
    )
    content_new = re.sub(same_as_compare_pattern, r'<xr>\1</xr>', content_new, flags=re.M)
    content_new = re.sub(r'(<xr>то же,\s*что\s*<wordLink[^>]*/>)\(', r'\1 (', content_new)

    # Also catch pure cross-reference blockquotes with a parenthesized "прим. см." note.
    note_ref_pattern = (
        r'<blockquote>\s*('
        + linkKeyword +
        r'\s*<wordLink[^>]*/>'
        r'\s*\(\s*прим\.\s*см\.\s*<wordLink[^>]*/>\s*\)[.,;]?'
        r')\s*</blockquote>'
    )
    content_new = re.sub(note_ref_pattern, r'<xr>\1</xr>', content_new, flags=re.M)
    content_new = re.sub(
        r'(<xr>' + linkKeyword + r'\s*<wordLink[^>]*/>)\(',
        r'\1 (',
        content_new
    )

    paired_xr_pattern = (
        r'<blockquote>\s*('
        r'парное\s*к\s*<wordLink[^>]*/>\s*и\s*к\s*<wordLink[^>]*/>[.;]'
        r')\s*</blockquote>'
    )
    content_new = re.sub(paired_xr_pattern, r'<xr>\1</xr>', content_new, flags=re.M)

    return content_new


MIXED_REF_BLOCKQUOTE_RE = re.compile(
    r'^<blockquote>\s*'
    r'(?P<note>\((?:ср\.|см\.) .*?<wordLink[^>]*/>.*?\))'
    r'\s+'
    r'(?P<rest>.+)'
    r'</blockquote>$',
    flags=re.S,
)

MIXED_PREFIX_REF_BLOCKQUOTE_RE = re.compile(
    r'^<blockquote>\s*'
    r'(?P<note>'
    r'(?:'
    r'и\.\s*д\.\s*от|'
    r'деепр\.\s*от|'
    r'понуд\.\s*от|'
    r'взаимн\.\s*от|'
    r'страд\.\s*от|'
    r'возвр\.\s*от|'
    r'возвр\.-\s*страд\.\s*от'
    r')\s*<wordLink[^>]*/>'
    r')'
    r'\s+'
    r'(?P<rest>.+)'
    r'</blockquote>$',
    flags=re.S,
)


def split_mixed_reference_blockquote_xml(xml: str) -> str | None:
    stripped = xml.strip()
    match = MIXED_REF_BLOCKQUOTE_RE.match(stripped)
    if not match:
        match = MIXED_PREFIX_REF_BLOCKQUOTE_RE.match(stripped)
    if not match:
        return None

    note = match.group('note').strip()
    rest = match.group('rest').strip()
    if not rest:
        return None
    if rest.startswith('('):
        return None
    if not re.match(r'^[а-яё]', rest, flags=re.IGNORECASE):
        return None

    return f'<wrapper><xr>{note}</xr><blockquote>{rest}</blockquote></wrapper>'


def transform_tree(tree):
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for blockquote in list(root.iter('blockquote')):
        parent = parent_map.get(blockquote)
        if parent is None:
            continue

        original = ET.tostring(blockquote, encoding='unicode')
        split_xml = split_mixed_reference_blockquote_xml(original)
        if split_xml is not None:
            try:
                wrapper = ET.fromstring(split_xml)
            except ET.ParseError:
                wrapper = None

            if wrapper is not None:
                idx = list(parent).index(blockquote)
                parent.remove(blockquote)
                new_children = list(wrapper)
                for child in new_children[:-1]:
                    child.tail = '\n'
                if new_children:
                    new_children[-1].tail = blockquote.tail
                for offset, child in enumerate(new_children):
                    parent.insert(idx + offset, child)
                continue

        transformed = transform_content(original)
        if transformed == original:
            continue

        try:
            replacement = ET.fromstring(transformed)
        except ET.ParseError:
            continue

        replacement.tail = blockquote.tail
        idx = list(parent).index(blockquote)
        parent.remove(blockquote)
        parent.insert(idx, replacement)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 identify_cross_references.py <input.xml> <output.xml>")
        return 1

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    with open(input_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    content_new = transform_content(content)

    with open(output_filename, "w", encoding='utf-8') as output_file:
        output_file.write(content_new)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
