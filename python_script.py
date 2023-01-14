import re
import fileinput


with open ('letter_after.xml', 'r' ) as f:
    content = f.read()


# <blockquote>в разн. знач. район.</blockquote>
# to
#        <meta>в разн. знач.</meta>
#        <trn>$1</trn>
    content_new = re.sub('<blockquote>в разн\. знач\. (\w+).?<\/blockquote>', r'<meta>в разн. знач.</meta>\n\t\t<trn>\1</trn>', content, flags = re.M)

# <blockquote>р. ист. разг.</blockquote>
# <blockquote>р. сев.</blockquote>
    content_new = re.sub('<blockquote>(?!см)([а-я]{1,6}\.|редко) ?([а-я]{1,6}\.|редко)? ([а-я]{1,6}\.|редко)</blockquote>', r'<blockquote>\1</blockquote>\n<blockquote>\2</blockquote>\n<blockquote>\3</blockquote>\n', content_new, flags = re.M)
# remove empty
# <blockquote></blockquote>\n
# that previos command generated
    content_new = re.sub('<blockquote></blockquote>\n', r'', content_new, flags = re.M)

    
    content_new = re.sub('<blockquote>(кит|р|ар|тиб|ир|ар\.-ир|р\.-ир)\.<\/blockquote>', r'<origin>\1.</origin>', content_new, flags = re.M)

    #process meta for different verb categories
    content_new = re.sub('<blockquote>и\. д\. от (\w+).?.?<\/blockquote>', r'<actionNoun word="\1" />', content_new, flags = re.M)
    content_new = re.sub('<blockquote>понуд\. от (\w+).? ?([IV]+)?.?<\/blockquote>', r'<caus word="\1" index="\2" />', content_new, flags = re.M)
    content_new = re.sub('<blockquote>взаимн\. от (\w+).? ?([IV]+).?<\/blockquote>', r'<recv word="\1" index="\2" />', content_new, flags = re.M)
    content_new = re.sub('<blockquote>возвр\.-страд\. от (\w+).?.?<\/blockquote>', r'<refpass word="\1" />', content_new, flags = re.M)
    content_new = re.sub('<blockquote>возвр\. от (\w+).?.?<\/blockquote>', r'<refv word="\1" />', content_new, flags = re.M)
    
    
    #replace meta sameas and look tags
    content_new = re.sub('<blockquote>то же, что (\w+)-?\s?([IV]+)?\s?(\d)?.<\/blockquote>', r'<sameas word="\1" index="\2" subindex="\3" />', content_new, flags = re.M)
    content_new = re.sub('<sameas word="(\w+)" index="" subindex="" \/>', r'<sameas word="\1" />', content_new, flags = re.M)
    content_new = re.sub('<sameas word="(\w+)" index="(\w+)" subindex="" \/>', r'<sameas word="\1" index="\2" />', content_new, flags = re.M)
    content_new = re.sub('<sameas word="(\w+)" index="" subindex="(.+)" \/>', r'<sameas word="\1" subindex="\2" />', content_new, flags = re.M)
    content_new = re.sub('<blockquote>см\. (\w+)-?\s?([IV]+)?\s?(\d)?.<\/blockquote>', r'<look word="\1" index="\2" subindex="\3" />', content_new, flags = re.M)
    content_new = re.sub('<look word="(\w+)" index="" subindex="" \/>', r'<look word="\1" />', content_new, flags = re.M)
    content_new = re.sub('<look word="(\w+)" index="(\w+)" subindex="" \/>', r'<look word="\1" index="\2" />', content_new, flags = re.M)
    content_new = re.sub('<look word="(\w+)" index="" subindex="(.+)" \/>', r'<look word="\1" subindex="\2" />', content_new, flags = re.M)
    content_new = re.sub('index="I"', r'index="1"', content_new, flags = re.M)
    content_new = re.sub('index="II"', r'index="2"', content_new, flags = re.M)
    content_new = re.sub('index="III"', r'index="3"', content_new, flags = re.M)
    content_new = re.sub('index="IV"', r'index="4"', content_new, flags = re.M)
    content_new = re.sub('index="V"', r'index="5"', content_new, flags = re.M)
    
    content_new = re.sub('<blockquote>(разг|уст|лингв|полит|спорт|полигр|с\.-х|рел|воен|дип|горн|пед|этн)\.<\/blockquote>', r'<meta>\1.</meta>', content_new, flags = re.M)
    content_new = re.sub('<blockquote>(лит|театр|филос|миф)\.<\/blockquote>', r'<meta>\1.</meta>', content_new, flags = re.M)
    content_new = re.sub('<blockquote>(геол|хим|мед|тех|ист|мат|бот)\.<\/blockquote>', r'<meta>\1.</meta>', content_new, flags = re.M)
    content_new = re.sub('<blockquote>(сев|южн|чатк|чуйск|тяньш|талас|памир|синьцз)\.<\/blockquote>', r'<meta>\1.</meta>', content_new, flags = re.M)
    
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


    outputFile = open("letter_after.xml", "w")
    outputFile.write(content_new)
    outputFile.close()


#content_new = re.sub('', r'', content_new, flags = re.M)
