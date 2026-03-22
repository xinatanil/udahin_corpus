import re
import sys
from constants import linkKeyword

if len(sys.argv) < 3:
    print("Usage: python3 identify_cross_references.py <input.xml> <output.xml>")
    sys.exit(1)

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

with open(inputFilename, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all <blockquote> that consist solely of a cross-reference and replace them with <xr>.
standalone_pattern = (
    r'<blockquote>\s*('
    r'\(?\s*' + linkKeyword + r'\s*<wordLink[^>]*/>\s*\)?[.,;]?'
    r')\s*</blockquote>'
)
content_new = re.sub(standalone_pattern, r'<xr>\1</xr>', content, flags=re.M)

# Also catch "то же, что <wordLink...>(см. <wordLink...>)." style blockquotes.
same_as_pattern = (
    r'<blockquote>\s*('
    r'то же,\s*что\s*<wordLink[^>]*/>'
    r'\s*\(\s*см\.\s*<wordLink[^>]*/>\s*\)[.,;]?'
    r')\s*</blockquote>'
)
content_new = re.sub(same_as_pattern, r'<xr>\1</xr>', content_new, flags=re.M)
content_new = re.sub(r'(<xr>то же,\s*что\s*<wordLink[^>]*/>)\(', r'\1 (', content_new)

with open(outputFilename, "w", encoding='utf-8') as outputFile:
    outputFile.write(content_new)
