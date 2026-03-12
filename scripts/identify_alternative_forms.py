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

content_new = re.sub(
    r'<blockquote>(\(неправ\.\s+(?!вместо\b)[^)]+\))</blockquote>',
    r'<alternativeForm>\1</alternativeForm>',
    content_new,
    flags=re.M
)

hardcoded_cases = [
    '(деепр. бүйүрүп и бүйрүп)',
    '(деепр. жаап)',
    '(деепр. прош. вр. жумуп и жуумп)',
    '(деепр. ийирип, ийрип)',
    '(деепр. каап)',
    '(деепр. кээп)',
    '(деепр. кооп)',
    '(деепр. көөмп)',
    '(деепр. көөп)',
    '(деепр. сээп)',
    '(деепр. таамп)',
    '(деепр. таап)',
    '(деепр. тээп)',
    '(деепр. чаап и редко чабып)',
    '(деепр. чүйрүп и чүйүрүп)',
    '(деепр. прош. вр. үйүрүп или үйрүп)',
    '(деепр. өөп; см. жытта- 2)',
    '(южн. пада)',
    '(южн. падачы)',
    '(южн. палов)',
    '(южн. прич. прош. вр. богон, отриц. форма наст.-буд. вр. бовойт)',
    '(неправ. вместо аа)',
    '(неправ. вместо кун)'
]

for hc in hardcoded_cases:
    content_new = content_new.replace(
        f'<blockquote>{hc}</blockquote>',
        f'<alternativeForm>{hc}</alternativeForm>'
    )

# (точнее ...) blockquote extraction
# 1. Full blockquote replacement: <blockquote>(точнее ...)</blockquote>
content_new = re.sub(
    r'(\s*)<blockquote>(\(точнее\s+[^)]+\))</blockquote>',
    r'\1<alternativeForm>\2</alternativeForm>',
    content_new,
    flags=re.M
)

# 2. Partial blockquote extraction: <blockquote>(точнее ...) ...</blockquote>
content_new = re.sub(
    r'(\s*)<blockquote>(\(точнее\s+[^)]+\))\s+(.+?)</blockquote>',
    r'\1<alternativeForm>\2</alternativeForm>\1<blockquote>\3</blockquote>',
    content_new,
    flags=re.M
)

# (при наращении аффиксов ...) blockquote extraction
# Rename the entire blockquote to alternativeForm
content_new = re.sub(
    r'(\s*)<blockquote>(\(при наращении аффиксов\s+[^)]+\).*?)</blockquote>',
    r'\1<alternativeForm>\2</alternativeForm>',
    content_new,
    flags=re.M
)

# (орф. ...) blockquote extraction
# Rename the entire blockquote to alternativeForm
content_new = re.sub(
    r'(\s*)<blockquote>(\(орф\.\s+[^)]+\).*?)</blockquote>',
    r'\1<alternativeForm>\2</alternativeForm>',
    content_new,
    flags=re.M
)

count = content_new.count('<alternativeForm>')
print(f'Total alternativeForm tags: {count}')

with open(outputFilename, 'w') as f:
    f.write(content_new)
