#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOKEN_RE = re.compile(r'\S+')
BLOCKQUOTE_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.S)
TRAILING_RUSSIAN_WORDS = {
    'горюя', 'как', 'будто', 'словно', 'точно', 'погов', 'фольк', 'собир',
    'мы', 'он', 'она', 'они', 'оно', 'это', 'этот', 'эта', 'эти',
}


def iter_blockquotes(card_xml: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for idx, m in enumerate(BLOCKQUOTE_RE.finditer(card_xml), 1):
        inner = m.group(1).strip()
        xml = m.group(0)
        text = re.sub(r'<[^>]+>', '', inner)
        tokens = TOKEN_RE.findall(text)
        items.append({
            'blockquote_id': f'bq_{idx}',
            'blockquote_xml': xml,
            'text': text,
            'tokens': tokens,
        })
    return items


def normalize_split(source: str, target: str) -> tuple[str, str]:
    s = source.strip()
    t = target.strip()
    if not s or not t:
        return s, t
    while True:
        m = re.search(r'^(?P<body>.*?)(?:\s+)(?P<tail>[А-Яа-яЁё-]+[,:;.]?)$', s)
        if not m:
            break
        tail = m.group('tail')
        key = tail.strip('.,:;!?"«»„').lower()
        if key not in TRAILING_RUSSIAN_WORDS:
            break
        s = m.group('body').rstrip()
        t = f'{tail} {t}'.strip()
    return s, t


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
    card_path = review_path.with_name(review_path.name.removesuffix('.review.json') + '.card.xml')
    if not card_path.exists():
        raise SystemExit(f'Card XML not found: {card_path}')

    data = json.loads(review_path.read_text(encoding='utf-8'))
    card_xml = card_path.read_text(encoding='utf-8')
    blockquotes = {item['blockquote_id']: item for item in iter_blockquotes(card_xml)}

    fixes = []
    seen_ids: set[str] = set()
    for decision in data.get('decisions', []):
        bq_id = decision.get('blockquote_id')
        if not bq_id or bq_id in seen_ids:
            continue
        seen_ids.add(bq_id)
        item = blockquotes.get(bq_id)
        if not item:
            continue
        source_token_count = decision.get('source_token_count')
        tokens = item['tokens']
        if source_token_count is None:
            continue
        if not isinstance(source_token_count, int):
            continue
        if source_token_count <= 0 or source_token_count >= len(tokens):
            continue
        source = ' '.join(tokens[:source_token_count])
        target = ' '.join(tokens[source_token_count:])
        source, target = normalize_split(source, target)
        if not source or not target:
            continue
        fixes.append({
            'action': 'replace_exact_xml',
            'find_xml': item['blockquote_xml'],
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
