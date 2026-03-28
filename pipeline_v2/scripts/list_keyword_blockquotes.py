import sys
import xml.etree.ElementTree as ET


def get_inner_xml(element):
    parts = [element.text or ""]
    for child in element:
        parts.append(ET.tostring(child, encoding="unicode"))
    return "".join(parts)


def get_first_direct_blockquote(element):
    for child in list(element):
        if child.tag == 'blockquote':
            return child
    return None


def build_entry(card_k, blockquote, homonym_index=None, meaning_index=None):
    lines = [f'<k>{card_k}</k>']
    if homonym_index:
        lines.append(f'<homonymIndex>{homonym_index}</homonymIndex>')
    if meaning_index:
        lines.append(f'<meaningIndex>{meaning_index}</meaningIndex>')
    lines.append(f'<blockquote>{get_inner_xml(blockquote)}</blockquote>')
    return "\n".join(lines) + "\n"


def maybe_collect(entries, card_k, scope, exclude_colon, homonym_index=None, meaning_index=None):
    blockquote = get_first_direct_blockquote(scope)
    if blockquote is None or blockquote.find('wordLink') is None:
        return

    blockquote_content = get_inner_xml(blockquote)
    if not blockquote_content.strip():
        return
    if exclude_colon and ':' in blockquote_content:
        return

    entries.append(build_entry(card_k, blockquote, homonym_index=homonym_index, meaning_index=meaning_index))


def list_keyword_blockquotes(input_file, output_file, exclude_colon=True):
    tree = ET.parse(input_file)
    root = tree.getroot()

    with_wordlink = []

    for card in root.iter('card'):
        card_k = card.findtext('k', default='')
        maybe_collect(with_wordlink, card_k, card, exclude_colon)

        for meaning in card.findall('meaning'):
            maybe_collect(
                with_wordlink,
                card_k,
                meaning,
                exclude_colon,
                meaning_index=meaning.findtext('meaningIndex', default='').strip() or None,
            )

        for homonym in card.findall('homonym'):
            homonym_index = homonym.findtext('homonymIndex', default='').strip() or None
            maybe_collect(
                with_wordlink,
                card_k,
                homonym,
                exclude_colon,
                homonym_index=homonym_index,
            )

            for meaning in homonym.findall('meaning'):
                maybe_collect(
                    with_wordlink,
                    card_k,
                    meaning,
                    exclude_colon,
                    homonym_index=homonym_index,
                    meaning_index=meaning.findtext('meaningIndex', default='').strip() or None,
                )

    with open(output_file, 'w', encoding='utf-8') as f:
        for e in with_wordlink:
            f.write(e + '\n')

    print(f'With wordLink: {len(with_wordlink)}')
    print(f'Wrote to {output_file}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 list_keyword_blockquotes.py <input.xml> <output.txt> [--with-colon]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    exclude_colon = '--with-colon' not in sys.argv

    list_keyword_blockquotes(input_file, output_file, exclude_colon=exclude_colon)
