import re


TOKEN_PATTERN = r'[^\s()<>]+'
ROMAN_PATTERN = r'[IVX]+'


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
