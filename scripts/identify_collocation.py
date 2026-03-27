from constants import metaWord, originWord
import sys
import xml.etree.ElementTree as ET
import re

metaOrOriginWord = f"(?:{metaWord}|{originWord})"
metaOrOriginPattern = re.compile(rf"^(?:{metaOrOriginWord}[ \t]*)+:$")
singleMetaOrOriginWithColonPattern = re.compile(rf"^({metaOrOriginWord}):$")
HARDCODED_COLLOCATION_BLOCKQUOTES = {
    ', ири:',
    '(неправ. ыпча):',
    '(неправ. вместо кун):',
    'усиление к словам, начинающимся на би:',
    '(только в одной погов.; ср. төөмантек):',
    '(только в сочет. с жети)',
    '(в сочет. с орой или арай):',
    '(чамек):',
    '(только в сочет. с той):',
    'в исх. п. и с притяж. аффиксом 3 л.:',
    'в выражениях сожаления, досады:',
    'в роли вспомогательного глагола:',
    'в соединении с айыл:',
    'в отриц. форме:',
    'в знач. утверждения при отриц. форме:',
    '(встречается только с киргизским аффиксом мн. ч.):',
    'преимущественно в отриц. оборотах:',
    '(только в деепр. прош. вр.):',
    '(вместо катыр, хатыр):',
    'с отриц. основного глагола:',
    '(вместо пороз):',
    '(встречено только в отриц. форме):',
	'только в отриц. форме или в отриц. обороте:',
    'только с отриц.:',
	'только в отриц. обороте:',
	'в ласк. обращениях:',
	'(или кам тагана, кам такана):',
    
}
NUMBER_ONLY_BLOCKQUOTE_PATTERN = re.compile(r'^\d+\.:?\s*$')

def insert_colloc_identifier(card, element, strip_colon=True):
    if strip_colon:
        # Remove ':' from the element's text
        element.text = element.text.strip()[:-1].rstrip()
    
    # Insert <collocationIdentifier>:</collocationIdentifier> after the element
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    current_idx = list(card).index(element)
    card.insert(current_idx + 1, colloc_id)

def get_keyword(card):
    """Get the keyword text from the card's <k> element."""
    k = card.find('k')
    if k is not None and k.text:
        return k.text.strip()
    return None


def insert_colloc_identifier_before(parent, element):
    colloc_id = ET.Element('collocationIdentifier')
    colloc_id.text = ':'
    current_idx = list(parent).index(element)
    parent.insert(current_idx, colloc_id)


def process_direct_coloned_meta_origin(parent):
    elements_processed = 0

    for child in list(parent):
        if child.tag != 'blockquote' or not child.text:
            continue

        text = child.text.strip()
        match = singleMetaOrOriginWithColonPattern.match(text)
        if not match:
            continue

        value = match.group(1)
        if re.fullmatch(originWord, value):
            child.tag = 'origin'
        else:
            child.tag = 'meta'
        child.text = value
        insert_colloc_identifier(parent, child, strip_colon=False)
        elements_processed += 1

    return elements_processed


def process_direct_hardcoded_collocations(parent):
    elements_processed = 0

    for child in list(parent):
        if child.tag != 'blockquote' or not child.text:
            continue

        text = child.text.strip()
        if text not in HARDCODED_COLLOCATION_BLOCKQUOTES:
            continue

        insert_colloc_identifier(parent, child)
        elements_processed += 1

    return elements_processed


def process_meanings(card):
    elements_processed = 0

    for meaning in card.findall('meaning'):
        blockquotes = meaning.findall('blockquote')
        if not blockquotes:
            continue

        for blockquote in blockquotes:
            if not blockquote.text:
                continue

            text = blockquote.text.strip()
            if NUMBER_ONLY_BLOCKQUOTE_PATTERN.match(text):
                continue

            if text.startswith(': '):
                blockquote.text = text[2:]
                insert_colloc_identifier_before(meaning, blockquote)
                elements_processed += 1
            elif metaOrOriginPattern.match(text):
                insert_colloc_identifier(meaning, blockquote)
                elements_processed += 1
            elif text in HARDCODED_COLLOCATION_BLOCKQUOTES:
                insert_colloc_identifier(meaning, blockquote)
                elements_processed += 1
            elif text.endswith(']:'):
                insert_colloc_identifier(meaning, blockquote)
                elements_processed += 1
            else:
                continue

            break

    return elements_processed


def process_card(card, children):
    elements_processed = 0
    
    for child in children:
        if child.text and ':' in child.text:
            text = child.text.strip()

            if child.tag == 'k' and text.endswith(':'):
                # <k> ending with ':' — strip colon, insert collocationIdentifier after <k>
                insert_colloc_identifier(card, child)
                elements_processed += 1
            elif child.tag == 'blockquote':
                if text.startswith(': '):
                    child.text = text[2:]
                    insert_colloc_identifier_before(card, child)
                    elements_processed += 1
                    continue

                # Remaining rules only apply to blockquotes immediately after <k>
                child_idx = children.index(child)
                if child_idx == 0 or children[child_idx - 1].tag != 'k':
                    continue

                keyword = get_keyword(card)
                if keyword and text.startswith(keyword + ': '):
                    # Strip "keyword: " from blockquote text
                    child.text = text[len(keyword) + 2:]
                    # Insert collocationIdentifier BEFORE the blockquote
                    colloc_id = ET.Element('collocationIdentifier')
                    colloc_id.text = ':'
                    current_idx = list(card).index(child)
                    card.insert(current_idx, colloc_id)
                    elements_processed += 1
                elif keyword and text.startswith(keyword) and text.endswith(':'):
                    insert_colloc_identifier(card, child)
                    elements_processed += 1
                elif metaOrOriginPattern.match(text):
                    insert_colloc_identifier(card, child)
                    elements_processed += 1
                elif text in HARDCODED_COLLOCATION_BLOCKQUOTES:
                    insert_colloc_identifier(card, child)
                    elements_processed += 1
                elif text.endswith(']:'):
                    insert_colloc_identifier(card, child)
                    elements_processed += 1

    return elements_processed


def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()

        total_count = 0
        
        for card in root.iter('card'):
            children = list(card)
            total_count += process_direct_coloned_meta_origin(card)
            total_count += process_direct_hardcoded_collocations(card)
            for homonym in card.findall('homonym'):
                total_count += process_direct_coloned_meta_origin(homonym)
                total_count += process_direct_hardcoded_collocations(homonym)
            total_count += process_card(card, children)
            total_count += process_meanings(card)

        # print(f"Total collocations processed: {total_count}")

        if hasattr(ET, 'indent'):
            ET.indent(tree, space="\t", level=0)
            
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
    except Exception as e:
        print(f"Error processing XML: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
    else:
        print("Usage: python3 identify_collocation.py <input.xml> <output.xml>")
        sys.exit(1)
        
    process_file(input_filename, output_filename)


# <trn>6.: урсун выражение заклятия;</trn>
# <trn>1.: шатыра-шатман весёлый, радостный;</trn>
# <trn>6.: бери карай с предшеств. исх. п. начиная от..., вот уже...как;</trn>
