import re

from rule_loader import load_rule_lines


_meta_words = load_rule_lines('meta_words.txt')
_meta_special_wb = load_rule_lines('meta_special_wb.txt')
_meta_special_no_wb = load_rule_lines('meta_special_no_wb.txt')
_origin_words = load_rule_lines('origin_words.txt')
_link_keywords = load_rule_lines('link_keywords.txt')
_link_special = load_rule_lines('link_special.txt')


def _escape(word):
    return re.escape(word)


_meta_wb_parts = [_escape(w) for w in _meta_words] + _meta_special_wb
_meta_outer_parts = []
if _meta_wb_parts:
    _meta_outer_parts.append(r'\b(?:' + '|'.join(_meta_wb_parts) + r')')
if _meta_special_no_wb:
    _meta_outer_parts.extend(_meta_special_no_wb)
metaWord = r'(?:' + '|'.join(_meta_outer_parts) + r')'

_origin_plain = [_escape(w) for w in _origin_words if not w.startswith('(')]
_origin_special_no_wb = [_escape(w) for w in _origin_words if w.startswith('(')]
_origin_parts = []
if _origin_plain:
    _origin_parts.append(r'\b(?:' + '|'.join(_origin_plain) + r')')
if _origin_special_no_wb:
    _origin_parts.extend(_origin_special_no_wb)
originWord = r'(?:' + '|'.join(_origin_parts) + r')'

_link_plain = [_escape(w) for w in _link_keywords]
_link_parts = []
if _link_plain:
    _link_parts.append(r'\b(?:' + '|'.join(_link_plain) + r')')
if _link_special:
    _link_parts.extend(_link_special)
linkKeyword = r'(?:' + '|'.join(_link_parts) + r')'
