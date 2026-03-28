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

    def extract_romans(text):
        match = re.search(r'\s+([IVX]+(?:\s*,\s*[IVX]+)*)(\.?)$', text.strip())
        if match:
            base = text[:match.start()]
            romans = [x.strip() for x in match.group(1).split(',')]
            dot = match.group(2)
            return base, romans, dot
        return text, [], ""

    link_pattern = re.compile(rf'^({constants.linkKeyword})(.*)$')
    
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
                
            base1, romans1, dot1 = extract_romans(bq1_text)
            base2, romans2, dot2 = extract_romans(bq2_text)
            
            if base1 == k_text and len(romans1) >= 2 and len(romans1) == len(romans2):
                match = link_pattern.match(base2)
                if match:
                    link_kw = match.group(1)
                    some_word = match.group(2)
                    
                    idx = list(root).index(card)
                    
                    root.remove(card)
                    
                    # Insert in reverse order to maintain original forward ordering
                    for i in reversed(range(len(romans1))):
                        r1 = romans1[i]
                        r2 = romans2[i]
                        
                        new_card = ET.Element('card')
                        k_new = ET.SubElement(new_card, 'k')
                        k_new.text = f"{k_text} {r1}"
                        
                        if optional_bq_text is not None:
                            opt_bq = ET.SubElement(new_card, 'blockquote')
                            opt_bq.text = optional_bq_text
                            
                        bq_new = ET.SubElement(new_card, 'blockquote')
                        bq_new.text = f"{link_kw}{some_word} {r2}{dot2}"
                        
                        root.insert(idx, new_card)

    tree.write(output_file, encoding='UTF-8', xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 identify_glued_cards.py <input> <output>")
        sys.exit(1)
    process_glued_cards(sys.argv[1], sys.argv[2])





# TODO: Where do examples go in this case? To both cards?
# <card>
#     <k>чектир-</k>
#     <blockquote>чектир- I, II</blockquote>
#     <blockquote>понуд. от чек- V, VI;</blockquote>
#     <blockquote>тамеки чектир- дать покурить или позволить покурить;</blockquote>
#     <blockquote>канаттууга кактырбай, тумшуктууга чектирбей не позволяя причинить малейшую неприятность; ограждая от малейшей обиды (напр. пестовать ребёнка, заботливо относиться к жене и т.п.);</blockquote>
#     <blockquote>машакат чектир- см. машакат;</blockquote>
#     <blockquote>убайым чектир- см. убайым I.</blockquote>
# </card>