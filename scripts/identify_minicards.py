import sys
import re
import xml.etree.ElementTree as ET

def process_element(element):
    children = list(element)
    
    # 1. Rename tags to miniK and miniTrn
    for i in range(len(children)):
        child = children[i]
        if child.tag == 'blockquote' and child.text:
            text = child.text.strip()
            # If it starts with "1) "
            if re.match(r'^1\)\s', text):
                child.tag = 'miniTrn'
                # Find the previous blockquote to rename to miniK
                for j in range(i-1, -1, -1):
                    if children[j].tag == 'blockquote':
                        children[j].tag = 'miniK'
                        break
            # If it starts with "2) ", "3) ", etc.
            elif re.match(r'^\d+\)\s', text):
                child.tag = 'miniTrn'

    # 2. Group into miniCards
    new_children = []
    i = 0
    while i < len(children):
        child = children[i]
        if child.tag == 'miniK':
            mini_card = ET.Element('miniCard')
            mini_card.append(child)
            
            # Find the last miniTrn before the next miniK
            last_mini_trn_idx = i
            j = i + 1
            while j < len(children) and children[j].tag != 'miniK':
                if children[j].tag == 'miniTrn':
                    last_mini_trn_idx = j
                j += 1
            
            # Append everything up to last_mini_trn_idx into the mini_card
            for k in range(i + 1, last_mini_trn_idx + 1):
                mini_card.append(children[k])
                
            new_children.append(mini_card)
            i = last_mini_trn_idx + 1
        else:
            new_children.append(child)
            i += 1
            
    # Replace old children with new children
    element[:] = new_children

def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()

        elements_processed = 0
        for card in root.iter('card'):
            meanings = card.findall('meaning')
            if meanings:
                for meaning in meanings:
                    process_element(meaning)
                    elements_processed += 1
            else:
                process_element(card)
                elements_processed += 1
                
        # Format the XML if python 3.9+
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
        input_filename = 'sources/corrected_source_dict_with_categories.xml' 
        output_filename = 'sources/corrected_source_dict_with_minicards.xml'
        
    process_file(input_filename, output_filename)