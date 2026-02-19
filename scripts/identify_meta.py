import re
import fileinput
import sys
import xml.etree.ElementTree as ET

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

from constants import metaWord, originWord, linkKeyword

metaOrOriginWord = metaWord + '|' + originWord
with open(inputFilename, 'r' ) as f:
    content = f.read()
    
    content_new = content
    
# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub(rf'<blockquote>({metaOrOriginWord}) ({metaOrOriginWord}) ?({metaOrOriginWord})?</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)

    content_new = re.sub(rf'<blockquote>({metaWord})<\/blockquote>', r'<meta>\1</meta>', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>({originWord})<\/blockquote>', r'<origin>\1</origin>', content_new, flags = re.M)

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
        
        cards = root.findall('.//card')
        for card in cards:
            meanings = card.findall('.//meaning')
            for meaning in meanings:
                blockquotes = meaning.findall('./blockquote')
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
                    
                    # Insert into meaning before the blockquote
                    bq_index = list(meaning).index(bq)
                    for el in reversed(new_elements):
                        meaning.insert(bq_index, el)
                    
                    # Cleanup blockquote text
                    # Use match.end() to cut out the matched part
                    new_text = text[match.end():].lstrip()
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
