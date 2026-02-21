import sys
import xml.etree.ElementTree as ET

def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()

        elements_processed = 0
        for card in root.iter('card'):
            # Iterate using index since we are going to modify the list of children
            for i, child in enumerate(list(card)):
                if child.tag == 'k' and child.text and child.text.strip().endswith(':'):
                    # Remove ':' from <k>'s text
                    child.text = child.text.strip()[:-1].rstrip()
                    
                    # Insert <collocationIdentifier>:</collocationIdentifier> after <k>
                    colloc_id = ET.Element('collocationIdentifier')
                    colloc_id.text = ':'
                    card.insert(i + 1, colloc_id)
                    elements_processed += 1
                        
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
