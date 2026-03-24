import re
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

from constants import linkKeyword

LOOK_BELOW_PLACEHOLDER = "__LOOK_BELOW__"
TOKEN_PATTERN = r'[^\s()<>]+'
ROMAN_PATTERN = r'[IVX]+'
generic_reference_pattern = re.compile(
    rf'(?P<prefix>{linkKeyword})'
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


def format_word_link(word, homonym=None, meaning=None):
    attrs = [f'word="{word}"']
    if homonym:
        attrs.append(f'homonym="{homonym}"')
    if meaning:
        attrs.append(f'meaning="{meaning}"')
    return f'<wordLink {" ".join(attrs)} />'


def parse_word_link(link_text):
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', link_text))
    if "word" not in attrs:
        return None
    return attrs


def render_word_link_from_attrs(attrs):
    return format_word_link(attrs["word"], attrs.get("homonym"), attrs.get("meaning"))


def replace_simple_reference(match):
    return (
        f'{match.group("prefix")}'
        f'{format_word_link(match.group("word"), match.group("homonym"), match.group("meaning"))}'
        f'{match.group("trailing") or ""}'
    )


def parse_reference_segment(segment):
    segment = re.sub(r"\s+", " ", segment.strip())
    if not segment:
        return None

    tokens = segment.split()
    meaning = None
    homonym = None

    if tokens and re.fullmatch(r'\d+', tokens[-1]):
        meaning = tokens.pop()
    if tokens and re.fullmatch(ROMAN_PATTERN, tokens[-1]):
        homonym = tokens.pop()

    if not 1 <= len(tokens) <= 3:
        return None

    word = " ".join(tokens).strip()
    if not word:
        return None

    return {"word": word, "homonym": homonym, "meaning": meaning}


def expand_reference_list(text):
    parts = [re.sub(r"\s+", " ", part.strip()) for part in text.split(",")]
    refs = []
    last_full_ref = None

    for part in parts:
        if not part:
            continue

        if re.fullmatch(ROMAN_PATTERN, part):
            if not last_full_ref:
                return None
            refs.append({
                "word": last_full_ref["word"],
                "homonym": part,
                "meaning": None,
            })
            continue

        if re.fullmatch(r'\d+', part):
            if not last_full_ref:
                return None
            refs.append({
                "word": last_full_ref["word"],
                "homonym": last_full_ref.get("homonym"),
                "meaning": part,
            })
            continue

        parsed = parse_reference_segment(part)
        if not parsed:
            return None

        refs.append(parsed)
        last_full_ref = parsed

    return refs or None


def render_reference_list(text):
    refs = expand_reference_list(text)
    if not refs:
        return None
    return ", ".join(
        format_word_link(ref["word"], ref.get("homonym"), ref.get("meaning"))
        for ref in refs
    )


def expand_tail_references(first_link_text, tail_text):
    first_attrs = parse_word_link(first_link_text)
    if not first_attrs:
        return None

    refs = [first_link_text.strip()]
    for part in [re.sub(r"\s+", " ", p.strip()) for p in tail_text.split(",")]:
        if not part:
            continue

        if re.fullmatch(r'\d+', part):
            cloned = dict(first_attrs)
            cloned["meaning"] = part
            refs.append(render_word_link_from_attrs(cloned))
            continue

        if re.fullmatch(ROMAN_PATTERN, part):
            cloned = dict(first_attrs)
            cloned["homonym"] = part
            cloned.pop("meaning", None)
            refs.append(render_word_link_from_attrs(cloned))
            continue

        parsed = parse_reference_segment(part)
        if not parsed:
            return None
        refs.append(format_word_link(parsed["word"], parsed.get("homonym"), parsed.get("meaning")))

    if len(refs) == 1:
        return None
    return ", ".join(refs)


def convert_plain_multi_refs(content):
    sr_pattern = re.compile(
        r'<blockquote>\s*\(\s*ср\.\s+'
        r'(?P<main>[^<()]+?)'
        r'\s*\)\s*(?P<punct>[.;])?\s*</blockquote>',
        flags=re.M,
    )

    def sr_replacer(match):
        main_rendered = render_reference_list(match.group("main"))
        if not main_rendered:
            return match.group(0)

        punct = match.group("punct") or ""
        return f'<xr>(ср. {main_rendered}){punct}</xr>'

    content = sr_pattern.sub(sr_replacer, content)

    pattern = re.compile(
        r'<blockquote>\s*(?P<prefix>'
        r'то же,\s*что|'
        r'см\.|'
        r'и\.\s*д\.\s*от|'
        r'деепр\.\s*от|'
        r'понуд\.\s*от|'
        r'взаимн\.\s*от|'
        r'страд\.\s*от|'
        r'возвр\.\s*от|'
        r'уподоб\.\s*от|'
        r'парное\s*к|'
        r'многокр\.\s*от|'
        r'отвл\.\s*от|'
        r'уменьш\.\s*от|'
        r'уменьш\.-ласк\.\s*от|'
        r'отриц\.\s*от|'
        r'противоп\.|'
        r'прил\.\s*от|'
        r'уменьш\.\s*к'
        r')\s+'
        r'(?P<main>[^<()]+?)'
        r'(?P<note>\s*\(\s*см\.\s*(?P<note_refs>[^<()]+?)\s*\))?'
        r'(?P<punct>[.;])?\s*</blockquote>',
        flags=re.M,
    )

    def replacer(match):
        main_rendered = render_reference_list(match.group("main"))
        if not main_rendered:
            return match.group(0)

        note = ""
        note_refs = match.group("note_refs")
        if note_refs is not None:
            note_rendered = render_reference_list(note_refs)
            if not note_rendered:
                return match.group(0)
            note = f' (см. {note_rendered})'

        punct = match.group("punct") or ""
        prefix = re.sub(r"\s+", " ", match.group("prefix").strip())
        return f'<xr>{prefix} {main_rendered}{note}{punct}</xr>'

    return pattern.sub(replacer, content)


def expand_existing_wordlink_lists(content):
    note_pattern = re.compile(
        r'\((?P<prefix>см\.|ср\.|прим\.\s*см\.|ещё\s+прим\.\s*см\.)\s*'
        r'(?P<first><wordLink[^>]*/>)'
        r'(?P<tail>(?:\s*,\s*[^<()]+)+)\)'
    )

    def note_replacer(match):
        expanded = expand_tail_references(match.group("first"), match.group("tail"))
        if not expanded:
            return match.group(0)
        prefix = re.sub(r"\s+", " ", match.group("prefix").strip())
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

        if tail_tokens:
            if re.fullmatch(r'\d+', tail_tokens[-1]):
                meaning = tail_tokens[-1]
                tail_tokens = tail_tokens[:-1]

        if tail_tokens:
            if re.fullmatch(r'[IVX]+', tail_tokens[-1]):
                homonym = tail_tokens[-1]
                tail_tokens = tail_tokens[:-1]

        if tail_tokens and meaning is None:
            if re.fullmatch(r'\d+', tail_tokens[-1]):
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

    updated_content = split_compound_pattern.sub(replacer, content)
    return updated_content, previews


with open(inputFilename, 'r', encoding='utf-8') as f:
    content = f.read()
    content = re.sub(r'\(см\.\s+ниже\)', f'({LOOK_BELOW_PLACEHOLDER})', content, flags=re.I)
    content = re.sub(r'см\.\s+ниже', LOOK_BELOW_PLACEHOLDER, content, flags=re.I)
    content = convert_plain_multi_refs(content)

    # detect links
    content_new = generic_reference_pattern.sub(replace_simple_reference, content)
    content_new = expand_existing_wordlink_lists(content_new)
    content_new, previews = merge_split_compound_links(content_new)
    content_new = re.sub(r'(<wordLink[^>]*/>)\(', r'\1 (', content_new)
    content_new = content_new.replace(f'({LOOK_BELOW_PLACEHOLDER})', '(см. ниже)')
    content_new = content_new.replace(LOOK_BELOW_PLACEHOLDER, 'см. ниже')

    # if previews:
    #     print(f"Merged split compound links: {len(previews)}")
    #     for before, after in previews:
    #         print(f"BEFORE: {before}")
    #         print(f"AFTER:  {after}")

    with open(outputFilename, "w", encoding="utf-8") as outputFile:
        outputFile.write(content_new)
