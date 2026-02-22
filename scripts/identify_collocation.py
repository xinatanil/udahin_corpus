import sys
import xml.etree.ElementTree as ET
import re
from constants import metaWord, originWord

metaOrOriginWord = f"(?:{metaWord}|{originWord})"
pattern = re.compile(rf"^(?:{metaOrOriginWord}[ \t]*)+:$")

def is_special_blockquote(text):
    text_stripped = text.strip()
    return (
        text_stripped.endswith(']:') or
        (text_stripped.startswith('усиление к словам, начинающимся на ') and text_stripped.endswith(':')) or
        text_stripped == 'подражательное слово:' or
		text_stripped == 'бирин (бир-ин):' or
		text_stripped == 'в отриц. форме:' or
		text_stripped == '(в эпосе, когда речь ведётся от лица монгола или калмыка; ср. жабуу III):' or
		text_stripped == '(встречено только в отриц. форме):' or
		text_stripped == 'в выражениях сожаления, досады:' or
		text_stripped == '(только в деепр. прош. вр.):' or
		text_stripped == '(от г. Ирбит, Ирбитская ярмарка):' or
		text_stripped == 'только с отриц.:' or
		text_stripped == '(неправ. вместо кун):'
    )

def insert_colloc_identifier(card, element):
    # Remove ':' from the element's text
    element.text = element.text.strip()[:-1].rstrip()
    
    # Insert <collocationIdentifier>:</collocationIdentifier> after the element
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    current_idx = list(card).index(element)
    card.insert(current_idx + 1, colloc_id)

def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()

        elements_processed = 0
        for card in root.iter('card'):
            children = list(card)
            for i, child in enumerate(children):
                if child.tag == 'k':
                    if child.text and child.text.strip().endswith(':'):
                        insert_colloc_identifier(card, child)
                        elements_processed += 1
                    elif i + 1 < len(children):
                        next_child = children[i + 1]
                        if next_child.tag == 'blockquote' and next_child.text:
                            text_stripped = next_child.text.strip()
                            if pattern.match(text_stripped):
                                insert_colloc_identifier(card, next_child)
                                elements_processed += 1
                elif child.tag == 'blockquote' and child.text and is_special_blockquote(child.text):
                    insert_colloc_identifier(card, child)
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