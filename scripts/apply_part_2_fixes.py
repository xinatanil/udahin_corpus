#!/usr/bin/env python3

from pathlib import Path
import re
import sys


FIXES = [
    (
        '<xr>то же, что <wordLink word="барпакта-"/></xr>',
        '<trn>(в своих движениях, в действиях);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="бултуңда-"/></xr>',
        '<trn>(но о чём-л. маленьком).</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="бултуңдат-"/></xr>',
        '<trn>(но о чём-л. маленьком).</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="быркыра-"/></xr>',
        '<trn>(но о чём-л. более мягком);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="тегирич"/></xr>',
        '<trn>(но несколько шире его и идёт сразу над ним).</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="кармаак"/></xr>',
        '<trn>(но обычно о воровстве);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="кет-" homonym="II"/></xr>',
        '<trn>(слово это встречается только в одной неприличной, но широко известной поговорке).</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="мышмыңда-"/></xr>',
        '<trn>(но в более сильной степени).</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="тирүү"/></xr>',
        '<trn>(но в отдельных сочетаниях употребляется на севере и в литературе);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="шатекте-"/></xr>',
        '<trn>(но не гуськом);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="шокшокто-"/></xr>',
        '<trn>(об одном, отдельном);</trn>',
    ),
    (
        '<xr>то же, что <wordLink word="эңиш" homonym="III"/></xr>',
        '<trn>(теперь этот вид спорта не встречается).</trn>',
    ),
    (
        '<xr>понуд. от <wordLink word="эрмеле-"/></xr>',
        '<trn>(с выпадением конечного е);</trn>',
    ),
    (
        '<xr>возвр. от <wordLink word="сөздө-"/></xr>',
        '<blockquote>(встречается только в рифме с көздөн-);</blockquote>',
    ),
]

TRN_TO_META = [
    '<trn>(только в роли вспомогательного глагола);</trn>',
    '<trn>(чаще встречается в сочет. с аке 3);</trn>',
    '<trn>лат.</trn>',
]

TRN_TO_META_AND_COLLON = [
    '<trn>(только в сочет. с жети):</trn>',
]

TRN_TO_META_AND_TRN = [
    '<trn>(только в сочет. с кылыч) обнажиться (сабля носилась без ножен и без портупеи);</trn>',
    '<trn>(чаще в сочет. с жан) успокоение, отдых;</trn>',
]

META_TRN_BLOCKQUOTE_TO_ORIGIN_TRN = [
    (
        '<meta>южн.</meta>',
        '<trn>с уйг.</trn>',
        '<blockquote>сосуд, тара (перемётная сума, мешок, ведро и т.п.).</blockquote>',
        '<origin>южн. с уйг.</origin>',
        '<trn>сосуд, тара (перемётная сума, мешок, ведро и т.п.).</trn>',
    ),
]

TRN_TO_ALTFORM = [
    '<trn>неправ. вместо авиз (см.);</trn>',
    '<trn>неправ. вместо агалы.</trn>',
    '<trn>неправ. вместо иншаалла.</trn>',
]

TRN_TO_BLOCKQUOTE = [
    '<trn>чылбырлаш бастырып (о всадниках) двигаясь рядом.</trn>',
    '<trn>чылбырын курчоого илди поводок (коня) он зацепил за верёвку юрты;</trn>',
    '<trn>абалдан или абалтан издавна, испокон веков.</trn>',
]

TRN_BLOCKQUOTE_TO_META_TRN = [
    (
        '<trn>союз</trn>',
        '<blockquote>но, однако, тем не менее.</blockquote>',
        '<meta>союз</meta>',
        '<trn>но, однако, тем не менее.</trn>',
    ),
    (
        '<trn>союз</trn>',
        '<blockquote>что; который; кто; тот, кто; то, что; тогда, когда;</blockquote>',
        '<meta>союз</meta>',
        '<trn>что; который; кто; тот, кто; то, что; тогда, когда;</trn>',
    ),
]

TRN_BLOCKQUOTE_TO_XR = [
    (
        '<trn>см.</trn>',
        '<blockquote>марш.</blockquote>',
        '<xr>см. марш.</xr>',
    ),
]

XR_REWRITES = [
    (
        '<xr>см. марш.</xr>',
        '<xr>см. <wordLink word="марш"/>.</xr>',
    ),
]

TRN_META_TO_META_TRN = [
    (
        '<trn>шахм.</trn>',
        '<meta>мат.</meta>',
        '<meta>шахм.</meta>',
        '<trn>мат.</trn>',
    ),
]

BLOCKQUOTE_TO_META = [
    '<blockquote>(обычно в сочет. с түш-)</blockquote>',
]

BLOCKQUOTE_TO_TRN = [
    '<blockquote>горячительная пища или горячительный напиток (киргизские знахари всю пищу и напитки делили на три группы: ысылык или ысык - "горячительную", сууктук или суук - "прохладительную" и мүнөз тамак "нейтральную"; напр. говядина считалась "прохладительной", конина - "горячительной", а баранина - "нейтральной", зелёный чай - "прохладительным"; в соответствии с этим и все болезни делились на ысыкчан "горячие" и суукчан "холодные"; при "горячей" болезни предписывали диету "холодную"; при "холодной"- "горячую");</blockquote>',
    '<blockquote>летосчисление по двенадцатилетнему животному циклу; название годов этого цикла в последовательном порядке: 1) чычкан мышь, 2) уй корова, 3) барс барс, 4) коён заяц, 5) улуу дракон, 6) жылан змея, 7) жылкы лошадь, 8) кой овца, 9) мечин обезьяна, 10) тоок курица, 11) ит собака, 12) доңуз свинья; в южной Киргизии распространён таджикский вариант названия годов: муш, бакар или пада, палаң, каргөш, лахаң или нахаң, мар, аспи, гаспан, хамдүйнө, мурк, сакь, кук;</blockquote>',
    '<blockquote>по пятому году (т.е. уже взрослый - о лошадях, крупном рогатом скоте, верблюдах, оленях; до четырёх лет эти животные имеют специальные названия в зависимости от возраста; после четырёх лет возраст считается по асый\'ям: жаңы асый или бир асый по пятому году, эки асый по шестому году, үч асый по седьмому году и т.д.);</blockquote>',
    '<blockquote>именное отрицание не, без (по правилам орфографии пишется с некоторыми словами слитно, напр.: бейкабар, бейопа и др., но часто встречается и раздельное написание, напр.: бей ал см. <wordLink word="бейал"/>, бей тааныш см. <wordLink word="бейтааныш"/> и др.);</blockquote>',
    '<blockquote>небольшой каменистый или песчаный склон горы без растительности; яр с отлогими берегами (в зависимости от цвета и состава породы называются различно: ак чап белый склон, көк чап синий (или зелёный) склон, кызыл чап красный склон; кумдуу чап песчаный склон и. т. п.);</blockquote>',
    '<blockquote>обычай купли родителями собственного ребёнка в целях охранения его от всякой порчи (в качестве платы дают девять предметов, имя такому ребёнку обычно даётся Тогузак Девятка или Сатыбалды Купил).</blockquote>',
    '<blockquote>форма штрафов в детской игре в чижика: бежать до назначенного места, произнося "зуу" без передышки; если одного выдыха не хватит, то оставшееся расстояние проигравший везёт выигравшего на себе;</blockquote>',
    '<blockquote>слово это известно только как название рода и в одном употребительном выражении: баланын үйү, бапанын алачыгы эмес! (здесь) не место безобразничать (букв. (это) не дом парня, не лачуга бапа).</blockquote>',
    '<blockquote>бог (употребляется вместо кудай или как парное к <wordLink word="нему"/>; иногда вместе с асман или көк);</blockquote>',
    '<blockquote>верёвка, идущая от түндүк\'а (см. <wordLink word="түндүк" meaning="3"/>) к баш босого (см. <wordLink word="босого"/>).</blockquote>',
    '<blockquote>арча, древовидный можжевельник (на юге различают два вида: өрүк арча арча с плотной крепкой древесиной и жибек арча арча с мягкой древесиной);</blockquote>',
    '<blockquote>горная ложбина (то же, что <wordLink word="салаа"/>, но глубже и с отвесными берегами, заканчивающаяся тупиком);</blockquote>',
    '<blockquote>в форме дей является первым компонентом сложных глаголов, сочетаясь с глаголами ал-, бер-, кал-, кой-, кер-, сал-, тур-, түш-;</blockquote>',
    '<blockquote>один из видов куш (см. <wordLink word="куш" homonym="I"/>; его подвиды: кара кашка тынар или кызыл кашка тынар);</blockquote>',
]

BLOCKQUOTE_TO_XR_AND_TRN = [
    (
        '<blockquote>то же, что <wordLink word="көкбөрү"/> козлодрание (конное состязание, участники которого верхом на конях вырывают друг у друга тушу козлёнка или телёнка);</blockquote>',
        '<xr>то же, что <wordLink word="көкбөрү"/></xr>',
        '<trn>козлодрание (конное состязание, участники которого верхом на конях вырывают друг у друга тушу козлёнка или телёнка);</trn>',
    ),
]

BLOCKQUOTE_TO_ALTFORM_META_META_TRN = [
    (
        '<blockquote>(иначе чач алуу) южн. этн. свадебный обычай: перед свадьбой жениху бреют голову, грудь покрывают платком, во время бритья друзья бросают в платок деньги.</blockquote>',
        '<alternativeForm>(иначе чач алуу)</alternativeForm>',
        '<meta>южн.</meta>',
        '<meta>этн.</meta>',
        '<trn>свадебный обычай: перед свадьбой жениху бреют голову, грудь покрывают платком, во время бритья друзья бросают в платок деньги.</trn>',
    ),
]


def convert_tail_to_meta(text: str, tail_xml: str) -> str:
    if tail_xml.startswith('<trn>'):
        inner = tail_xml[len('<trn>'):-len('</trn>')]
    else:
        inner = tail_xml[len('<blockquote>'):-len('</blockquote>')]
    return f'<meta>{inner}</meta>'


def retag(xml: str, new_tag: str) -> str:
    close = xml.find('>')
    inner = xml[close + 1:xml.rfind('</')]
    return f'<{new_tag}>{inner}</{new_tag}>'


def split_trn_to_meta_and_trn(trn_xml: str) -> tuple[str, str]:
    inner = trn_xml[len('<trn>'):-len('</trn>')]
    close_idx = inner.find(')')
    if close_idx == -1:
        raise ValueError(f'Cannot split trn without parenthesized prefix: {trn_xml}')
    meta_inner = inner[:close_idx + 1]
    trn_inner = inner[close_idx + 1:].lstrip()
    return f'<meta>{meta_inner}</meta>', f'<trn>{trn_inner}</trn>'


def apply_fixes(text: str) -> tuple[str, int]:
    applied = 0
    for xr_xml, tail_xml in FIXES:
        pattern = re.compile(
            rf'(^[ \t]*){re.escape(xr_xml)}\s*\n([ \t]*){re.escape(tail_xml)}',
            flags=re.M,
        )

        def repl(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{xr_xml}\n{indent}{convert_tail_to_meta(text, tail_xml)}'

        text = pattern.sub(repl, text, count=1)

    for trn_xml in TRN_TO_META:
        pattern = re.compile(rf'(^[ \t]*){re.escape(trn_xml)}', flags=re.M)

        def repl_meta(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{convert_tail_to_meta(text, trn_xml)}'

        text = pattern.sub(repl_meta, text, count=1)

    for trn_xml in TRN_TO_ALTFORM:
        pattern = re.compile(rf'(^[ \t]*){re.escape(trn_xml)}', flags=re.M)

        def repl_alt(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{retag(trn_xml, "alternativeForm")}'

        text = pattern.sub(repl_alt, text, count=1)

    for trn_xml in TRN_TO_META_AND_COLLON:
        pattern = re.compile(rf'(^[ \t]*){re.escape(trn_xml)}', flags=re.M)

        def repl_meta_collon(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            inner = trn_xml[len('<trn>'):-len('</trn>')]
            meta_inner = inner[:-1]
            return (
                f'{indent}<meta>{meta_inner}</meta>\n'
                f'{indent}<collocationIdentifier>:</collocationIdentifier>'
            )

        text = pattern.sub(repl_meta_collon, text, count=1)

    for trn_xml in TRN_TO_META_AND_TRN:
        pattern = re.compile(rf'(^[ \t]*){re.escape(trn_xml)}', flags=re.M)

        def repl_meta_trn(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            meta_xml, new_trn_xml = split_trn_to_meta_and_trn(trn_xml)
            return f'{indent}{meta_xml}\n{indent}{new_trn_xml}'

        text = pattern.sub(repl_meta_trn, text, count=1)

    for trn_xml in TRN_TO_BLOCKQUOTE:
        pattern = re.compile(rf'(^[ \t]*){re.escape(trn_xml)}', flags=re.M)

        def repl_blockquote(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{retag(trn_xml, "blockquote")}'

        text = pattern.sub(repl_blockquote, text, count=1)

    for meta_xml, trn_xml, blockquote_xml, origin_xml, new_trn_xml in META_TRN_BLOCKQUOTE_TO_ORIGIN_TRN:
        pattern = re.compile(
            rf'(^[ \t]*){re.escape(meta_xml)}\s*\n'
            rf'([ \t]*){re.escape(trn_xml)}\s*\n'
            rf'([ \t]*){re.escape(blockquote_xml)}',
            flags=re.M,
        )

        def repl_origin_trn(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{origin_xml}\n{indent}{new_trn_xml}'

        text = pattern.sub(repl_origin_trn, text, count=1)

    for trn_xml, blockquote_xml, meta_xml, new_trn_xml in TRN_BLOCKQUOTE_TO_META_TRN:
        pattern = re.compile(
            rf'(^[ \t]*){re.escape(trn_xml)}\s*\n([ \t]*){re.escape(blockquote_xml)}',
            flags=re.M,
        )

        def repl_meta_trn_pair(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{meta_xml}\n{indent}{new_trn_xml}'

        text = pattern.sub(repl_meta_trn_pair, text, count=1)

    for trn_xml, blockquote_xml, xr_xml in TRN_BLOCKQUOTE_TO_XR:
        pattern = re.compile(
            rf'(^[ \t]*){re.escape(trn_xml)}\s*\n([ \t]*){re.escape(blockquote_xml)}',
            flags=re.M,
        )

        def repl_xr_pair(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{xr_xml}'

        text = pattern.sub(repl_xr_pair, text, count=1)

    for old_xr, new_xr in XR_REWRITES:
        pattern = re.compile(rf'(^[ \t]*){re.escape(old_xr)}', flags=re.M)

        def repl_xr(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{new_xr}'

        text = pattern.sub(repl_xr, text, count=1)

    for trn_xml, meta_xml, new_meta_xml, new_trn_xml in TRN_META_TO_META_TRN:
        pattern = re.compile(
            rf'(^[ \t]*){re.escape(trn_xml)}\s*\n([ \t]*){re.escape(meta_xml)}',
            flags=re.M,
        )

        def repl_swap(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{new_meta_xml}\n{indent}{new_trn_xml}'

        text = pattern.sub(repl_swap, text, count=1)

    for blockquote_xml in BLOCKQUOTE_TO_META:
        pattern = re.compile(rf'(^[ \t]*){re.escape(blockquote_xml)}', flags=re.M)

        def repl_bq_meta(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{retag(blockquote_xml, "meta")}'

        text = pattern.sub(repl_bq_meta, text, count=1)

    for blockquote_xml in BLOCKQUOTE_TO_TRN:
        pattern = re.compile(rf'(^[ \t]*){re.escape(blockquote_xml)}', flags=re.M)

        def repl_bq_trn(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{retag(blockquote_xml, "trn")}'

        text = pattern.sub(repl_bq_trn, text, count=1)

    for blockquote_xml, xr_xml, trn_xml in BLOCKQUOTE_TO_XR_AND_TRN:
        pattern = re.compile(rf'(^[ \t]*){re.escape(blockquote_xml)}', flags=re.M)

        def repl_bq_xr_trn(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return f'{indent}{xr_xml}\n{indent}{trn_xml}'

        text = pattern.sub(repl_bq_xr_trn, text, count=1)

    for blockquote_xml, alt_xml, meta1_xml, meta2_xml, trn_xml in BLOCKQUOTE_TO_ALTFORM_META_META_TRN:
        pattern = re.compile(rf'(^[ \t]*){re.escape(blockquote_xml)}', flags=re.M)

        def repl_bq_alt_meta_meta_trn(match: re.Match[str]) -> str:
            nonlocal applied
            applied += 1
            indent = match.group(1)
            return (
                f'{indent}{alt_xml}\n'
                f'{indent}{meta1_xml}\n'
                f'{indent}{meta2_xml}\n'
                f'{indent}{trn_xml}'
            )

        text = pattern.sub(repl_bq_alt_meta_meta_trn, text, count=1)

    return text, applied


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: apply_part_2_fixes.py <input.xml> <output.xml>', file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    text = input_path.read_text(encoding='utf-8')
    new_text, applied = apply_fixes(text)
    output_path.write_text(new_text, encoding='utf-8')
    print(f'Applied {applied} part 2 fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
