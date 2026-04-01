
import sys
import re
from io import BytesIO
import xml.etree.ElementTree as ET
from constants import metaWord, originWord, linkKeyword
from rule_loader import load_rule_lines


def collapse_ws(text):
    return re.sub(r'\s+', ' ', text).strip()


def normalize_rule_entry(text):
    text = text.strip()
    if text.startswith('blockquote_xml:'):
        text = text.split(':', 1)[1].strip()
    return collapse_ws(text)


def normalize_element_xml(elem):
    return normalize_rule_entry(ET.tostring(elem, encoding='unicode'))


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
            'ал', 'мен', 'сен', 'бул', 'анда', 'эмес', 'анын', 'бар', 'кой',
			'кетип', 'калган', 'ошол', 'бир', 'эки', 'ак'
        }
        pattern = r'\b(' + '|'.join(self.standalone_forbidden_words) + r')\b'
        self.re_standalone_forbidden = re.compile(pattern, re.IGNORECASE)

        # 7. Words ending with hyphen (e.g. "алдырыл-", "ойно-")
        # Matches word characters followed by a hyphen at the end of the word boundary or string
        self.re_ends_with_hyphen = re.compile(r'\w+-(?!\w)')
        self.re_russian_tail_hint = re.compile(r'[цщъьёюяЦЩЪЬЁЮЯ]')
        kyr_word = r'[А-Яа-яЁёӨөҮүҢңӘә]+(?:-[А-Яа-яЁёӨөҮүҢңӘә]+)*'
        self.re_leading_hyphenated_collocation = re.compile(
            r'^(?P<left>'
            r'(?:'
            rf'(?:{kyr_word}(?:\s+{kyr_word}){{0,3}}\s+[А-Яа-яЁёӨөҮүҢңӘә]+-)'
            r'|'
            rf'(?:{kyr_word}-)'
            r')'
            r'(?:\s+или\s+'
            r'(?:'
            rf'(?:{kyr_word}(?:\s+{kyr_word}){{0,3}}\s+[А-Яа-яЁёӨөҮүҢңӘә]+-)'
            r'|'
            rf'(?:{kyr_word}-)'
            r'))*'
            r')\s+(?P<right>.+)$'
        )

        comparison_words = load_rule_lines('link_nonrefs_after_sr.txt')
        if comparison_words:
            self.re_comparison_only_note = re.compile(
                r'^\(\s*ср\.\s*(?:' + '|'.join(re.escape(word) for word in comparison_words) + r')\b.*\)\s*[:.;]?\s*$',
                re.IGNORECASE,
            )
        else:
            self.re_comparison_only_note = None

        self.forbidden_suffix_exceptions = frozenset(
            collapse_ws(line) for line in load_rule_lines('trn_forbidden_suffix_exceptions.txt')
        )

    def looks_like_kyrgyz_collocation_with_russian_tail(self, text):
        normalized = collapse_ws(text)
        if not normalized or normalized.startswith('('):
            return False

        match = self.re_leading_hyphenated_collocation.match(normalized)
        if not match:
            return False

        right = match.group('right').lstrip(' ,;:.')
        if not right:
            return False

        return bool(self.re_russian_tail_hint.search(right))

    def should_exclude_candidate(self, text, element, k_text):
        """
        Checks a specific text candidate against exclusion rules.
        Returns True if it matches an exclusion rule (skip it).
        """
        if not text:
            return True

        # Rule: Exclude if contains wordLink
        if element is not None and element.find('.//wordLink') is not None:
            return True

        # Rule: Exclude if Kyrgyz chars present
        if self.re_kyrgyz.search(text):
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

        # Rule: Exclude if contains word ending with forbidden suffixes,
        # unless this exact line is whitelisted as a known good translation.
        if (
            self.re_forbidden_suffixes.search(text)
            and collapse_ws(text) not in self.forbidden_suffix_exceptions
        ):
            return True

        # Rule: Exclude if contains words ending with hyphen
        # if self.re_ends_with_hyphen.search(text):
        #     return True

        # Rule: Exclude mixed "Kyrgyz collocation + Russian gloss" lines such as
        # "этибар кыл- обращать внимание;" so they can be handled later as
        # examples/collocations instead of becoming <trn>.
        if self.looks_like_kyrgyz_collocation_with_russian_tail(text):
            return True

        # Rule: Exclude standalone comparison-only notes like "(ср. монг. ...):"
        if self.re_comparison_only_note and self.re_comparison_only_note.match(text):
            return True

        return False


class TRNProcessor:
    """
    Manages the XML processing workflow.
    """
    def __init__(self, input_file=None, output_file=None):
        self.input_file = input_file
        self.output_file = output_file
        self.filter = TranslationFilter()
        self.count_trn_found = 0
        self.semantic_colon_rules = self.load_semantic_colon_rules()

    def load_semantic_colon_rules(self):
        rule_names = (
            'colon_altform_collocation.txt',
            'colon_meta_collocation.txt',
            'colon_xr_collocation.txt',
            'colon_collocation.txt',
        )
        rules = set()
        for name in rule_names:
            for line in load_rule_lines(name):
                rules.add(normalize_rule_entry(line))
        return frozenset(rules)

    def clean_k_word(self, text):
        if not text: return ""
        # Remove trailing punctuation like -, , etc. and homonym numbers I, II...
        return re.sub(r'[,\-:\s]+$', '', text).strip()

    def should_skip_by_meta_prefix(self, text):
        skip_prefixes = (
            'усиление к словам, начинающимся на',
            'подражательное слово'
        )
        return any(text.startswith(prefix) for prefix in skip_prefixes)

    def looks_like_long_example_line(self, text):
        normalized = re.sub(r'\s+', ' ', text).strip()
        if len(normalized.split()) < 4:
            return False

        strong_markers = ('фольк.', 'стих.', 'погов.')
        weak_markers = ('ист.', 'бран.', 'южн.')

        for marker in strong_markers + weak_markers:
            idx = normalized.find(marker)
            if idx == -1:
                continue

            prefix = normalized[:idx].strip()
            suffix = normalized[idx + len(marker):].strip()
            if len(prefix.split()) < 2 or len(suffix.split()) < 1:
                continue

            if marker in weak_markers:
                prev = normalized[:idx].rstrip()
                prev_char = prev[-1] if prev else ''
                if prev_char in '(;':
                    continue

            return True

        return False

    def should_skip_card(self, card):
        for meta in card.findall('.//meta'):
            meta_text = "".join(meta.itertext()).strip()
            if self.should_skip_by_meta_prefix(meta_text):
                return True
        for blockquote in card.findall('.//blockquote'):
            blockquote_text = "".join(blockquote.itertext()).strip()
            if self.should_skip_by_meta_prefix(blockquote_text):
                return True
        return False

    def apply_regex_preprocessing(self, content):
        """
        Applies loose regex replacement to fix simple cases before XML parsing.
        """
        #    <card>
        #        <k>радиола</k>
        #        <blockquote>радиола.</blockquote>
        #    </card>
        # or
        #    <card>
        #        <k>транспорт</k>
        #        <blockquote>транспорт;</blockquote>
        #        <blockquote>...</blockquote>
        #    </card>
        # converts first blockquote to <trn> when it matches the keyword
        return re.sub(r'(<card>\n\t\t<k>(.+)</k>\n\t\t)<blockquote>\2([.;])</blockquote>', 
                      r'\1<trn>\2\3</trn>', 
                      content, flags=re.M)

    def process_tree(self, tree):
        root = tree.getroot()
        self.preprocess_tree(tree)
        for card in root.findall('card'):
            self.process_card(card)

    def preprocess_tree(self, tree):
        root = tree.getroot()
        for card in root.findall('card'):
            children = list(card)
            if len(children) < 2:
                continue
            if children[0].tag != 'k' or children[1].tag != 'blockquote':
                continue

            k_elem = children[0]
            bq = children[1]
            if len(bq) > 0:
                continue

            k_text = k_elem.text or ''
            bq_text = bq.text or ''
            if bq_text not in {f'{k_text}.', f'{k_text};'}:
                continue

            bq.tag = 'trn'
            self.count_trn_found += 1

    def transform_content(self, content):
        content = self.apply_regex_preprocessing(content)
        root = ET.fromstring(content)
        tree = ET.ElementTree(root)
        self.process_tree(tree)

        buffer = BytesIO()
        tree.write(buffer, encoding='UTF-8', xml_declaration=True)
        return buffer.getvalue().decode('UTF-8')

    def process(self):
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            transformed = self.transform_content(content)
        except (ET.ParseError, IOError) as e:
            print(f"Error processing XML: {e}")
            return

        with open(self.output_file, 'w', encoding='utf-8') as output_file:
            output_file.write(transformed)

    def process_card(self, card):
        if self.should_skip_card(card):
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
        if element.find('collocationIdentifier') is not None:
            return

        # 3. Find FIRST NON-EMPTY direct blockquote in the element.
        target_bq = None
        target_text = ""

        seen_xr = False

        for child in list(element):
            if child.tag == 'trn':
                return
            if child.tag == 'xr':
                seen_xr = True
                continue
            if child.tag == 'miniCard' and seen_xr:
                return
            if child.tag != 'blockquote':
                continue

            t = "".join(child.itertext()).strip()
            if t:
                target_bq = child
                target_text = t
                break

        if target_bq is None:
            return

        # If a blockquote is already explicitly classified by the colon-review
        # workflow, let that later stage own it instead of turning it into <trn>.
        if normalize_element_xml(target_bq) in self.semantic_colon_rules:
            return
        plain_target_text = collapse_ws(''.join(target_bq.itertext()))
        if plain_target_text.endswith(':') and re.match(r'^\(?\s*(?:ср\.|см\.)', plain_target_text, re.IGNORECASE):
            return
        # Even with the broad wordLink exclusion disabled, a colon-final first
        # blockquote with inline links is still much more likely to be an xr /
        # collocation header than a translation.
        if target_text.endswith(':') and target_bq.find('.//wordLink') is not None:
            return

        if self.should_skip_by_meta_prefix(target_text):
            return
        if self.looks_like_long_example_line(target_text):
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
