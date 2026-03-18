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
    '(неправ. вместо кун)',
    '(ак сакал)',
    '(ап-алыс)',
    '(ап-апакай)',
    '(чаще багелек, иногда багалак)',
    '(бай-аке)',
    '(да-эле)',
    '(дин-ислам)',
    '(жайма аш)',
    '(жайлы)',
    '(жапакеш)',
    '(зирбе)',
    '(итебар)',
    '(ихин)',
    '(кабаанак)',
    '(канааттанарлык)',
    '(канааттандырарлык)',
    '(канжарла-)',
    '(кери бейил)',
    '(койну, койнуң, койнум и т.д.)',
    '(кур-куй)',
    '(курт)',
    '(курутов)',
    '(кыйымалуу)',
    '(кып-кызыл)',
    '(кырр-кырла-)',
    '(кычырла-)',
    '(көк тал)',
    '(көк сеңке)',
    '(ла илаха ил алла)',
    '(лок-ло)',
    '(мана-бу)',
    '(мады-эшек)',
    '(чаще менменсин-, см.)',
    '(мунун, мунусу и т.д.)',
    '(мына як)',
    '(мырза-айым)',
    '(накта)',
    '(не-эт)',
    '(нечен)',
    '(олда)',
    '(оорукчан)',
    '(ошону-эт-)',
    '(ошого, ошогон, ошоо дат. п., ошондо местн. п., ошондон, ошонон исх. п.)',
    '(сал-а кой-мо)',
    '(Сибирь)',
    '(сокурлук)',
    '(стихиялык)',
    '(сүзөөнөк)',
    '(сураанчак)',
    '(суракчаан)',
    '(сүткөр)',
    '(сүткорчулук)',
    '(суу бурар)',
    '(сымпый-)',
    '(сырдыгаш)',
    '(сөгөр)',
    '(сөлпөр)',
    '(сөмөтей)',
    '(тажрыйба)',
    '(таканчык)',
    '(такылдатыш)',
    '(тамашакор, тамашакөй)',
    '(тамшант-)',
    '(таңатыр-)',
    '(тандалуу)',
    '(тандамалуу)',
    '(танки)',
    '(таржымал)',
    '(тогоон)',
    '(тоскоолдук)',
    '(түн ичинде)',
    '(тупа)',
    '(түркөйү)',
    '(тү)',
    '(түшкүсүн)',
    '(убайран)',
    '(үйрөткүлүү)',
    '(үйүрлүү)',
    '(укумчул)',
    '(умашта-)',
    '(үмүткөр)',
    '(уруучулук)',
    '(уул-у-чу-лук)',
    '(участкалык)',
    '(участоктуу)',
    '(чаар ала)',
    '(чагелек)',
    '(чакырчу)',
    '(чалмачыл)',
    '(чарапзел)',
    '(чемишке)',
    '(чертпут)',
    '(чикелек)',
    '(чү-де)',
    '(чүңкөлөй)',
    '(чууру-)',
    '(чуштугуй)',
    '(чуштуй-)',
    '(чуштуйт-)',
    '(чуштук)',
    '(чымчалак)',
    '(чыңдоолу)',
    '(чыңыроон)',
    '(чөмөлөк)',
    '(чөңкө)',
    '(шовинисчилик)',
    '(шогон)',
    '(шүйшүнт-)',
    '(шүүдрүм)',
    '(шыгырчыл)',
    '(шыдыра)',
    '(шыкылды)',
    '(ызбошчик)',
    '(ылы)',
    '(ыпын)',
    '(ыраматылык)',
    '(ыстарчын)',
    '(ычкырлык)',
    '(эмгичекти)',
    '(э-ме-ген-де)',
    '(э-ме-й)',
    '(э-ме-с)',
    '(э-ме-се)',
    '(эмне-эт-)',
    '(эмизүү)',
    '(эмине)',
    '(эминелик)',
    '(эминеликтен)',
    '(энечил)',
    '(эңишмек)',
    '(эргиште-)',
    '(эрден)',
    '(эригисиз)',
    '(эрте-менен-ки)',
    '(өзү бүтөт)',
    '(өткөр-ө)',
    '(өт II-ө)',
	'(в практике чаще арт-)',
	'(аткаруу комитети)',
    '(мн. ч. балдар, реже балалар)',
    '(в печати бирери, южн. бирээргиси)',
	'(встречается и дооран)',
    '(иногда жайчыл)',
    '(чаще ичеги)',
    '(ишшек)',
    '(метатеза казан-кап)',
    '(пишется кайп, кайып или кайп эрен или кайып эрен)',
	'(Коммунисттик Интернационал)',
    '(кул ху аллаху ахад)',
    'или минет-, минт-, мүнт- (муну эт-)',
    '(нээт)',
	'(мүш)',
	'(нез)',
	'(аны эт; в произношении и часто в орфографии ант- с мягким т)',
	'(бу, редко бо)',
    '(кыйыма)',
    '(часто пишется и произносится мийзам)',
    '(местами дандыр, нандыр)',
    'чаще южн. үкө',
    '(о-йак)',
    '(в научной литературе ойрат)',
    '(чаще кара нөшөрлө-)',
    '(ушуну эт-)',
	'(или эмоционально сильнее адам-эй)',
    '(встречаются ещё формы доол, добулбас, доолбарс, доолбаш; первая часть доол - инд.)',
    '(в северных говорах встречаются формы шөкүлдү, шекилди, шыкылды)',
    '(күлүстөн)'
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

# (в произношении ...) blockquote extraction
# Rename the entire blockquote to alternativeForm only if it ends with a parenthesis
content_new = re.sub(
    r'(\s*)<blockquote>(\(в произношении\s+[^)]+\))</blockquote>',
    r'\1<alternativeForm>\2</alternativeForm>',
    content_new,
    flags=re.M
)

count = content_new.count('<alternativeForm>')
print(f'Total alternativeForm tags (before text match): {count}')

hardcoded_cases_pattern1 = {
    '<blockquote>айлампаш (айлан баш)</blockquote>': '<alternativeForm>(айлан баш)</alternativeForm>',
    '<blockquote>апачуу (ап-ачуу)</blockquote>': '<alternativeForm>(ап-ачуу)</alternativeForm>',
    '<blockquote>апачык (ап-ачык)</blockquote>': '<alternativeForm>(ап-ачык)</alternativeForm>',
    '<blockquote>апкир- (алып кир-)</blockquote>': '<alternativeForm>(алып кир-)</alternativeForm>',
    '<blockquote>аппак (ап-ак)</blockquote>': '<alternativeForm>(ап-ак)</alternativeForm>',
    '<blockquote>бирин (бир-ин)</blockquote>': '<alternativeForm>(бир-ин)</alternativeForm>',
    '<blockquote>кагелес (как-элес)</blockquote>': '<alternativeForm>(как-элес)</alternativeForm>',
    '<blockquote>каер (кай йер, кайсы жер)</blockquote>': '<alternativeForm>(кай йер, кайсы жер)</alternativeForm>',
    '<blockquote>казгатар (каз катар)</blockquote>': '<alternativeForm>(каз катар)</alternativeForm>',
    '<blockquote>казгаяк (казык аяк)</blockquote>': '<alternativeForm>(казык аяк)</alternativeForm>',
    '<blockquote>карасана- (кара-сана-)</blockquote>': '<alternativeForm>(кара-сана-)</alternativeForm>',
    '<blockquote>карындыз (кара ындыз, кара андыз)</blockquote>': '<alternativeForm>(кара ындыз, кара андыз)</alternativeForm>',
    '<blockquote>кечкир- (кеч кир)</blockquote>': '<alternativeForm>(кеч кир)</alternativeForm>',
    '<blockquote>кутмаарек (кут-маарек)</blockquote>': '<alternativeForm>(кут-маарек)</alternativeForm>'
}

for bq, alt in hardcoded_cases_pattern1.items():
    content_new = content_new.replace(bq, alt)

count_after = content_new.count('<alternativeForm>')
print(f'Total alternativeForm tags (after text match): {count_after}')

with open(outputFilename, 'w') as f:
    f.write(content_new)


#(орфографически следует көзөл)
# <k>көпөмсү-</k>
# <blockquote>(вероятно, ошибочно вместо көкөмсү-)</blockquote>

# <k>күлпөт</k>
# <blockquote>(видимо, вместо үлпөт)</blockquote>
