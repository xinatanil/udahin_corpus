import sys
import re
import xml.etree.ElementTree as ET

def process_file(input_file, output_file):
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except (ET.ParseError, IOError) as e:
        print(f"Error processing XML: {e}")
        return

    # Regex for numbered prefixes like "1. ", "2. ", ..., "20. "
    # We want to match "1. " through "20. " at the start of the string.
    # The dot must be followed by a space.
    prefix_pattern = re.compile(r'^([1-9]|1[0-9]|20)\.\s')

    count_modified = 0

    for card in root.findall('card'):
        meanings = card.findall('meaning')
        for meaning in meanings:
            # Check the first blockquote inside the meaning
            blockquotes = meaning.findall('blockquote')
            if not blockquotes:
                continue

            first_blockquote = blockquotes[0]
            text = first_blockquote.text
            
            if not text:
                continue

            match = prefix_pattern.match(text)
            if match:
                # Extract the number (e.g., "1")
                number = match.group(1)
                full_prefix = match.group(0) # e.g. "1. "

                # Remove prefix from blockquote text
                new_text = text[len(full_prefix):]
                first_blockquote.text = new_text

                # Create <meaningIndex> tag with "1." (no space)
                meaning_index = ET.Element('meaningIndex')
                meaning_index.text = f"{number}."

                # Insert at index 0 of the meaning element
                meaning.insert(0, meaning_index)
                
                count_modified += 1

    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"Modified {count_modified} meanings.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python format_numbered_meanings.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    process_file(input_file, output_file)
