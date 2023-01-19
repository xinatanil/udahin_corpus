import re
import fileinput

metaWord = 'разг\.|уст\.|лингв\.|перен\.|полит\.|спорт\.|полигр\.|с\.-х\.|рел\.|воен\.|дип\.|горн\.|пед\.|этн\.|лит\.|театр\.|филос\.|миф\.|геол\.|хим\.|мед\.|тех\.|ист\.|мат\.|бот\.|сев\.|южн\.|чатк\.|чуйск\.|тяньш\.|талас\.|памир\.|синьцз\.|редко|прям\., перен\.'
originWord = 'кит\.|р\.|ар\.|тиб\.|ир\.|ар\.-ир\.|р\.-ир\.|ир\.-кирг\.'
metaOrOriginWord = metaWord + '|' + originWord
referencePattern = '(\w+)-? ?([IVX]+)? ?(\d)?[\.|;]?'
referenceReplace = 'word="\\1" index="\\2" subindex="\\3"'
with open ('letter_after.xml', 'r' ) as f:
    content = f.read()

# <blockquote>в разн. знач. район.</blockquote>
# to
#        <meta>в разн. знач.</meta>
#        <trn>$1</trn>
    content_new = re.sub('<blockquote>в разн\. знач\. (\w+).?<\/blockquote>', r'<meta>в разн. знач.</meta>\n\t\t<trn>\1</trn>', content, flags = re.M)

# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub(rf'<blockquote>({metaOrOriginWord}) ({metaOrOriginWord}) ?({metaOrOriginWord})?</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)

# <blockquote>2. южн. уст. сорт кустарной хлопчатобумажной материи с тканым узором;</blockquote>
    content_new = re.sub(rf'<blockquote>(\d\.) ({metaOrOriginWord}) ?({metaOrOriginWord})? (.+)</blockquote>', r'<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n<blockquote>\4</blockquote>\n', content_new, flags = re.M)
    
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
    content_new = re.sub(rf'<blockquote>возвр\.-страд\. от {referencePattern}<\/blockquote>', rf'<refpass {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>возвр\. от {referencePattern}<\/blockquote>', rf'<refv {referenceReplace} />', content_new, flags = re.M)
    
    content_new = re.sub(rf'<blockquote>уподоб\. от {referencePattern}<\/blockquote>', rf'<similative {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>парное к {referencePattern}<\/blockquote>', rf'<pair {referenceReplace} />', content_new, flags = re.M)
    
    
    #replace meta sameas and look tags
    content_new = re.sub(rf'<blockquote>то же, что {referencePattern}<\/blockquote>', rf'<sameas {referenceReplace} />', content_new, flags = re.M)
    content_new = re.sub(rf'<blockquote>см\. {referencePattern}<\/blockquote>', rf'<look {referenceReplace} />', content_new, flags = re.M)
    
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
    content_new = re.sub('<blockquote>(.+)@@ (.+.)</blockquote>', r'<ex><source>\1</source>\n<target>\2</target></ex>', content_new, flags = re.M)
    
# <blockquote>адамдан заты бир бөлөк фольк. он лучший из людей (букв. его сущность особая от людей);</blockquote>
# <blockquote>зордун түбү кор болот погов. конец насилия - позор (насилием доброго имени не заслужишь);</blockquote>
    content_new = re.sub('<blockquote>(.+) (фольк.|погов.|стих.) (.+.)</blockquote>', r'<ex><source>\1 \2</source><target>\3</target></ex>', content_new, flags = re.M)

# <blockquote>(ср. зер V)</blockquote>
# to
# <meta>(ср. зер V)</meta>
    content_new = re.sub('<blockquote>\(ср\. (.+)\)</blockquote>', r'<meta>(ср. \1)</meta>', content_new, flags = re.M)
    
    content_new = re.sub('<blockquote>\(или (.+)\)</blockquote>', r'<meta>(или \1)</meta>', content_new, flags = re.M)


    outputFile = open("letter_after.xml", "w")
    outputFile.write(content_new)
    outputFile.close()


#content_new = re.sub('', r'', content_new, flags = re.M)


#ав\.|анат\.|англ\.|башк\.|бенг\.|бран\.|буд\.|букв\.|бухг\.|вводн. сл\.|вет\.|взаимн\.|вин\.|возвр\.|вопр\.|вр\.|в разн. знач\.|в сочет\.|вспом\.|г\.|геогр\.|гл\.|гл. обр\.|грам\.|греч\.|груб\.|дат\.|деепр\.|дет\.|др\.|женск\.|звукоподр\.|знач\.|и. д\.|и др\.|им\.|инд\.|ирон\.|иссык-кульск\.|исх\.|и т. д\.|и т. п\.|ичкилик\.|каз\.|канц\.|карт\.|кирг\.|книжн\.|л\.|-л.\-|ласк\.|межд\.|мест\.|местн\.|метео\.|миф\.|многокр\.|монг\.|муз\.|напр\.|наст\.|неодобр\.|неправ\.|орф\.|отвл\.|отриц\.|офиц\.|охот\.|п\.|памирск\.|погов\.|понуд\.|поэт\.|пренебр\.|прил\.|прим\.|притяж\.|прич\.|противит\.|противоп\.|прош\.|прям\.|психол\.|разг\.|род\.|санскр\.|см\.|собир\.|соед\.|сокр\.|соотв\.|ср\.|стих\.||тадж\.|тат\.|т.е\.|тув\.|узб\.|уйг\.|уменьш\.|уподоб\.|употр\.|усил\.|уступ\.|физ\.|фин\.|фольк\.|шахм\.|школ\.|шутл\.|эвф\.|эк\.|юр.