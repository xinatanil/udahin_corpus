import re
import fileinput
import sys
import xml.etree.ElementTree as ET

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

from constants import metaWord, originWord, linkKeyword

metaOrOriginWord = metaWord + '|' + originWord
manual_exceptions = [
    '(в говорах)',
    '(о человеке с большими глазами и большими белками)',
    '(встречено только в одной поговорке; ср. то же слово у алтайцев, тувинцев и др.)',
    '(воспринимается не как глагол, а как имя)',
    '(без притяж. аффикса теряет конечный т; основой для киргизского языка, видимо, будет не аст, а асты; ср. үст)',
    '(фонетически и орфографически часто смешивается со словом бар I, когда последнее оформлено притяж. аффиксами)',
    '(о женщинах, преимущетвенно старых)',
    '(только в сочетании с числительным бир)',
    '(принимает аффикс мн. ч.)',
    '(практика даёт производные только от основы промысло)',
    '(видимо, искусственно образовано по типу көйкап)',
    '(вероятно, ошибочно вместо көкөмсү-)',
    '(обычно в сочет. с абышка или чал или кары)',
    '(наст.-буд. вр. кууйт и кубат, прич. куур и кубар)',
    '(произносится в нос)',
    '(эта форма встречается в местах близкого соседства киргизов с казахами, а также в эпосе и в некоторых южных говорах)',
    '(о девушке, молодухе)',
    '(о жеребятах)',
    '(в ряде случаев трудно разграничить шор I и шор II)',
    '(гл. обр. в фольклоре)',
    '(о коне)',
    '(ф гортанно-губной, произносится с призвуком ш);',
    '(о человеке)',
    '(и с притяж. аффиксом 3 л. бирөөсү, а иногда бирөбү один из них)',
    '(употребление ограничено)',
    '(обычно носовое)',
    '(в старом эпистолярном стиле)',
    '(в некоторых местах)',
    '(йэм после гласных, эм после согласных)',
    '(вместо жергелете)',
    '(с притяж. аффиксом 3 л. журдусу и журду)',
    '(о старых людях)',
    '(к мягкое)',
    '(обычно смешивается с канкор I, см.)',
    '(прич. прош. вр. карыган и карган)',
    '(о глазах)',
    '(при личных притяж. аффиксах ы часто выпадает)',
    '(видимо, вместо үлпөт)',
	'(о женщине)',
    '(о языке, губах)',
    '(глагол, выражающий движение наружу или вверх)',
    '(с мягким л)',
	'частица',
	'(тат. ласк. форма от дос)',
	'(значение даётся приблизительно; ср. өлкөн, өөркүн)',
    'послелог',
    'межд., выражающее недовольство, порицание, приятное удивление;',
    'межд., выражающее внезапное ощущение боли;',
    'межд., выражающее удивление;',
    'межд., выражающее удивление',
	'вопросительное и относительное местоимение, редко употребляемое самостоятельно;',
    'звукоподражание звону (напр. от удара по пустой металлической посуде; ср. каңк);',
    '(в изолированном виде как повеление, часто ке-)',
    '(о человеке невысокого роста, полненьком, сбитом и высоко держащем голову)',
    '(орфографически следует көзөл)',
    '(в лит. яз. считается неприличным, но в фольклоре и в быту употребляется очень часто)',
    '(только в одной погов.; ср. төөмантек)',
    
]

with open(inputFilename, 'r' ) as f:
    content = f.read()
    
    content_new = content
    
# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub(rf'<blockquote>({metaOrOriginWord}),? ({metaOrOriginWord}),? ?({metaOrOriginWord})?</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)

    content_new = re.sub(rf'<blockquote>({metaWord})<\/blockquote>', r'<meta>\1</meta>', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>({originWord})<\/blockquote>', r'<origin>\1</origin>', content_new, flags = re.M)
    content_new = re.sub(
        r'<blockquote>(усиление к словам, начинающимся на .*?)</blockquote>',
        r'<meta>\1</meta>',
        content_new,
        flags=re.M
    )
    content_new = re.sub(
        r'<blockquote>(подражательное слово.*)</blockquote>',
        r'<meta>\1</meta>',
        content_new,
        flags=re.M
    )
    for exc in manual_exceptions:
        content_new = content_new.replace(f'<blockquote>{exc}</blockquote>', f'<meta>{exc}</meta>')

    # New structured logic
    try:
        # Check for XML declaration
        xml_decl = ""
        if content_new.lstrip().startswith('<?xml'):
            end_index = content_new.find('?>')
            if end_index != -1:
                xml_decl = content_new[:end_index+2]
                content_new = content_new[end_index+2:].lstrip()

        # Wrap in a root element to ensure valid XML for parsing
        root = ET.fromstring(f"<root>{content_new}</root>")
        
        # Pre-compile regexes
        re_link = re.compile(linkKeyword)
        
        # Regex to match 1, 2, or 3 meta/origin words at start
        # Identical to the logic verified in reproduction script
        full_pattern = rf"^({metaOrOriginWord})(\s+({metaOrOriginWord}))?(\s+({metaOrOriginWord}))?(?=\s|$)"
        re_start_meta = re.compile(full_pattern)
        
        re_meta_only = re.compile(f"^({metaWord})$")
        re_origin_only = re.compile(f"^({originWord})$")
        
        parent_map = {c: p for p in root.iter() for c in p}
        
        cards = root.findall('.//card')
        for card in cards:
            for bq in card.findall('.//blockquote'):
                if bq.text:
                    text_stripped = bq.text.strip()
                    # Match "южн. [" followed by one word (no spaces) followed by "]"
                    match = re.search(r'(южн\.\s+\[[^\]\s]+\])$', text_stripped)
                    if match:
                        matched_text = match.group(1)
                        bq.text = text_stripped[:match.start()].rstrip()
                        
                        meta_el = ET.Element('meta')
                        meta_el.text = matched_text
                        meta_el.tail = '\n'
                        
                        parent = parent_map[bq]
                        bq_idx = list(parent).index(bq)
                        parent.insert(bq_idx + 1, meta_el)

            parents_to_check = [card] + card.findall('.//meaning')
            for p in parents_to_check:
                blockquotes = p.findall('./blockquote')
                if not blockquotes:
                    continue
                
                # Check FIRST blockquote only
                bq = blockquotes[0]
                if bq.text is None:
                    continue
                
                text = bq.text.strip()
                
                # 1. Check link keyword (if contains, skip)
                if re_link.search(text):
                    continue
                
                # 2. Check match at start
                match = re_start_meta.match(text)
                if match:
                    # Extract words
                    words_found = []
                    if match.group(1): words_found.append(match.group(1))
                    if match.group(3): words_found.append(match.group(3))
                    if match.group(5): words_found.append(match.group(5))
                    
                    if not words_found:
                        continue
                        
                    # Prepare new tags
                    new_elements = []
                    for w in words_found:
                        tag_name = 'meta'
                        if re_origin_only.match(w):
                            tag_name = 'origin'
                        # default to meta if not origin (or strictly meta)
                        
                        el = ET.Element(tag_name)
                        el.text = w
                        el.tail = '\n'
                        new_elements.append(el)
                    
                    # Insert into parent before the blockquote
                    bq_index = list(p).index(bq)
                    for el in reversed(new_elements):
                        p.insert(bq_index, el)
                    
                    # Cleanup blockquote text
                    # Use match.end() to cut out the matched part
                    new_text = text[match.end():].lstrip()
                    # Preserve trailing space if blockquote has child elements
                    # (e.g. <wordLink>) — otherwise the text runs into the tag
                    if len(bq) > 0 and bq.text and bq.text[-1] == ' ':
                        new_text = new_text + ' '
                    bq.text = new_text

        # Convert back to string
        # Exclude the fake root tag
        # ET.tostring includes the root, so we process children or use string manipulation
        # Just getting inner XML of root is cleaner
        raw_xml = ET.tostring(root, encoding='unicode')
        # Remove <root> and </root>
        content_new = raw_xml.replace('<root>', '', 1).replace('</root>', '', 1)
        if xml_decl:
            content_new = xml_decl + '\n' + content_new
        
    except ET.ParseError as e:
        print(f"Error parsing XML for meta extraction: {e}")
        # Build might fail or continue with partial changes. 
        # For now, we print error and keep content_new as is (from regexes).

    outputFile = open(outputFilename, "w")
    outputFile.write(content_new)
    outputFile.close()
