#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EX_BLOCK_RE = re.compile(r'<ex>\s*<source>(.*?)</source>\s*<target>(.*?)</target>\s*</ex>', re.S)


def already_has_equivalent_example(xml_text: str, replace_with_xml: str) -> bool:
    m = EX_BLOCK_RE.search(replace_with_xml)
    if not m:
        return replace_with_xml in xml_text
    source = m.group(1)
    target = m.group(2)
    for src, tgt in EX_BLOCK_RE.findall(xml_text):
        if src == source and tgt == target:
            return True
    return False


def apply_fix_set(xml_text: str, fixes: list[dict], source_name: str) -> tuple[str, int]:
    applied = 0
    for fix in fixes:
        if fix.get('action') != 'replace_exact_xml':
            continue
        find_xml = fix['find_xml']
        replace_with_xml = fix['replace_with_xml']

        if already_has_equivalent_example(xml_text, replace_with_xml):
            continue

        pattern = re.compile(rf'(^[ \t]*){re.escape(find_xml)}', flags=re.M)

        def repl(match: re.Match[str]) -> str:
            nonlocal applied
            indent = match.group(1)
            repl_xml = replace_with_xml.replace('\n', '\n' + indent)
            applied += 1
            return f'{indent}{repl_xml}'

        xml_text, count = pattern.subn(repl, xml_text, count=1)
        if count == 0:
            print(f'Warning: [{source_name}] exact XML not found: {find_xml[:120]}', file=sys.stderr)
    return xml_text, applied


def main() -> int:
    if len(sys.argv) != 4:
        print('Usage: apply_approved_llm_fixes.py <input.xml> <approved_dir> <output.xml>', file=sys.stderr)
        return 1

    input_xml = Path(sys.argv[1])
    approved_dir = Path(sys.argv[2])
    output_xml = Path(sys.argv[3])

    xml_text = input_xml.read_text(encoding='utf-8')
    total_applied = 0

    if approved_dir.exists():
        for fix_file in sorted(approved_dir.glob('*.json')):
            payload = json.loads(fix_file.read_text(encoding='utf-8'))
            xml_text, applied = apply_fix_set(xml_text, payload.get('fixes', []), fix_file.name)
            total_applied += applied

    output_xml.write_text(xml_text, encoding='utf-8')
    print(f'Applied {total_applied} approved LLM fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
