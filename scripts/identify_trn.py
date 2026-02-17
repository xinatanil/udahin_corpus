
import sys
import re
import xml.etree.ElementTree as ET
from constants import metaWord, originWord, linkKeyword


class TranslationFilter:
    """
    Encapsulates all logic for determining if a block of text 
    should be EXCLUDED from being a translation.
    """
    def __init__(self):
        # 1. Kyrgyz specific chars
        self.re_kyrgyz = re.compile(r'[өүңәӨҮҢӘ]')
        
        # 2. Keywords/Metadata (converted to regex)
        full_pattern_str = f"{metaWord}|{originWord}|{linkKeyword}"
        self.re_metaOriginLinkKeywords = re.compile(full_pattern_str, re.IGNORECASE)

        # 3. Roman numerals
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
        self.re_roman = re.compile(r'\b(' + '|'.join(roman_numerals) + r')\b')
        
        # 4. Global card content check
        self.re_global_forbidden = re.compile(r'1\)|2\)|3\)|4\)|5\)|:')

        # 5. Ending with forbidden suffixes
        # Suffixes: деп, тти, лды, рды, нды
        self.re_forbidden_suffixes = re.compile(r'(деп|тти|лды|рды|нды|дын|дун|нын|уу)\b', re.IGNORECASE)

        # 6. Standalone forbidden words (must be whole words)
        self.standalone_forbidden_words = {
            'азыр', 'экен', 'болгон', 'жаткан', 'керек', 'жок', 'бардык', 
            'ушул', 'кайсы', 'эмне', 'качан', 'кайдан', 'биз', 'силер', 
            'алар', 'мага', 'сага', 'аны', 'аныки', 'менен', 
            'тууралуу', 'боюнча', 'сайын', 'аркылуу', 'сыяктуу', 'бекен', 
            'беле', 'тура', 'деп', 'дейт', 'эл', 'абал', 'акыл', 'айдар',
            'бала', 'киши', 'адам', 'жер', 'суу', 'тоо', 'кол',
            'бут', 'баш', 'көз', 'ооз', 'мурун', 'чач', 'тырмак',
            'ал', 'мен', 'сен', 'бул', 'анда', 'эмес', 'анын'
        }
        pattern = r'\b(' + '|'.join(self.standalone_forbidden_words) + r')\b'
        self.re_standalone_forbidden = re.compile(pattern, re.IGNORECASE)

        # 7. Words ending with hyphen (e.g. "алдырыл-", "ойно-")
        # Matches word characters followed by a hyphen at the end of the word boundary or string
        self.re_ends_with_hyphen = re.compile(r'\w+-(?!\w)')

    def is_card_globally_forbidden(self, card_text_full):
        """Checks if the entire card content violates a rule."""
        if self.re_global_forbidden.search(card_text_full):
            return True
        return False

    def should_exclude_candidate(self, text, element, k_text):
        """
        Checks a specific text candidate against exclusion rules.
        Returns True if it matches an exclusion rule (skip it).
        """
        if not text:
            return True

        # Rule: Exclude if Kyrgyz chars present
        if self.re_kyrgyz.search(text):
            return True
            
        # Rule: Exclude if contains specific keywords
        if self.re_metaOriginLinkKeywords.search(text):
            return True

		# Rule: Exclude Roman numerals
        if self.re_roman.search(text):
            return True

		# Rule: Exclude if starts with "(или"
        if text.startswith("(или"):
            return True

        # Rule: Exclude if entirely in parentheses
        if text.startswith("(") and text.endswith(")"):
            return True
            
        # Rule: Exclude if contains the headword (k_text)
        # e.g. k="абайы", text="абайы, абай" -> skip
        if k_text and k_text in text.lower():
            return True

        # Rule: Exclude if contains standalone forbidden word "жок"
        if self.re_standalone_forbidden.search(text):
            return True

        # Rule: Exclude if contains forbidden substrings
        for forbidden in ["жагы", "болуп", "келди", "кетти", "барды", "калды", "ээ", "дагы"]:
            if forbidden in text:
                return True

        # Rule: Exclude if contains word ending with forbidden suffixes
        if self.re_forbidden_suffixes.search(text):
            return True

        # Rule: Exclude if contains words ending with hyphen
        if self.re_ends_with_hyphen.search(text):
            return True

        return False


class TRNProcessor:
    """
    Manages the XML processing workflow.
    """
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.filter = TranslationFilter()
        self.count_trn_found = 0

    def clean_k_word(self, text):
        if not text: return ""
        # Remove trailing punctuation like -, , etc. and homonym numbers I, II...
        return re.sub(r'[,\-:\s]+$', '', text).strip()

    def apply_regex_preprocessing(self, content):
        """
        Applies loose regex replacement to fix simple cases before XML parsing.
        """
        #    <card>
        #        <k>радиола</k>
        #        <blockquote>радиола.</blockquote>
        #    </card>
        # to
        #    <card>
        #        <k>радиола</k>
        #        <trn>радиола</trn>
        #    </card>
        return re.sub(r'<card>\n\t\t<k>(.+)</k>\n\t\t<blockquote>\1\.</blockquote>', 
                      r'<card>\n\t\t<k>\1</k>\n\t\t<trn>\1.</trn>', 
                      content, flags=re.M)

    def process(self):
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            content = self.apply_regex_preprocessing(content)

            root = ET.fromstring(content)
            tree = ET.ElementTree(root)
        except (ET.ParseError, IOError) as e:
            print(f"Error processing XML: {e}")
            return

        for card in root.findall('card'):
            self.process_card(card)

        tree.write(self.output_file, encoding='UTF-8', xml_declaration=True)
        print(f"Tagged {self.count_trn_found} new translations.")

    def process_card(self, card):
        # 1. Get all text in the card to check global forbidden
        card_text_full = "".join(card.itertext())
        if self.filter.is_card_globally_forbidden(card_text_full):
            return

        # 2. Prepare k_text for checking
        k_elem = card.find('k')
        k_text = ""
        if k_elem is not None and k_elem.text:
             k_text = self.clean_k_word(k_elem.text).lower()

        # 1.5 Handle <meaning> tags if present
        meanings = card.findall('meaning')
        if meanings:
            for meaning in meanings:
                self.check_and_mark_trn(meaning, k_text)
            return

        # No meaning tags, check the card itself
        self.check_and_mark_trn(card, k_text)

    def check_and_mark_trn(self, element, k_text):
        """
        Checks a candidate element (card or meaning) for a valid blockquote 
        and marks it as a translation if valid.
        """
        # 3. Find FIRST NON-EMPTY blockquote in the element
        blockquotes = element.findall('blockquote')
        target_bq = None
        target_text = ""
        
        for bq in blockquotes:
            # Skip if contains wordLink
            if bq.find('.//wordLink') is not None:
                continue
                
            t = "".join(bq.itertext()).strip()
            if t:
                target_bq = bq
                target_text = t
                break
        
        if target_bq is None:
            return
            
        # 4. Check against all exclusion rules
        if self.filter.should_exclude_candidate(target_text, target_bq, k_text):
            return

        # 5. If passed all, mark as trn
        target_bq.tag = 'trn'
        self.count_trn_found += 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python identify_trn.py <input> <output>")
        sys.exit(1)
        
    processor = TRNProcessor(sys.argv[1], sys.argv[2])
    processor.process()
