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

# Find all <blockquote> that consist solely of a linkKeyword followed by a <wordLink/> tag.
# Replace the <blockquote> tags with <xr> tags.
pattern = r'<blockquote>\s*(' + linkKeyword + r'\s*<wordLink[^>]*/>)\s*</blockquote>'
content_new = re.sub(pattern, r'<xr>\1</xr>', content, flags=re.M)

with open(outputFilename, "w", encoding='utf-8') as outputFile:
    outputFile.write(content_new)
