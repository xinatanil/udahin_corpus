
import re

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Helper to build the regex for a specific number
    # <blockquote> followed by whitespace, then n), then anything EXCEPT closing blockquote
    # We use (?:(?!</blockquote>).)* to match anything that is NOT the start of </blockquote>
    # This prevents backtracking across multiple blockquotes
    
    def get_pat(n):
        return r'(<blockquote>\s*' + str(n) + r'\)(?:(?!</blockquote>).)*</blockquote>)'

    # Pattern for 6 items
    # We allow whitespace between them
    pat6 = re.compile(
        get_pat(1) + r'\s*' +
        get_pat(2) + r'\s*' +
        get_pat(3) + r'\s*' +
        get_pat(4) + r'\s*' +
        get_pat(5) + r'\s*' +
        get_pat(6),
        re.DOTALL | re.IGNORECASE
    )

    # Pattern for 5 items
    pat5 = re.compile(
        get_pat(1) + r'\s*' +
        get_pat(2) + r'\s*' +
        get_pat(3) + r'\s*' +
        get_pat(4) + r'\s*' +
        get_pat(5),
        re.DOTALL | re.IGNORECASE
    )

    def replacer(match):
        # Replace all occurrences of "blockquote" with "category" in the matched string
        # This handles closing tags too </blockquote> -> </category>
        # And preserves the content/formatting/whitespace exactly as matched
        # Case-insensitive replacement (but regex matched blockquote case-insensitively)
        text = match.group(0)
        # Use simple string replace because we know the text contains ONLY the matched sequence
        # We assume <blockquote> is lowercase or we can do case-insensitive replace if needed.
        # But for robustness, let's just do case-insensitive replace of the tags.
        text = re.sub(r'blockquote', 'category', text, flags=re.IGNORECASE)
        return text

    # Apply 6 first (greedy for more items)
    content, n6 = pat6.subn(replacer, content)

    # Apply 5 next
    content, n5 = pat5.subn(replacer, content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        input_filename = sys.argv[1]
        output_filename = sys.argv[2]
    else:
        # Default or fallback
        input_filename = 'sources/corrected_source_dict.xml' 
        output_filename = 'sources/corrected_source_dict_with_categories.xml'
        
    process_file(input_filename, output_filename)