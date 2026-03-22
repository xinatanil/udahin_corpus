import copy
import re
import sys
import xml.etree.ElementTree as ET


ROMAN_NUMERAL_RE = re.compile(r"^(.*)\s+((?:X|IX|IV|V?I{0,3}))([,.;:]*)$")


def parse_homonym_headword(text):
    if not text:
        return None
    match = ROMAN_NUMERAL_RE.match(text.strip())
    if not match:
        return None
    base, numeral, _ = match.groups()
    if not base:
        return None
    return base, numeral


def is_compiled_homonym_card(card):
    return card.find("k") is not None and card.find("homonym") is not None


def build_homonym_card(group):
    first_k = group[0].findtext("k", default="")
    parsed = parse_homonym_headword(first_k)
    base_word = parsed[0] if parsed else first_k.strip()

    merged_card = ET.Element("card")
    k_el = ET.SubElement(merged_card, "k")
    k_el.text = base_word

    for card in group:
        if is_compiled_homonym_card(card):
            for existing_homonym in card.findall("homonym"):
                merged_card.append(copy.deepcopy(existing_homonym))
            continue

        homonym_el = ET.SubElement(merged_card, "homonym")
        for child in list(card):
            if child.tag == "k":
                continue
            homonym_el.append(copy.deepcopy(child))

    return merged_card


def compile_homonyms(root):
    cards = list(root)
    grouped_cards = {}
    group_order = []

    for idx, card in enumerate(cards):
        k_text = card.findtext("k", default="")
        parsed = parse_homonym_headword(k_text)

        if not parsed and not is_compiled_homonym_card(card):
            continue

        if parsed:
            base_word, _ = parsed
        else:
            base_word = k_text.strip()
        if base_word not in grouped_cards:
            grouped_cards[base_word] = []
            group_order.append(base_word)
        grouped_cards[base_word].append((idx, card))

    new_children = []
    emitted_groups = set()

    for idx, card in enumerate(cards):
        k_text = card.findtext("k", default="")
        parsed = parse_homonym_headword(k_text)

        if not parsed and not is_compiled_homonym_card(card):
            new_children.append(copy.deepcopy(card))
            continue

        if parsed:
            base_word, _ = parsed
        else:
            base_word = k_text.strip()
        group = grouped_cards.get(base_word, [])

        if len(group) == 1:
            new_children.append(copy.deepcopy(card))
            continue

        first_idx = group[0][0]
        if idx != first_idx or base_word in emitted_groups:
            continue

        merged_cards = [group_card for _, group_card in group]
        new_children.append(build_homonym_card(merged_cards))
        emitted_groups.add(base_word)

    root[:] = new_children


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compile_homonyms.py <input.xml> <output.xml>")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    tree = ET.parse(input_filename)
    root = tree.getroot()
    compile_homonyms(root)
    tree.write(output_filename, encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    main()
