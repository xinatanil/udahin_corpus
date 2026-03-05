import re
import sys
from collections import defaultdict
from constants import metaWord, originWord

metaOrOriginWord = f"(?:{metaWord}|{originWord})"
metaOrOriginPattern = re.compile(rf"^(?:{metaOrOriginWord}[ \t]*)+:$")

# Lines ending with ':' that are NOT collocations (skip them)
COLON_ENDING_EXCEPTIONS = [
	'(в народе их делили на несколько групп, придавая каждой из них свой эпитет:',
	'(в эпосе, когда речь ведётся от лица монгола или калмыка; ср. жабуу III):',
	'ист. батыр (предводитель военной дружины, прославившийся своей храбростью или военным искусством; обычно свою деятельность батыр начинал с угона чужого скота, что считалось молодечеством; батыры в народе делились на шесть категорий:',
	'ист. сев. манап (представитель верхушки киргизской феодально-родовой знати, который, не имея личной собственности, жил за счёт управляемого им населения и распоряжался его собственностью; одни манапы управляли несколькими родами, племенами, а другие - только частью волости; поэтому по значимости манапы делились на несколько категорий:'
]

# Lines ending with ':' that are confirmed collocations (checked against PDF)
COLON_ENDING_CHECKED = [
	'(в сочет. с орой или арай):',
	'(вместо катыр, хатыр):',
	'(вместо пороз):',
	'(встречается только с киргизским аффиксом мн. ч.):',
	'(встречено только в отриц. форме):',
	'(деги эле; см. деги, эле I):',
	'(или ай-ий или айиий или эмфатически ай-и-и-й) возглас удивления или сожаления:',
	'(или кам тагана, кам такана):',
	'(обычно в сочет. с түш-):',
	'(от г. Ирбит, Ирбитская ярмарка):',
	'(см. кыйгач):',
	'(см. сөөк 2):',
	'(ср. акыш I, акуш):',
	'(ср. каз. куралай горная коза):',
	'(ср. кемтик):',
	'(ср. кой- II):',
	'(ср. кур IV):',
	'(ср. көйүт-):',
	'(ср. монг. хурган ягнёнок):',
	'(ср. олбуш-):',
	'(ср. олой-):',
	'(ср. соёчор):',
	'(ср. тарт-):',
	'(ср. тат. күкай):',
	'(ср. таң I, таңда):',
	'(ср. тогуз 2):',
	'(ср. тув. оона самец косули, сайги, монг. самец антилопы):',
	'(ср. тырмак):',
	'(ср. ыдык):',
	'(только в деепр. прош. вр.):',
	'(только в соединении с увакыт или көңүл):',
	'(только в сочет. с жети):',
	'(только в сочет. с той):',
	'(только в сочет. с урун-; ср. тат., башк. бэр):',
	'(только в форме чечкедей):',
	'(только с числительным бир):',
	', ири:',
	'алагар, алагай:',
	'арык уйга жоон мүйүздүн кереги жок погов. тощей корове большие рога не нужны (они её не украсят):',
	'баакы II:',
	'бирин (бир-ин):',
	'богоздо-, богузда-:',
	'бурчактык, буурчактык:',
	'в выражениях сожаления, досады:',
	'(ср. тат. күкәй):',
	'в сочет. с ай, көк, асман, ава:',
	'деепр. от кайтар-:',
	'и. д. от ийлен-:',
	'итатай, итетай:',
	'ичме, ичмей:',
	'кебеже, кебежи:',
	'келече, келеч:',
]

# Lines ending with ':' that are questionable collocations (not sure if they are collocations)
COLON_ENDING_QUESTIONABLE = [
	'2) (в стихах для аллитерации иногда) то же, что көк муштум:',
	'2) большие и малые (по общественному положению):',
	'2) выражает побуждение:',
	'3) при условной форме выражает сожаление:',
	'ай-ий, уят-ай! ай, какой стыд!:',
	'актан сыздаган шордуу бедняжка, пострадавшая без вины:',
	'алма бурак запах яблока, яблочный запах:',
	'арпа кер жаак болуп калды ячмень вот-вот поспеет:',
	'бери бак- обычно в отриц. обороте:',
	'беш убак намаз пять уставных молитв:',
	'бутунун башы менен на цыпочках:',
	'в знач. утверждения при отриц. форме:',
	'в исх. п. и с притяж. аффиксом 3 л.:',
	'в роли вспомогательного глагола с деепр. наст. вр. выражает:',
	'в роли вспомогательного глагола:',
	'взаимн. от жай- V:',
	'выемка, впадина; дыра:',
	'жыргатам дедиң эле, кайта азабыңды тарттырып отурасың ты обещал мне усладу, а (теперь), наоборот, доставляешь мучение:',
	'жүнү тайкы короткошёрстный:',
	'калтар чач см. калтар:',
	'канаттууга кактыр- только в отриц. обороте:',
	'напрасно, зря, попусту:',
]

# Lines with ':' in the middle that are NOT collocations (skip them)
COLON_OTHER_EXCEPTIONS = [
]

input_file = sys.argv[1] if len(sys.argv) > 1 else '/Users/xinatanil/Sources/udahin/sources/corrected_source_dict.xml'


def is_content_line(line):
    """Check if a line has actual content (not just bare XML tags like </card>, <card>, etc.)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Pure opening/closing tags with no text content
    if re.match(r'^</?[a-zA-Z0-9_]+>$', stripped):
        return False
    return True


def gather_context(lines, match_idx, n_before=3, n_after=3):
    """
    Gather n content lines before and after match_idx, skipping bare tag lines.
    Returns a list of lines including the match line.
    """
    # Gather content lines before
    before = []
    j = match_idx - 1
    while len(before) < n_before and j >= 0:
        if is_content_line(lines[j]):
            before.append(lines[j])
        j -= 1
    before.reverse()

    # Gather content lines after
    after = []
    j = match_idx + 1
    while len(after) < n_after and j < len(lines):
        if is_content_line(lines[j]):
            after.append(lines[j])
        j += 1

    return before + [lines[match_idx]] + after


ending_with_colon = []
rest_by_tag = defaultdict(list)

with open(input_file, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f]

def is_proven_collocation_ending(tag, content):
    """Check if this colon-ending line is a proven collocation that doesn't need review."""
    text = content.strip()
    # <k> tags ending with ':' are always collocations
    if tag == 'k' and text.endswith(':'):
        return True
    # metaOrOrigin patterns (e.g. "ар. южн.:") are always collocations
    if metaOrOriginPattern.match(text):
        return True
    # Lines ending with ']:' are always collocations
    if text.endswith(']:'):
        return True
    return False


def is_proven_collocation_other(tag, content, lines, line_idx):
    """Check if this mid-colon line is a proven collocation that doesn't need review."""
    text = content.strip()
    # <blockquote> starting with keyword from preceding <k> and ending with ':'
    if tag == 'blockquote' and text.endswith(':'):
        # Look for a preceding <k> tag to get the keyword
        for j in range(line_idx - 1, max(line_idx - 5, -1), -1):
            k_match = re.match(r'^<k>(.*?)</k>$', lines[j])
            if k_match:
                keyword = k_match.group(1).strip()
                if keyword and text.startswith(keyword) and text.endswith(':'):
                    return True
                break
    # <blockquote> starting with "keyword: " (keyword from preceding <k>)
    if tag == 'blockquote':
        for j in range(line_idx - 1, max(line_idx - 5, -1), -1):
            k_match = re.match(r'^<k>(.*?)</k>$', lines[j])
            if k_match:
                keyword = k_match.group(1).strip()
                if keyword and text.startswith(keyword + ': '):
                    return True
                break
    return False


def is_colon_ending_exception(content):
    """Check if this line is a known exception (not a collocation)."""
    return content.strip() in COLON_ENDING_EXCEPTIONS


def is_colon_ending_already_reviewed(content):
    """Check if this line was already manually reviewed (checked or questionable)."""
    text = content.strip()
    return text in COLON_ENDING_CHECKED or text in COLON_ENDING_QUESTIONABLE


def is_colon_other_exception(content):
    """Check if this mid-colon line is a known exception (not a collocation)."""
    return content.strip() in COLON_OTHER_EXCEPTIONS


for i, line in enumerate(lines):
    match = re.match(r'^<([a-zA-Z0-9_]+)>(.*:.*)</\1>$', line)
    if match:
        tag = match.group(1)
        content = match.group(2).strip()

        context_lines = gather_context(lines, i)
        # Format: match line first, then --- separator, then full context
        combined_block = line + "\n---\n" + "\n".join(context_lines)

        if content.endswith(':'):
            if is_colon_ending_exception(content) or is_proven_collocation_ending(tag, content) or is_colon_ending_already_reviewed(content):
                continue
            ending_with_colon.append(combined_block)
        else:
            if is_colon_other_exception(content) or is_proven_collocation_other(tag, content, lines, i):
                continue
            rest_by_tag[tag].append(combined_block)

def sort_key(block):
    """Sort by match line text (first line of block), alphabetically."""
    first_line = block.split('\n')[0]
    # Strip XML tags for clean sorting
    text = re.sub(r'<[^>]+>', '', first_line).strip().lower()
    return text


with open('/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_ending_with_colon.txt', 'w', encoding='utf-8') as f:
    for block in sorted(ending_with_colon, key=sort_key):
        f.write(block + '\n\n\n')

with open('/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_ending_with_colon_lines.txt', 'w', encoding='utf-8') as f:
    for block in sorted(ending_with_colon, key=sort_key):
        f.write(block.split('\n', 1)[0] + '\n')

for tag, blocks_list in rest_by_tag.items():
    with open(f'/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_rest_{tag}.txt', 'w', encoding='utf-8') as f:
        for block in sorted(blocks_list, key=sort_key):
            f.write(block + '\n\n\n')
    with open(f'/Users/xinatanil/Sources/udahin/chatGPT_exp/tags_rest_{tag}_lines.txt', 'w', encoding='utf-8') as f:
        for block in sorted(blocks_list, key=sort_key):
            f.write(block.split('\n', 1)[0] + '\n')
