import re
import sys
from pathlib import Path

from constants import linkKeyword
from rule_loader import load_rule_lines
from reference_utils import (
    TOKEN_PATTERN,
    ROMAN_PATTERN,
    format_word_link,
    expand_tail_references,
    parse_word_link,
    render_word_link_from_attrs,
)


LOOK_BELOW_PLACEHOLDER = "__LOOK_BELOW__"
SR_COMPARISON_PLACEHOLDER = "__SR_COMPARISON__"
SR_NONREF_WORDS = load_rule_lines('link_nonrefs_after_sr.txt')
if SR_NONREF_WORDS:
    sr_nonref_pattern = re.compile(
        r'(?P<prefix>\bср\.\s*)(?P<lemma>' + '|'.join(re.escape(w) for w in SR_NONREF_WORDS) + r')\b',
        flags=re.I,
    )
else:
    sr_nonref_pattern = None

generic_reference_pattern = re.compile(
    rf'(?P<prefix>{linkKeyword})'
    r'(?P<ws>\s*)'
    r'(?P<word>\w+-?)'
    rf'(?:\s+(?P<homonym>{ROMAN_PATTERN}))?'
    r'(?:\s+(?P<meaning>\d+))?'
    r'(?P<trailing>[,.;])?',
    flags=re.M,
)

split_compound_pattern = re.compile(
    r'<wordLink(?P<before>[^>]*)\bword="(?P<word>[^"]+)"(?P<after>[^>]*)\s*/>'
    r'(?P<trailing>\s*(?:' + TOKEN_PATTERN + r'(?:\s+' + TOKEN_PATTERN + r'){0,2}))'
    r'(?P<suffix>\s*\(\s*(?:см\.\s*<wordLink[^>]*/>|' + LOOK_BELOW_PLACEHOLDER + r')\s*\))'
)

split_compound_multi_ref_pattern = re.compile(
    r'<wordLink(?P<before>[^>]*)\bword="(?P<word>[^"]+)"(?P<after>[^>]*)\s*/>'
    r'(?P<trailing>\s*(?:' + TOKEN_PATTERN + r'(?:\s+' + TOKEN_PATTERN + r'){0,2}))'
    r'(?P<suffix>\s*\(\s*(?:см\.|ср\.)\s*<wordLink[^>]*/>(?:\s*,\s*<wordLink[^>]*/>)*\s*\))'
)

attached_suffix_pattern = re.compile(
    r'(?P<link><wordLink[^>]*/>)'
    r'(?P<space>\s*)'
    r'(?:(?P<roman>' + ROMAN_PATTERN + r')(?:(?:\s+)(?P<meaning_after_roman>\d+))?|(?P<meaning_only>\d+))'
    r'(?=[,.;:)])'
)


def protect_look_below(content):
    content = re.sub(r'\(см\.\s+ниже\)', f'({LOOK_BELOW_PLACEHOLDER})', content, flags=re.I)
    content = re.sub(r'см\.\s+ниже', LOOK_BELOW_PLACEHOLDER, content, flags=re.I)
    return content


def restore_look_below(content):
    content = content.replace(f'({LOOK_BELOW_PLACEHOLDER})', '(см. ниже)')
    content = content.replace(LOOK_BELOW_PLACEHOLDER, 'см. ниже')
    return content


def protect_sr_nonrefs(content):
    if not sr_nonref_pattern:
        return content
    return sr_nonref_pattern.sub(
        lambda m: f'{SR_COMPARISON_PLACEHOLDER}{m.group("lemma")}',
        content,
    )


def restore_sr_nonrefs(content):
    return content.replace(SR_COMPARISON_PLACEHOLDER, 'ср. ')


def replace_simple_reference(match):
    return (
        f'{match.group("prefix")}'
        f'{match.group("ws")}'
        f'{format_word_link(match.group("word"), match.group("homonym"), match.group("meaning"))}'
        f'{match.group("trailing") or ""}'
    )


def expand_existing_wordlink_lists(content):
    note_pattern = re.compile(
        r'\((?P<lead>[^()<>]*?;\s*)?(?P<prefix>см\.|ср\.|прим\.\s*см\.|ещё\s+прим\.\s*см\.)\s*'
        r'(?P<first><wordLink[^>]*/>)'
        r'(?P<tail>(?:\s*,\s*[^<()]+)+)\)'
    )

    def note_replacer(match):
        if match.group("lead") and '.' in match.group("tail"):
            return match.group(0)
        expanded = expand_tail_references(match.group("first"), match.group("tail"))
        if not expanded:
            return match.group(0)
        lead = re.sub(r"\s+", " ", (match.group("lead") or "")).strip()
        prefix = re.sub(r"\s+", " ", match.group("prefix").strip())
        if lead:
            return f'({lead} {prefix} {expanded})'
        return f'({prefix} {expanded})'

    content = note_pattern.sub(note_replacer, content)

    repeated_index_pattern = re.compile(
        r'(?P<first><wordLink[^>]*/>)'
        r'(?P<tail>(?:\s*,\s*(?:' + ROMAN_PATTERN + r'|\d+))+)' 
        r'(?P<after>\s*(?=\(|[.;,]))'
    )

    def repeated_index_replacer(match):
        expanded = expand_tail_references(match.group("first"), match.group("tail"))
        if not expanded:
            return match.group(0)
        return f'{expanded}{match.group("after")}'

    return repeated_index_pattern.sub(repeated_index_replacer, content)


def attach_suffix_indices_to_wordlinks(content):
    def replacer(match):
        attrs = parse_word_link(match.group("link"))
        if not attrs:
            return match.group(0)

        roman = match.group("roman")
        meaning = match.group("meaning_after_roman") or match.group("meaning_only")
        changed = False

        if roman:
            if attrs.get("homonym"):
                return match.group(0)
            attrs["homonym"] = roman
            changed = True

        if meaning and not attrs.get("meaning"):
            attrs["meaning"] = meaning
            changed = True

        if not changed:
            return match.group(0)

        return render_word_link_from_attrs(attrs)

    return attached_suffix_pattern.sub(replacer, content)


def merge_split_compound_links(content):
    previews = []

    def replacer(match):
        original = match.group(0)
        base_word = match.group("word").strip()
        trailing = re.sub(r"\s+", " ", match.group("trailing")).strip()
        if not trailing:
            return original

        tokens = trailing.split()
        tail_tokens = tokens[:]
        meaning = None
        homonym = None

        if tail_tokens and re.fullmatch(r'\d+', tail_tokens[-1]):
            meaning = tail_tokens[-1]
            tail_tokens = tail_tokens[:-1]

        if tail_tokens and re.fullmatch(r'[IVX]+', tail_tokens[-1]):
            homonym = tail_tokens[-1]
            tail_tokens = tail_tokens[:-1]

        if tail_tokens and meaning is None and re.fullmatch(r'\d+', tail_tokens[-1]):
            meaning = tail_tokens[-1]
            tail_tokens = tail_tokens[:-1]

        tail = " ".join(tail_tokens).strip()
        if not tail:
            return original

        joiner = "" if base_word.endswith("-") else " "
        merged_word = f"{base_word}{joiner}{tail}"
        after = match.group("after")
        if meaning and 'meaning="' not in after:
            after = f'{after} meaning="{meaning}"'
        if homonym and 'homonym="' not in after:
            after = f'{after} homonym="{homonym}"'
        updated = (
            f'<wordLink{match.group("before")}word="{merged_word}"'
            f'{after} />'
        )
        full_updated = updated + match.group("suffix")
        previews.append((original, full_updated))
        return full_updated

    updated_content = content
    for pattern in (
        split_compound_pattern,
        split_compound_multi_ref_pattern,
    ):
        updated_content = pattern.sub(replacer, updated_content)
    return updated_content, previews


def transform_content(content, return_previews=False):
    content = protect_look_below(content)
    content = protect_sr_nonrefs(content)
    content_new = generic_reference_pattern.sub(replace_simple_reference, content)
    content_new = expand_existing_wordlink_lists(content_new)
    content_new = attach_suffix_indices_to_wordlinks(content_new)
    content_new, previews = merge_split_compound_links(content_new)
    content_new = re.sub(r'(<wordLink[^>]*/>)\(', r'\1 (', content_new)
    content_new = restore_sr_nonrefs(content_new)
    content_new = restore_look_below(content_new)

    if return_previews:
        return content_new, previews
    return content_new


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python3 identify_links.py <input.xml> <output.xml>")
        return 1

    input_filename = Path(sys.argv[1])
    output_filename = Path(sys.argv[2])

    content = input_filename.read_text(encoding='utf-8')
    content_new = transform_content(content)
    output_filename.write_text(content_new, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
