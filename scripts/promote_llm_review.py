#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import re
from pathlib import Path

ROOT = Path('/Users/xinatanil/Sources/udahin')
APPROVED_DIR = ROOT / 'chatGPT_exp' / 'approved_llm_fixes'
CONVERT = ROOT / 'scripts' / 'convert_card_review_to_fixes.py'
APPLY = ROOT / 'scripts' / 'apply_card_review_fixes.py'
XML = ROOT / 'chatGPT_exp' / 'converted_dict.xml'
EXPERIMENT_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'


def extract_headword(review_path: Path) -> str:
    import json
    data = json.loads(review_path.read_text(encoding='utf-8'))
    headword = data.get('card_headword')
    if not headword:
        raise SystemExit(f'card_headword missing in {review_path}')
    return headword


def extract_card(text: str, headword: str) -> str:
    m = re.search(rf'<card>\s*<k>{re.escape(headword)}</k>.*?</card>', text, re.S)
    if not m:
        raise SystemExit(f'Card not found in XML: {headword}')
    return m.group(0)


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: promote_llm_review.py <review.json>', file=sys.stderr)
        return 1

    review_path = Path(sys.argv[1]).resolve()
    if not review_path.exists():
        print(f'Review file not found: {review_path}', file=sys.stderr)
        return 1

    stem = review_path.name.removesuffix('.review.json')
    fixes_path = EXPERIMENT_DIR / f'{stem}.approved_fixes.json'
    patched_card_path = EXPERIMENT_DIR / f'{stem}.patched_card.xml'
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ['python3', str(CONVERT), str(review_path), str(fixes_path)],
        check=True,
    )
    subprocess.run(
        ['python3', str(APPLY), str(XML), str(fixes_path), str(EXPERIMENT_DIR / f'{stem}.tmp.xml')],
        check=True,
    )

    headword = extract_headword(review_path)
    tmp_xml = (EXPERIMENT_DIR / f'{stem}.tmp.xml')
    patched_card = extract_card(tmp_xml.read_text(encoding='utf-8'), headword)
    patched_card_path.write_text(patched_card + '\n', encoding='utf-8')
    tmp_xml.unlink()

    dest = APPROVED_DIR / fixes_path.name
    shutil.copy2(fixes_path, dest)
    print(f'Promoted fixes to {dest}')
    print(f'Patched card preview written to {patched_card_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
