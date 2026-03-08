from constants import linkKeyword
import sys
import xml.etree.ElementTree as ET
import re

def insert_colloc_identifier(card, element, strip_colon=True):
    if strip_colon:
        # Remove ':' from the element's text
        element.text = element.text.strip()[:-1].rstrip()
    
    # Insert <collocationIdentifier>:</collocationIdentifier> after the element
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    current_idx = list(card).index(element)
    card.insert(current_idx + 1, colloc_id)

def get_keyword(card):
    """Get the keyword text from the card's <k> element."""
    k = card.find('k')
    if k is not None and k.text:
        return k.text.strip()
    return None


def process_card(card, children):
    elements_processed = 0
    
    for child in children:
        if child.text and ':' in child.text:
            text = child.text.strip()

            if child.tag == 'k' and text.endswith(':'):
                # <k> ending with ':' — strip colon, insert collocationIdentifier after <k>
                insert_colloc_identifier(card, child)
                elements_processed += 1
            elif child.tag == 'blockquote':
                # Only process blockquotes immediately after <k>
                child_idx = children.index(child)
                if child_idx == 0 or children[child_idx - 1].tag != 'k':
                    continue
                keyword = get_keyword(card)
                if keyword and text.startswith(keyword + ': '):
                    # Strip "keyword: " from blockquote text
                    child.text = text[len(keyword) + 2:]
                    # Insert collocationIdentifier BEFORE the blockquote
                    colloc_id = ET.Element('collocationIdentifier')
                    colloc_id.text = ':'
                    current_idx = list(card).index(child)
                    card.insert(current_idx, colloc_id)
                    elements_processed += 1
                elif keyword and text.startswith(keyword) and text.endswith(':'):
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