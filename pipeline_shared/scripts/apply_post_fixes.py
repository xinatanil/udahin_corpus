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


def should_apply_rule(rule: dict, mode: str) -> bool:
    stage = rule.get('stage', 'late')
    if mode == 'all':
        return True
    if mode == 'pre_trn':
        return stage == 'pre_trn'
    if mode == 'post_homonym':
        return stage == 'post_homonym'
    raise ValueError(f'Unknown mode: {mode}')


def main() -> int:
    args = sys.argv[1:]
    mode = 'all'
    if len(args) >= 2 and args[0] == '--mode':
        if len(args) < 4:
            print('Usage: python3 apply_post_fixes.py [--mode all|pre_trn|post_homonym] <input.xml> <output.xml>')
            return 1
        mode = args[1]
        args = args[2:]

    if len(args) < 2:
        print('Usage: python3 apply_post_fixes.py [--mode all|pre_trn|post_homonym] <input.xml> <output.xml>')
        return 1
    if mode not in {'all', 'pre_trn', 'post_homonym'}:
        print('Mode must be one of: all, pre_trn, post_homonym')
        return 1

    input_path = Path(args[0])
    output_path = Path(args[1])

    content = input_path.read_text(encoding='utf-8')
    fixes_applied = 0
    rules = load_post_fix_rules()

    for rule in rules.get('text_replacements', []):
        if not should_apply_rule(rule, mode):
            continue
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
    print(f'Applied {fixes_applied} post fix(es) [{mode}]')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
