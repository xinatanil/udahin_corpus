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


def convert_tail_to_meta(text: str, tail_xml: str) -> str:
    if tail_xml.startswith('<trn>'):
        inner = tail_xml[len('<trn>'):-len('</trn>')]
    else:
        inner = tail_xml[len('<blockquote>'):-len('</blockquote>')]
    return f'<meta>{inner}</meta>'


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
