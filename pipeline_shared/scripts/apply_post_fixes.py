#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / 'rules' / 'post_fixes.json'


def load_post_fix_rules() -> dict:
    with RULES_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: python3 apply_post_fixes.py <input.xml> <output.xml>')
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    content = input_path.read_text(encoding='utf-8')
    fixes_applied = 0
    rules = load_post_fix_rules()

    for rule in rules.get('text_replacements', []):
        flags = 0
        for flag_name in rule.get('flags', []):
            flags |= getattr(re, flag_name)
        content, count = re.subn(
            rule['pattern'],
            rule['replacement'],
            content,
            count=rule.get('count', 0),
            flags=flags,
        )
        fixes_applied += count

    output_path.write_text(content, encoding='utf-8')
    print(f'Applied {fixes_applied} post fix(es)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
