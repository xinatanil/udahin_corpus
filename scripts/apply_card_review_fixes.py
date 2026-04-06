#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def apply_fixes(xml_text: str, fixes: list[dict]) -> tuple[str, int]:
    applied = 0
    for fix in fixes:
        find_xml = fix['find_xml']
        replace_with_xml = fix['replace_with_xml']
        pattern = re.compile(rf'(^[ \t]*){re.escape(find_xml)}', flags=re.M)

        def repl(match: re.Match[str]) -> str:
            nonlocal applied
            indent = match.group(1)
            repl_xml = replace_with_xml.replace('\n', '\n' + indent)
            applied += 1
            return f'{indent}{repl_xml}'

        xml_text, count = pattern.subn(repl, xml_text, count=1)
        if count == 0:
            print(f'Warning: exact blockquote not found for fix: {find_xml[:120]}', file=sys.stderr)
    return xml_text, applied


def main() -> int:
    if len(sys.argv) != 4:
        print('Usage: apply_card_review_fixes.py <input.xml> <approved_fixes.json> <output.xml>', file=sys.stderr)
        return 1

    input_xml = Path(sys.argv[1])
    fixes_json = Path(sys.argv[2])
    output_xml = Path(sys.argv[3])

    xml_text = input_xml.read_text(encoding='utf-8')
    payload = json.loads(fixes_json.read_text(encoding='utf-8'))
    new_text, applied = apply_fixes(xml_text, payload.get('fixes', []))
    output_xml.write_text(new_text, encoding='utf-8')
    print(f'Applied {applied} reviewed fix(es) to {output_xml}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
