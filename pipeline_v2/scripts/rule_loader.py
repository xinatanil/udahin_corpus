from __future__ import annotations

import json
from pathlib import Path


RULES_DIR = Path(__file__).resolve().parents[1] / 'rules'


def load_rule_lines(filename: str) -> list[str]:
    path = RULES_DIR / filename
    with path.open('r', encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f if line.rstrip('\n')]


def load_rule_json(filename: str):
    path = RULES_DIR / filename
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)
