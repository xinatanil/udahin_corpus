import re
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

linkKeyword = r'и\. д\. от |понуд\. от |взаимн\. от |страд\. от |возвр\.- ?страд\. от |возвр\. от |уподоб\. от |парное к |многокр\. от |отвл\. от |уменьш\. от |уменьш\.-ласк\. от |деепр\. от |\(ср\. |то же, что |см\. '
referencePattern = '(\w+-?),? ?([IVX]+)? ?(\d)?[\.|;]?'
referenceReplace = '<wordLink word="\\2" homonym="\\3" meaning="\\4" />'

with open(inputFilename, 'r') as f:
    content = f.read()
    
    #detect links
    content_new = re.sub(rf'({linkKeyword}){referencePattern}', rf'\1{referenceReplace}', content, flags = re.M)
    content_new = re.sub('homonym=""', r'', content_new, flags = re.M)
    content_new = re.sub('meaning=""', r'', content_new, flags = re.M)

    with open(outputFilename, "w") as outputFile:
        outputFile.write(content_new)
