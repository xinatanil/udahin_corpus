import sys
import xml.etree.ElementTree as ET
import re
import constants

def process_glued_cards(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    # pattern for the second blockquote
    # It starts with a linkKeyword, then captures the rest (someWord), followed by " I, II."
    bq2_pattern = re.compile(rf'^({constants.linkKeyword})(.*?)\s+I,\s*II\.?$')
    
    cards = list(root.findall('card'))
    for card in cards:
        children = list(card)
        if len(children) in [3, 4]:
            if children[0].tag != 'k':
                continue
            
            k_text = children[0].text.strip() if children[0].text else ""
            
            if len(children) == 3:
                if children[1].tag != 'blockquote' or children[2].tag != 'blockquote':
                    continue
                bq1_text = children[1].text.strip() if children[1].text else ""
                optional_bq_text = None
                bq2_text = children[2].text.strip() if children[2].text else ""
            elif len(children) == 4:
                if children[1].tag != 'blockquote' or children[2].tag != 'blockquote' or children[3].tag != 'blockquote':
                    continue
                bq1_text = children[1].text.strip() if children[1].text else ""
                optional_bq_text = children[2].text.strip() if children[2].text else ""
                bq2_text = children[3].text.strip() if children[3].text else ""
                
            # Check bq1 matches "keyWord I, II"
            if bq1_text == f"{k_text} I, II":
                # Check bq2 matches "linkKeyword someWord I, II."
                match = bq2_pattern.match(bq2_text)
                if match:
                    link_kw = match.group(1)
                    some_word = match.group(2)
                    
                    idx = list(root).index(card)
                    
                    card1 = ET.Element('card')
                    k1 = ET.SubElement(card1, 'k')
                    k1.text = f"{k_text} I"
                    if optional_bq_text is not None:
                        opt_bq1 = ET.SubElement(card1, 'blockquote')
                        opt_bq1.text = optional_bq_text
                    bq1_1 = ET.SubElement(card1, 'blockquote')
                    bq1_1.text = f"{link_kw}{some_word} I."
                    
                    card2 = ET.Element('card')
                    k2 = ET.SubElement(card2, 'k')
                    k2.text = f"{k_text} II"
                    if optional_bq_text is not None:
                        opt_bq2 = ET.SubElement(card2, 'blockquote')
                        opt_bq2.text = optional_bq_text
                    bq2_1 = ET.SubElement(card2, 'blockquote')
                    # If there is trailing whitespace in some_word we'll just keep it? Actually some_word could be just "наар"
                    bq2_1.text = f"{link_kw}{some_word} II."
                    
                    root.remove(card)
                    root.insert(idx, card2)
                    root.insert(idx, card1)

    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 identify_glued_cards.py <input> <output>")
        sys.exit(1)
    process_glued_cards(sys.argv[1], sys.argv[2])
