#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path('/Users/xinatanil/Sources/udahin')
APPROVED_DIR = ROOT / 'chatGPT_exp' / 'approved_llm_fixes'
CONVERT = ROOT / 'scripts' / 'convert_card_review_to_fixes.py'
APPLY = ROOT / 'scripts' / 'apply_card_review_fixes.py'
XML = ROOT / 'chatGPT_exp' / 'converted_dict.xml'
EXPERIMENT_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'


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
    patched_path = EXPERIMENT_DIR / f'{stem}.patched.xml'
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ['python3', str(CONVERT), str(review_path), str(fixes_path)],
        check=True,
    )
    subprocess.run(
        ['python3', str(APPLY), str(XML), str(fixes_path), str(patched_path)],
        check=True,
    )

    dest = APPROVED_DIR / fixes_path.name
    shutil.copy2(fixes_path, dest)
    print(f'Promoted fixes to {dest}')
    print(f'Patched preview written to {patched_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
