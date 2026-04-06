#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def ex_xml(source: str, target: str) -> str:
    return (
        '<ex>\n'
        f'\t<source>{source}</source>\n'
        f'\t<target>{target}</target>\n'
        '</ex>'
    )


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: convert_card_review_to_fixes.py <review.json> <approved_fixes.json>', file=sys.stderr)
        return 1

    review_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    data = json.loads(review_path.read_text(encoding='utf-8'))

    fixes = []
    for decision in data.get('decisions', []):
        if not decision.get('is_example'):
            continue
        source = decision.get('source')
        target = decision.get('target')
        if not source or not target:
            continue
        fixes.append({
            'action': 'replace_exact_xml',
            'find_xml': decision['blockquote_xml'],
            'replace_with_xml': ex_xml(source, target),
            'reason': decision.get('reason', ''),
            'confidence': decision.get('confidence', 0),
        })

    out = {
        'card_headword': data.get('card_headword'),
        'source_review_file': str(review_path),
        'fixes': fixes,
    }
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(fixes)} approved fix(es) to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
