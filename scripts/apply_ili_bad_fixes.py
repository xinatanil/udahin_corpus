#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path('/Users/xinatanil/Sources/udahin')
ILI_FIXES_JSON = ROOT_DIR / 'scripts' / 'data' / 'ili_bad_fixes.json'


def warn_unmatched(label: str, *parts: str) -> None:
    snippet = '\n'.join(parts)
    print(f'Warning: {label} not found:', file=sys.stderr)
    print(snippet, file=sys.stderr)


def load_entries(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    return data['entries']


def apply_fixes(xml_text: str, entries: list[dict[str, str]]) -> tuple[str, int]:

    applied = 0
    for entry in entries:
        original_source = entry['original_source']
        original_target = entry['original_target']
        fixed_source = entry['fixed_source']
        fixed_target = entry['fixed_target']
        pattern = re.compile(
            rf'(^[ \t]*)<ex>\s*\n'
            rf'([ \t]*){re.escape(original_source)}\s*\n'
            rf'([ \t]*){re.escape(original_target)}\s*\n'
            rf'([ \t]*)</ex>',
            flags=re.M,
        )

        def repl(match: re.Match[str]) -> str:
            indent = match.group(1)
            child_indent = match.group(2)
            return (
                f'{indent}<ex>\n'
                f'{child_indent}{fixed_source}\n'
                f'{child_indent}{fixed_target}\n'
                f'{indent}</ex>'
            )

        xml_text, count = pattern.subn(repl, xml_text, count=1)
        if count:
            applied += 1
        else:
            warn_unmatched('ili fix', original_source, original_target)
    return xml_text, applied


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: apply_ili_bad_fixes.py <input.xml> <output.xml>', file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    entries = load_entries(ILI_FIXES_JSON)

    xml_text = input_path.read_text(encoding='utf-8')
    xml_text, applied = apply_fixes(xml_text, entries)
    output_path.write_text(xml_text, encoding='utf-8')
    print(f'Applied {applied} ili fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
