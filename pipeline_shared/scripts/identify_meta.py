import re
import sys
import xml.etree.ElementTree as ET

from rule_loader import load_rule_json, load_rule_lines
from constants import metaWord, originWord, linkKeyword

metaOrOriginWord = metaWord + '|' + originWord
manual_exceptions = load_rule_lines('meta_manual_exceptions.txt')
exact_replacements = load_rule_json('meta_exact_replacements.json')
comparison_nonref_words = load_rule_lines('link_nonrefs_after_sr.txt')


def transform_text(content):
    content_new = content

    for rule in exact_replacements:
        flags = 0
        for flag_name in rule.get('flags', []):
            flags |= getattr(re, flag_name)
        content_new = re.sub(
            rule['pattern'],
            rule['replacement'],
            content_new,
            flags=flags,
        )

    content_new = re.sub(
        rf'<blockquote>({metaOrOriginWord}),? ({metaOrOriginWord}),? ?({metaOrOriginWord})?</blockquote>',
        r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n',
        content_new,
        flags=re.M,
    )

    content_new = re.sub(rf'<blockquote>({metaWord})<\/blockquote>', r'<meta>\1</meta>', content_new, flags=re.M)
    content_new = re.sub(rf'<blockquote>({originWord})<\/blockquote>', r'<origin>\1</origin>', content_new, flags=re.M)
    content_new = re.sub(
        r'<blockquote>(усиление к словам, начинающимся на .*?)</blockquote>',
        r'<meta>\1</meta>',
        content_new,
        flags=re.M,
    )
    content_new = re.sub(
        r'<blockquote>(подражательное слово.*)</blockquote>',
        r'<meta>\1</meta>',
        content_new,
        flags=re.M,
    )
    content_new = re.sub(
        r'<blockquote>(\(см\.\s*<wordLink[^>]*/>\s*;\s*видимо,[^<]*\))</blockquote>',
        r'<meta>\1</meta>',
        content_new,
        flags=re.M,
    )

    if comparison_nonref_words:
        comparison_note_pattern = re.compile(
            r'<blockquote>(\(\s*ср\.\s*(?:'
            + '|'.join(re.escape(word) for word in comparison_nonref_words)
            + r')\b[^<]*\))</blockquote>',
            flags=re.I,
        )
        content_new = comparison_note_pattern.sub(r'<meta>\1</meta>', content_new)

    for exc in manual_exceptions:
        content_new = content_new.replace(f'<blockquote>{exc}</blockquote>', f'<meta>{exc}</meta>')

    return content_new


def transform_tree(tree):
    root = tree.getroot()
    re_link_start = re.compile(rf'^(?:{linkKeyword})')
    full_pattern = (
        rf'^({metaOrOriginWord}),?'
        rf'(\s+({metaOrOriginWord}),?)?'
        rf'(\s+({metaOrOriginWord}),?)?'
        rf'(\s+({metaOrOriginWord}),?)?'
        rf'(?=\s|$)'
    )
    re_start_meta = re.compile(full_pattern)
    re_origin_only = re.compile(f'^({originWord})$')

    parent_map = {c: p for p in root.iter() for c in p}

    cards = root.findall('.//card')
    for card in cards:
        for bq in card.findall('.//blockquote'):
            if not bq.text:
                continue
            text_stripped = bq.text.strip()
            match = re.search(r'(южн\.\s+\[[^\]\s]+\])$', text_stripped)
            if not match:
                continue

            matched_text = match.group(1)
            bq.text = text_stripped[:match.start()].rstrip()

            meta_el = ET.Element('meta')
            meta_el.text = matched_text
            meta_el.tail = '\n'

            parent = parent_map[bq]
            bq_idx = list(parent).index(bq)
            parent.insert(bq_idx + 1, meta_el)

        parents_to_check = [card] + card.findall('.//meaning')
        for parent in parents_to_check:
            blockquotes = parent.findall('./blockquote')
            if not blockquotes:
                continue

            bq = blockquotes[0]
            if bq.text is None:
                continue

            text = bq.text.strip()
            if re_link_start.search(text):
                continue

            match = re_start_meta.match(text)
            if not match:
                continue

            words_found = []
            if match.group(1):
                words_found.append(match.group(1).rstrip(','))
            if match.group(3):
                words_found.append(match.group(3).rstrip(','))
            if match.group(5):
                words_found.append(match.group(5).rstrip(','))
            if match.group(7):
                words_found.append(match.group(7).rstrip(','))
            if not words_found:
                continue

            new_elements = []
            for word in words_found:
                tag_name = 'origin' if re_origin_only.match(word) else 'meta'
                el = ET.Element(tag_name)
                el.text = word
                el.tail = '\n'
                new_elements.append(el)

            bq_index = list(parent).index(bq)
            for el in reversed(new_elements):
                parent.insert(bq_index, el)

            new_text = text[match.end():].lstrip()
            if len(bq) > 0 and bq.text and bq.text[-1] == ' ':
                new_text = new_text + ' '
            bq.text = new_text


def transform_content(content):
    content_new = transform_text(content)

    try:
        xml_decl = ''
        if content_new.lstrip().startswith('<?xml'):
            end_index = content_new.find('?>')
            if end_index != -1:
                xml_decl = content_new[:end_index + 2]
                content_new = content_new[end_index + 2:].lstrip()

        root = ET.fromstring(f'<root>{content_new}</root>')
        tree = ET.ElementTree(root)
        transform_tree(tree)

        raw_xml = ET.tostring(root, encoding='unicode')
        content_new = raw_xml.replace('<root>', '', 1).replace('</root>', '', 1)
        if xml_decl:
            content_new = xml_decl + '\n' + content_new

    except ET.ParseError as e:
        print(f'Error parsing XML for meta extraction: {e}')

    return content_new


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 identify_meta.py <input.xml> <output.xml>')
        return 1

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    with open(input_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    content_new = transform_content(content)

    with open(output_filename, 'w', encoding='utf-8') as output_file:
        output_file.write(content_new)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
