import sys
import re
from bs4 import BeautifulSoup
from constants import metaWord

metaWord_pattern = re.compile(metaWord)

def clean_k_text(k_text):
    if not k_text:
        return ""
    # Strip Roman numerals (I, II, III, etc.) at the end of the string
    cleaned = re.sub(r'\s+[IVXLCDM]+\s*$', '', k_text)
    # Strip hyphens
    cleaned = cleaned.replace('-', '')
    return cleaned.strip()

def identify_examples(k_elem, card_or_meaning, soup):
    k_text = k_elem.get_text() if k_elem else ""
    k_cleaned = clean_k_text(k_text)
    
    if not k_cleaned:
        return

    # Find the index of the first <trn>
    trns = card_or_meaning.find_all('trn', recursive=False)
    if not trns:
        return
        
    first_trn = trns[0]
    
    # Process subsequent siblings of the first <trn>
    elements_to_process = []
    current_sibling = first_trn.find_next_sibling()
    while current_sibling:
        elements_to_process.append(current_sibling)
        current_sibling = current_sibling.find_next_sibling()
        
    for element in elements_to_process:
        if element.name == 'blockquote':
            text = element.get_text()
            
            if k_cleaned in text:
                matches = list(metaWord_pattern.finditer(text))
                
                if len(matches) == 1:
                    match = matches[0]
                    before_meta = text[:match.start()]
                    after_meta = text[match.end():]
                    
                    if before_meta.strip() and after_meta.strip():
                        inner_html = element.decode_contents()
                        html_matches = list(metaWord_pattern.finditer(inner_html))
                        
                        if len(html_matches) == 1:
                            html_match = html_matches[0]
                            part1_html = inner_html[:html_match.start()].strip()
                            part2_html = inner_html[html_match.start():].strip()
                            
                            ex_elem = soup.new_tag('ex')
                            
                            try:
                                source_soup = BeautifulSoup(f'<source>{part1_html}</source>', 'xml')
                                target_soup = BeautifulSoup(f'<target>{part2_html}</target>', 'xml')
                                
                                if source_soup.source and target_soup.target:
                                    ex_elem.append(source_soup.source)
                                    ex_elem.append(target_soup.target)
                                    element.replace_with(ex_elem)
                            except Exception as e:
                                print(f"Error parsing fragments for {k_text}: {e}", file=sys.stderr)

def process_file(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'xml')

        for card in soup.find_all('card'):
            k_elem = card.find('k')
            
            meanings = card.find_all('meaning', recursive=False)
            if meanings:
                for meaning in meanings:
                    identify_examples(k_elem, meaning, soup)
            else:
                identify_examples(k_elem, card, soup)
                
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
    except Exception as e:
        print(f"Error processing XML: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
        process_file(input_filename, output_filename)
    else:
        print("Usage: python3 identify_examples.py <input.xml> <output.xml>")
        sys.exit(1)