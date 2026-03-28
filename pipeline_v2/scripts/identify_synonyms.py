
import sys
import xml.etree.ElementTree as ET

from rule_loader import load_rule_json

EXACT_SYNONYM_CASES = load_rule_json('synonym_exact_cases.json')

def transform_tree(tree):
    root = tree.getroot()
    count_synonyms = 0

    for card in root.findall('card'):
        # Get children list to access by index and preserve order
        children = list(card)
        
        # We look for <k> followed immediately by <blockquote>
        # Iterate up to second to last element
        for i in range(len(children) - 1):
            elem = children[i]
            next_elem = children[i+1]
            
            if elem.tag == 'k' and elem.text:
                k_text = elem.text.strip()
                if k_text.endswith(','):
                    # Check if next element is blockquote
                    if next_elem.tag == 'blockquote' and next_elem.text:
                        bq_text = next_elem.text.strip()
                        # Check if blockquote starts with k_text (including comma)
                        # We use .strip() on bq_text but check against k_text_stripped
                        # Example: k="алмас," bq="алмас, алмаз" -> startswith("алмас,") is True
                        if bq_text.startswith(k_text):
                            # Update <k>: Remove trailing comma
                            # We want to remove the comma from the original text, maybe preserve other whitespace?
                            # The user said: Remove the comma in <k>'s contents.
                            # k.text might be "алмас, " or " алмас, "
                            # Using rstrip(',') on the strip() version is safe?
                            # Let's just remove the last comma.
                            
                            # Find the last comma index
                            last_comma_index = elem.text.rfind(',')
                            if last_comma_index != -1:
                                # Remove comma at last_comma_index
                                elem.text = elem.text[:last_comma_index] + elem.text[last_comma_index+1:]
                            
                            # Rename <blockquote> to <synonym>
                            next_elem.tag = 'synonym'
                            count_synonyms += 1

            if elem.tag == 'blockquote' and elem.text:
                for rule in EXACT_SYNONYM_CASES:
                    if elem.text.strip() != rule['blockquote']:
                        continue

                    idx = list(card).index(elem)
                    card.remove(elem)

                    syn = ET.Element('synonym')
                    syn.text = rule['synonym']
                    card.insert(idx, syn)
                    break

    return count_synonyms


def process_synonyms(input_file, output_file):
    try:
        tree = ET.parse(input_file)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    transform_tree(tree)
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    # print(f"Identified {count_synonyms} synonyms.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python identify_synonyms.py <input> <output>")
        sys.exit(1)
        
    process_synonyms(sys.argv[1], sys.argv[2])
