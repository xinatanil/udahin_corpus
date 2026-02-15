
import sys
import re
import xml.etree.ElementTree as ET


def clean_k_word(text):
    if not text: return ""
    # Remove trailing punctuation like -, , etc. and homonym numbers I, II...
    # The user example showed "а I", "а II". We probably want just "а".
    # But clean_k_word in previous version was: re.sub(r'[,\-:\s]+$', '', text).strip()
    # "а I" -> "а I".
    # If blockquote is "а I", it matches.
    # Let's clean commonly attached homonym markers if they are at the end?
    # User's example: <k>абайы,</k> -> clean "абайы" -> <trn>абайы, абай</trn> (contains "абайы").
    return re.sub(r'[,\-:\s]+$', '', text).strip()

def process_trn(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        #    <card>
        #        <k>радиола</k>
        #        <blockquote>радиола.</blockquote>
        #    </card>
        # to
        #    <card>
        #        <k>радиола</k>
        #        <trn>радиола</trn>
        #    </card>
        content = re.sub(r'<card>\n\t\t<k>(.+)</k>\n\t\t<blockquote>\1\.</blockquote>', r'<card>\n\t\t<k>\1</k>\n\t\t<trn>\1.</trn>', content, flags=re.M)

        root = ET.fromstring(content)
        tree = ET.ElementTree(root)
    except (ET.ParseError, IOError) as e:
        print(f"Error processing XML: {e}")
        return

    count_trn_found = 0
    
    # Regex patterns for exclusions
    # 1. Kyrgyz specific chars
    re_kyrgyz = re.compile(r'[өүңәӨҮҢӘ]')
    
    # 2. Meta/Origin/Link words
    meta_words = r'разг\.|уст\.|лингв\.|перен\.|полит\.|спорт\.|полигр\.|с\.-х\.|рел\.|воен\.|дип\.|горн\.|пед\.|этн\.|лит\.|театр\.|филос\.|миф\.|геол\.|хим\.|мед\.|тех\.|ист\.|мат\.|бот\.|сев\.|южн\.|чатк\.|чуйск\.|тяньш\.|талас\.|памир\.|синьцз\.|редко|прям\., перен\.|бран\.|карт\.|женск\.|охот\.|муз\.|иссык-кульск\.|анат\.|грам\.|ирон\.|инд\.|геогр\.|ласк\.|эвф\.|груб\.|шутл\.|юр\.|только в исх\. п\.'
    origin_words = r'кит\.|р\.|ар\.|тиб\.|ир\.|ар\.-ир\.|р\.-ир\.|ир\.-кирг\.|ир\.-ар\.|кирг\.-ир\.'
    link_keywords = r'и\. д\. от|понуд\. от|взаимн\. от|страд\. от|возвр\.- ?страд\. от|возвр\. от|уподоб\. от|парное к|многокр\. от|отвл\. от|уменьш\. от|уменьш\.-ласк\. от|деепр\. от|\(ср\.|то же, что|см\.|отриц\. от|неправ\. вместо'
    
    # Combined pattern
    full_pattern_str = f"{meta_words}|{origin_words}|{link_keywords}"
    re_keywords = re.compile(full_pattern_str, re.IGNORECASE)

    # 3. Roman numerals
    roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
    re_roman = re.compile(r'\b(' + '|'.join(roman_numerals) + r')\b')
    
    # 4. Global card content check
    re_global_forbidden = re.compile(r'1\)|2\)|3\)|4\)|5\)|:')


    for card in root.findall('card'):
        # Get all text in the card to check global forbidden
        card_text_full = "".join(card.itertext())
        
        if re_global_forbidden.search(card_text_full):
            continue

        # Prepare k_text for checking
        k_elem = card.find('k')
        k_text = ""
        if k_elem is not None and k_elem.text:
             k_text = clean_k_word(k_elem.text).lower()

        # Find FIRST NON-EMPTY blockquote
        blockquotes = card.findall('blockquote')
        target_bq = None
        target_text = ""
        
        for bq in blockquotes:
            t = "".join(bq.itertext()).strip()
            if t:
                target_bq = bq
                target_text = t
                break
        
        if target_bq is None:
            continue
            
        # exclude if Kyrgyz chars
        if re_kyrgyz.search(target_text):
            continue
            
        # exclude if keywords
        if re_keywords.search(target_text):
            continue
            
        # exclude Roman numerals
        if re_roman.search(target_text):
            continue
            
        # exclude if starts with "(или"
        if target_text.startswith("(или"):
            continue

        # exclude if entirely in parentheses
        if target_text.startswith("(") and target_text.endswith(")"):
            continue
            
        # exclude if contains k_text
        # e.g. k="абайы", text="абайы, абай" -> skip
        if k_text and k_text in target_text.lower():
            continue

        # If passed all, mark as trn
        target_bq.tag = 'trn'
        count_trn_found += 1


    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"Tagged {count_trn_found} new translations.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python identify_trn.py <input> <output>")
        sys.exit(1)
        
    process_trn(sys.argv[1], sys.argv[2])
