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

content_new = content_new.replace(
    '<blockquote>(неправ. вместо аа)</blockquote>',
    '<alternativeForm>(неправ. вместо аа)</alternativeForm>'
)
content_new = content_new.replace(
    '<blockquote>(неправ. вместо кун)</blockquote>',
    '<alternativeForm>(неправ. вместо кун)</alternativeForm>'
)

content_new = re.sub(
    r'<blockquote>(\(неправ\.\s+(?!вместо\b)[^)]+\))</blockquote>',
    r'<alternativeForm>\1</alternativeForm>',
    content_new,
    flags=re.M
)

deepr_cases = [
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
    '(деепр. өөп; см. жытта- 2)'
]

for dc in deepr_cases:
    content_new = content_new.replace(
        f'<blockquote>{dc}</blockquote>',
        f'<alternativeForm>{dc}</alternativeForm>'
    )

count = content_new.count('<alternativeForm>')
print(f'Total alternativeForm tags: {count}')

with open(outputFilename, 'w') as f:
    f.write(content_new)
