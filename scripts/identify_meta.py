import re
import fileinput
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

from constants import metaWord, originWord

metaOrOriginWord = metaWord + '|' + originWord
with open(inputFilename, 'r' ) as f:
    content = f.read()
    
    #detect links
    content_new = content
    

    
# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub(rf'<blockquote>({metaOrOriginWord}) ({metaOrOriginWord}) ?({metaOrOriginWord})?</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)

    content_new = re.sub(rf'<blockquote>({metaWord})<\/blockquote>', r'<meta>\1</meta>', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>({originWord})<\/blockquote>', r'<origin>\1</origin>', content_new, flags = re.M)

    outputFile = open(outputFilename, "w")
    outputFile.write(content_new)
    outputFile.close()


#ав\.|англ\.|башк\.|бенг\.|буд\.|бухг\.|вводн. сл\.|вет\.|вин\.|вопр\.|вр\.|в сочет\.|вспом\.|г\.||гл\.|гл. обр\.|греч\.|дат\.|деепр\.|дет\.|др\.|звукоподр\.|знач\.|и др\.|им\.|инд\.|исх\.|и т. д\.|и т. п\.|ичкилик\.|каз\.|канц\.|кирг\.|книжн\.|л\.|-л.\-||межд\.|мест\.|местн\.|метео\.|многокр\.|монг\.|муз\.|напр\.|наст\.|неодобр\.|неправ\.|орф\.|отриц\.|офиц\.|п\.|памирск\.|погов\.|поэт\.|пренебр\.|прил\.|прим\.|притяж\.|прич\.|противит\.|противоп\.|прош\.|прям\.|психол\.|разг\.|род\.|санскр\.|см\.|собир\.|соед\.|сокр\.|соотв\.|ср\.|стих\.||тадж\.|тат\.|т.е\.|тув\.|узб\.|уйг\.|уменьш\.|употр\.|усил\.|уступ\.|физ\.|фин\.|фольк\.|шахм\.|школ\.||эк\.

# <blockquote>(см. не I).</blockquote>