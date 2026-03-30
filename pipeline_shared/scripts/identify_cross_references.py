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

    return content_new


def transform_tree(tree):
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for blockquote in list(root.iter('blockquote')):
        parent = parent_map.get(blockquote)
        if parent is None:
            continue

        original = ET.tostring(blockquote, encoding='unicode')
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
