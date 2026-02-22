import sys
import xml.etree.ElementTree as ET
import copy

def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # Create a new root for the output file
        new_root = ET.Element(root.tag, root.attrib)
        new_tree = ET.ElementTree(new_root)

        elements_processed = 0
        for card in root.iter('card'):
            children = list(card)
            for i, child in enumerate(children):
                if child.tag == 'k':
                    if i + 1 < len(children):
                        next_child = children[i + 1]
                        if next_child.tag == 'blockquote' and next_child.text:
                            text_stripped = next_child.text.strip()
                            if text_stripped.endswith(':'):
                                new_root.append(copy.deepcopy(card))
                                elements_processed += 1
                                break

        if hasattr(ET, 'indent'):
            ET.indent(new_tree, space="\t", level=0)
            
        new_tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print(f"Extracted {elements_processed} cards to {output_file}")
    except Exception as e:
        print(f"Error processing XML: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
    else:
        print("Usage: python3 extract_cards_with_colon.py <input.xml> <output.xml>")
        sys.exit(1)
        
    process_file(input_filename, output_filename)
