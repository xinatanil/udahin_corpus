import re
import fileinput
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

metaWord = 'разг\.|уст\.|лингв\.|перен\.|полит\.|спорт\.|полигр\.|с\.-х\.|рел\.|воен\.|дип\.|горн\.|пед\.|этн\.|лит\.|театр\.|филос\.|миф\.|геол\.|хим\.|мед\.|тех\.|ист\.|мат\.|бот\.|сев\.|южн\.|чатк\.|чуйск\.|тяньш\.|талас\.|памир\.|синьцз\.|редко|прям\., перен\.|бран\.|карт\.|женск\.|охот\.|муз\.|иссык-кульск\.|анат\.|грам\.|ирон\.|инд\.|геогр\.|ласк\.|эвф\.|груб\.|шутл\.|юр\.|дет\.|фольк\.|в отриц\. обороте'
originWord = 'кит\.|р\.|ар\.|тиб\.|ир\.|ар\.-ир\.|р\.-ир\.|ир\.-кирг\.|ир\.-ар\.|кирг\.-ир\.'
metaOrOriginWord = metaWord + '|' + originWord
linkKeyword = r'и\. д\. от |понуд\. от |взаимн\. от |страд\. от |возвр\.- ?страд\. от |возвр\. от |уподоб\. от |парное к |многокр\. от |отвл\. от |уменьш\. от |уменьш\.-ласк\. от |деепр\. от |\(ср\. |то же, что |см\. '
referencePattern = '(\w+-?),? ?([IVX]+)? ?(\d)?[\.|;]?'
referenceReplace = '<wordLink word="\\2" homonym="\\3" meaning="\\4" />'
with open(inputFilename, 'r' ) as f:
    content = f.read()
    
    #detect links
    content_new = re.sub(rf'({linkKeyword}){referencePattern}', rf'\1{referenceReplace}', content, flags = re.M)
    content_new = re.sub('homonym=""', r'', content_new, flags = re.M)
    content_new = re.sub('meaning=""', r'', content_new, flags = re.M)
    

    
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