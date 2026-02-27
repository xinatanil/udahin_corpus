from constants import linkKeyword
import sys
import xml.etree.ElementTree as ET
import re
from extract_colons import COLON_ENDING_EXCEPTIONS, COLON_OTHER_EXCEPTIONS


def insert_colloc_identifier(card, element, strip_colon=True):
    if strip_colon:
        # Remove ':' from the element's text
        element.text = element.text.strip()[:-1].rstrip()
    
    # Insert <collocationIdentifier>:</collocationIdentifier> after the element
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    current_idx = list(card).index(element)
    card.insert(current_idx + 1, colloc_id)


def is_exception(text):
    """Check if this text is a known exception that should NOT get a collocation identifier."""
    stripped = text.strip()
    return stripped in COLON_ENDING_EXCEPTIONS or stripped in COLON_OTHER_EXCEPTIONS


def process_card(card, children):
    """
    For any element containing ':', if it's not in the exception lists,
    insert a collocation identifier.
    
    Returns: number of elements processed
    """
    elements_processed = 0
    
    for child in children:
        if child.text and ':' in child.text:
            text_stripped = child.text.strip()
            if is_exception(text_stripped):
                continue
            insert_colloc_identifier(card, child)
            elements_processed += 1
    
    return elements_processed


def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()

        total_count = 0
        
        for card in root.iter('card'):
            children = list(card)
            total_count += process_card(card, children)

        print(f"Total collocations processed: {total_count}")

        if hasattr(ET, 'indent'):
            ET.indent(tree, space="\t", level=0)
            
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
    except Exception as e:
        print(f"Error processing XML: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
    else:
        print("Usage: python3 identify_collocation.py <input.xml> <output.xml>")
        sys.exit(1)
        
    process_file(input_filename, output_filename)