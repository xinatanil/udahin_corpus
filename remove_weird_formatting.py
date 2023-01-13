import re
import fileinput


with open ('letter_wip.xml', 'r' ) as f:
    content = f.read()

# replace weird newline and 8 spaces in source
    content_new = re.sub('\n               ', r' ', content, flags = re.M)

# remove my mistake with global search and replace
# <p>южн.</p>
#         </blockquote>
    content_new = re.sub('<p>южн.</p>\n\t\t</blockquote>', r'южн.</blockquote>', content_new, flags = re.M)

# remove consequences of previous command
# <blockquote>
#            южн.</blockquote>
    content_new = re.sub('<blockquote>\n\t\t\tюжн.</blockquote>', r'<blockquote>южн.</blockquote>', content_new, flags = re.M)
    
#        <blockquote>
#            <p>южн.</p>
#        </blockquote>
# to
# <blockquote><p>южн.</p></blockquote>
#    content_new = re.sub('<blockquote>\n\t\t\t<p>южн.<\/p>\n\t\t<\/blockquote>', r'<meta>южн.</meta>', content_new, flags = re.M)

    outputFile = open("letter_after.xml", "w")
    outputFile.write(content_new)
    outputFile.close()


#content_new = re.sub('', r'', content_new, flags = re.M)
