import re
import fileinput


with open ('letter_wip.xml', 'r' ) as f:
    content = f.read()

# replace weird newline and 8 spaces in source
    content_new = re.sub('\n               ', r' ', content, flags = re.M)

    content_new = re.sub('<p>южн\.</p>', r'южн.', content_new, flags = re.M)
    content_new = re.sub('<p>фольк\.</p>', r'фольк.', content_new, flags = re.M)

    content_new = re.sub('южн\.\n\t\t</blockquote>', r'южн.</blockquote>', content_new, flags = re.M)
    content_new = re.sub('<blockquote>\n\t\t\tюжн\.', r'<blockquote>южн.', content_new, flags = re.M)
    
    outputFile = open("letter_after.xml", "w")
    outputFile.write(content_new)
    outputFile.close()


#content_new = re.sub('', r'', content_new, flags = re.M)
