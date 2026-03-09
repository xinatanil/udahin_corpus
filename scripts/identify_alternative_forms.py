import re
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

with open(inputFilename, 'r') as f:
    content = f.read()

content_new = re.sub(
    r'<blockquote>(\(или .+\))</blockquote>',
    r'<alternativeForm>\1</alternativeForm>',
    content,
    flags=re.M
)

count = content_new.count('<alternativeForm>')
print(f'Total alternativeForm tags: {count}')

with open(outputFilename, 'w') as f:
    f.write(content_new)
