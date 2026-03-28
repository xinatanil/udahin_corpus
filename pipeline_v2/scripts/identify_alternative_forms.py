import re
import sys
import xml.etree.ElementTree as ET

from rule_loader import load_rule_json, load_rule_lines

hardcoded_cases = load_rule_lines('alternative_forms_exact.txt')
hardcoded_cases_pattern1 = load_rule_json('alternative_forms_mappings.json')


def transform_content(content):
    content_new = re.sub(
        r'<blockquote>(\(или .+\))</blockquote>',
        r'<alternativeForm>\1</alternativeForm>',
        content,
        flags=re.M
    )

    content_new = re.sub(
        r'<blockquote>(\(неправ\.\s+(?!вместо\b)[^)]+\))</blockquote>',
        r'<alternativeForm>\1</alternativeForm>',
        content_new,
        flags=re.M
    )

    for hc in hardcoded_cases:
        content_new = content_new.replace(
            f'<blockquote>{hc}</blockquote>',
            f'<alternativeForm>{hc}</alternativeForm>'
        )

    content_new = re.sub(
        r'(\s*)<blockquote>(\(точнее\s+[^)]+\))</blockquote>',
        r'\1<alternativeForm>\2</alternativeForm>',
        content_new,
        flags=re.M
    )

    content_new = re.sub(
        r'(\s*)<blockquote>(\(точнее\s+[^)]+\))\s+(.+?)</blockquote>',
        r'\1<alternativeForm>\2</alternativeForm>\1<blockquote>\3</blockquote>',
        content_new,
        flags=re.M
    )

    content_new = re.sub(
        r'(\s*)<blockquote>(\(при наращении аффиксов\s+[^)]+\).*?)</blockquote>',
        r'\1<alternativeForm>\2</alternativeForm>',
        content_new,
        flags=re.M
    )

    content_new = re.sub(
        r'(\s*)<blockquote>(\(орф\.\s+[^)]+\).*?)</blockquote>',
        r'\1<alternativeForm>\2</alternativeForm>',
        content_new,
        flags=re.M
    )

    content_new = re.sub(
        r'(\s*)<blockquote>(\(в произношении\s+[^)]+\))</blockquote>',
        r'\1<alternativeForm>\2</alternativeForm>',
        content_new,
        flags=re.M
    )

    for bq, alt in hardcoded_cases_pattern1.items():
        content_new = content_new.replace(bq, alt)

    return content_new
def transform_tree(tree):
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for bq in list(root.iter('blockquote')):
        parent = parent_map.get(bq)
        if parent is None:
            continue

        original = ET.tostring(bq, encoding='unicode')
        transformed = transform_content(original)
        if transformed == original:
            continue

        try:
            wrapper = ET.fromstring(f'<root>{transformed}</root>')
        except ET.ParseError:
            continue

        idx = list(parent).index(bq)
        parent.remove(bq)

        new_elements = list(wrapper)
        if not new_elements:
            continue

        new_elements[-1].tail = bq.tail
        for offset, new_el in enumerate(new_elements):
            parent.insert(idx + offset, new_el)


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 identify_alternative_forms.py <input.xml> <output.xml>")
        return 1

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    with open(input_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    content_new = transform_content(content)

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(content_new)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())


#(орфографически следует көзөл)
# <k>көпөмсү-</k>
# <blockquote>(вероятно, ошибочно вместо көкөмсү-)</blockquote>

# <k>күлпөт</k>
# <blockquote>(видимо, вместо үлпөт)</blockquote>
