import re
import fileinput
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

metaWord = 'разг\.|уст\.|лингв\.|перен\.|полит\.|спорт\.|полигр\.|с\.-х\.|рел\.|воен\.|дип\.|горн\.|пед\.|этн\.|лит\.|театр\.|филос\.|миф\.|геол\.|хим\.|мед\.|тех\.|ист\.|мат\.|бот\.|сев\.|южн\.|чатк\.|чуйск\.|тяньш\.|талас\.|памир\.|синьцз\.|редко|прям\., перен\.|бран\.|карт\.|женск\.|охот\.|муз\.|иссык-кульск\.|анат\.|грам\.|ирон\.|инд\.|геогр\.|ласк\.|эвф\.|груб\.|шутл\.|юр\.'
originWord = 'кит\.|р\.|ар\.|тиб\.|ир\.|ар\.-ир\.|р\.-ир\.|ир\.-кирг\.|ир\.-ар\.|кирг\.-ир\.'
metaOrOriginWord = metaWord + '|' + originWord
referencePattern = '(\w+)-?,? ?([IVX]+)? ?(\d)?[\.|;]?'
referenceReplace = 'word="\\1" index="\\2" subindex="\\3"'
with open(inputFilename, 'r' ) as f:
    content = f.read()

# <blockquote>в разн. знач. район.</blockquote>
# to
#        <meta>в разн. знач.</meta>
#        <trn>$1</trn>
    content_new = re.sub('<blockquote>в разн\. знач\. (\w+).?<\/blockquote>', r'<meta>в разн. знач.</meta>\n\t\t<trn>\1</trn>', content, flags = re.M)

# <blockquote>пейилдүүлүк: кичи пейилдүүлүк## вежливость, учтивость;</blockquote>
    content_new = re.sub('<blockquote>(.+: )?(.+)## (.+)</blockquote>(\n\s+<blockquote>(.+)@@1 (.+.)</blockquote>)?(\n\s+<blockquote>(.+)@@2 (.+.)</blockquote>)?(\n\s+<blockquote>(.+)@@3 (.+.)</blockquote>)?(\n\s+<blockquote>(.+)@@4 (.+.)</blockquote>)?(\n\s+<blockquote>(.+)@@5 (.+.)</blockquote>)?', r'<minicard><k>\2</k>\n<trn>\3</trn><ex><source>\5</source>\n<target>\6</target></ex><ex><source>\8</source>\n<target>\9</target></ex><ex><source>\11</source>\n<target>\12</target></ex><ex><source>\14</source>\n<target>\15</target></ex><ex><source>\17</source>\n<target>\18</target></ex></minicard>', content_new, flags=re.M)
    content_new = re.sub('<ex><source></source>\n<target></target></ex>', r'', content_new, flags = re.M)

    content_new = re.sub('<blockquote>([^:\n]+)</blockquote>\n\s+<blockquote>1\) (.+)</blockquote>\s+<blockquote>2\) (.+)</blockquote>', r'<minicard><k>\1</k><meaning><trn>\2</trn></meaning><meaning><trn>\3</trn></meaning></minicard>', content_new, flags=re.M)

# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub(rf'<blockquote>({metaOrOriginWord}) ({metaOrOriginWord}) ?({metaOrOriginWord})?</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)
    
    content_new = re.sub(rf'<trn>({metaOrOriginWord}) ({metaOrOriginWord})? ?({metaOrOriginWord})? ?(.+)</trn>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n<trn>\4</trn>\n', content_new, flags = re.M)

# <blockquote>2. южн. уст. сорт кустарной хлопчатобумажной материи с тканым узором;</blockquote>
    content_new = re.sub(rf'<blockquote>(\d\.)? ?({metaOrOriginWord}) ?({metaOrOriginWord})? (.+)</blockquote>', r'<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n<blockquote>\4</blockquote>\n', content_new, flags = re.M)
    
    # remove numbers in meanings
    content_new = re.sub(rf'<blockquote>\d\. (.+)</blockquote>', r'<blockquote>\1</blockquote>', content_new, flags = re.M)
    # remove numbered homonyms
    content_new = re.sub(rf'<blockquote>\w+-? [IV]+</blockquote>', r'', content_new, flags = re.M)
    
    content_new = re.sub(rf'<blockquote>({metaWord})<\/blockquote>', r'<meta>\1</meta>', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>({originWord})<\/blockquote>', r'<origin>\1</origin>', content_new, flags = re.M)

    content_new = re.sub(r'<meta>прям., перен.</meta>', r'<meta>прям.</meta>\n<meta>перен.</meta>\n', content_new, flags = re.M)

    #process meta for different verb categories
    content_new = re.sub(rf'<blockquote>и\. д\. от {referencePattern}<\/blockquote>', rf'<actionNoun {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>понуд\. от {referencePattern}<\/blockquote>', rf'<caus {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>взаимн\. от {referencePattern}<\/blockquote>', rf'<recv {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>страд\. от {referencePattern}<\/blockquote>', rf'<pass {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>возвр\.- ?страд\. от {referencePattern}<\/blockquote>', rf'<refpass {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>возвр\. от {referencePattern}<\/blockquote>', rf'<refv {referenceReplace} />', content_new, flags = re.M)
    
    content_new = re.sub(rf'<blockquote>уподоб\. от {referencePattern}<\/blockquote>', rf'<similative {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>парное к {referencePattern}<\/blockquote>', rf'<pair {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>многокр\. от {referencePattern}<\/blockquote>', rf'<iter {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>отвл\. от {referencePattern}<\/blockquote>', rf'<abstract {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>уменьш\. от {referencePattern}<\/blockquote>', rf'<dim {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>уменьш\.-ласк\. от {referencePattern}<\/blockquote>', rf'<dimaff {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>деепр\. от {referencePattern}<\/blockquote>', rf'<participle {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>\(ср\. {referencePattern}\)<\/blockquote>', rf'<compare {referenceReplace} />', content_new, flags = re.M)

    #replace meta sameas and look tags
    content_new = re.sub(rf'<blockquote>то же, что {referencePattern}<\/blockquote>', rf'<sameas {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>\(?см\. {referencePattern}\)?.?<\/blockquote>', rf'<look {referenceReplace} />', content_new, flags = re.M)
    
    content_new = re.sub(rf'<(.+)>то же, что ([\w\- ]+) \(см\. {referencePattern}\).?</\1>', r'<anchorRef word="\3" index="\4" subindex="\5" anchor="\2"/>', content_new, flags = re.M)

    content_new = re.sub('subindex=""', r'', content_new, flags = re.M)
    content_new = re.sub('index=""', r'', content_new, flags = re.M)
    content_new = re.sub('<blockquote></blockquote>\n', r'', content_new, flags = re.M)
    
    content_new = re.sub('index="I"', r'index="1"', content_new, flags = re.M)
    content_new = re.sub('index="II"', r'index="2"', content_new, flags = re.M)
    content_new = re.sub('index="III"', r'index="3"', content_new, flags = re.M)
    content_new = re.sub('index="IV"', r'index="4"', content_new, flags = re.M)
    content_new = re.sub('index="V"', r'index="5"', content_new, flags = re.M)
    content_new = re.sub('index="VI"', r'index="6"', content_new, flags = re.M)
    content_new = re.sub('index="VII"', r'index="7"', content_new, flags = re.M)
    content_new = re.sub('index="VIII"', r'index="8"', content_new, flags = re.M)
    content_new = re.sub('index="IX"', r'index="9"', content_new, flags = re.M)
    content_new = re.sub('index="X"', r'index="10"', content_new, flags = re.M)
    
    
#    <card>
#        <k>радиола</k>
#        <blockquote>радиола.</blockquote>
#    </card>
# to
#    <card>
#        <k>радиола</k>
#        <trn>радиола</trn>
#    </card>
    content_new = re.sub('<k>(.+)</k>\n\t\t([\S\s]+)?<blockquote>\\1.</blockquote>', r'<k>\1</k>\n\t\t\2<trn>\1</trn>', content_new, flags = re.M)

# <blockquote>радиолошкон райондор&& радиофицированные районы.</blockquote>
# to
#        <ex>
#            <source>радиолошкон райондор</source>
#            <target>радиофицированные районы</target>
#        </ex>
    content_new = re.sub('<blockquote>(.+)@@ ?(.+.)</blockquote>', r'<ex><source>\1</source>\n<target>\2</target></ex>', content_new, flags = re.M)
    
# <blockquote>адамдан заты бир бөлөк фольк. он лучший из людей (букв. его сущность особая от людей);</blockquote>
# <blockquote>зордун түбү кор болот погов. конец насилия - позор (насилием доброго имени не заслужишь);</blockquote>
    # content_new = re.sub('<blockquote>(.+) (фольк\.|погов\.|стих\.|ист\.) (.+.)</blockquote>', r'<ex><source>\1 \2</source><target>\3</target></ex>', content_new, flags = re.M)


# <blockquote>(ср. зер V)</blockquote>
# to
# <meta>(ср. зер V)</meta>
    content_new = re.sub('<blockquote>\(ср\. (.+)\).?</blockquote>', r'<meta>(ср. \1)</meta>', content_new, flags = re.M)
    
    content_new = re.sub('<blockquote>\(или (.+)\)</blockquote>', r'<alter>(или \1)</alter>', content_new, flags = re.M)



    outputFile = open(outputFilename, "w")
    outputFile.write(content_new)
    outputFile.close()


#ав\.|англ\.|башк\.|бенг\.|буд\.|бухг\.|вводн. сл\.|вет\.|вин\.|вопр\.|вр\.|в сочет\.|вспом\.|г\.||гл\.|гл. обр\.|греч\.|дат\.|деепр\.|дет\.|др\.|звукоподр\.|знач\.|и др\.|им\.|инд\.|исх\.|и т. д\.|и т. п\.|ичкилик\.|каз\.|канц\.|кирг\.|книжн\.|л\.|-л.\-||межд\.|мест\.|местн\.|метео\.|многокр\.|монг\.|муз\.|напр\.|наст\.|неодобр\.|неправ\.|орф\.|отриц\.|офиц\.|п\.|памирск\.|погов\.|поэт\.|пренебр\.|прил\.|прим\.|притяж\.|прич\.|противит\.|противоп\.|прош\.|прям\.|психол\.|разг\.|род\.|санскр\.|см\.|собир\.|соед\.|сокр\.|соотв\.|ср\.|стих\.||тадж\.|тат\.|т.е\.|тув\.|узб\.|уйг\.|уменьш\.|употр\.|усил\.|уступ\.|физ\.|фин\.|фольк\.|шахм\.|школ\.||эк\.

# <blockquote>(см. не I).</blockquote>