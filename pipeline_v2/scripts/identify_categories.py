import sys
import xml.etree.ElementTree as ET


CATEGORY_SEQUENCE_LENGTHS = (6, 5)


def is_numbered_blockquote(element, number):
    return (
        element.tag == 'blockquote'
        and element.text is not None
        and element.text.strip().startswith(f'{number})')
    )


def process_element(element):
    children = list(element)
    i = 0

    while i < len(children):
        matched = False
        for length in CATEGORY_SEQUENCE_LENGTHS:
            if i + length > len(children):
                continue
            chunk = children[i:i + length]
            if all(is_numbered_blockquote(child, idx + 1) for idx, child in enumerate(chunk)):
                for child in chunk:
                    child.tag = 'category'
                i += length
                matched = True
                break
        if not matched:
            i += 1


def transform_tree(tree):
    root = tree.getroot()
    elements_processed = 0

    for card in root.iter('card'):
        process_element(card)
        elements_processed += 1
        for meaning in card.findall('meaning'):
            process_element(meaning)
            elements_processed += 1
        for homonym in card.findall('homonym'):
            process_element(homonym)
            elements_processed += 1
            for meaning in homonym.findall('meaning'):
                process_element(meaning)
                elements_processed += 1

    if hasattr(ET, 'indent'):
        ET.indent(tree, space='\t', level=0)

    return elements_processed


def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        transform_tree(tree)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
    except Exception as e:
        print(f"Error processing XML: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
    else:
        input_filename = 'sources/corrected_source_dict.xml'
        output_filename = 'sources/corrected_source_dict_with_categories.xml'

    process_file(input_filename, output_filename)
