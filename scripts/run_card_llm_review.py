#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/Users/xinatanil/Sources/udahin')
INPUT_XML = ROOT / 'chatGPT_exp' / 'converted_dict.xml'
OUT_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'
DEFAULT_CARD = 'партия'
MODEL = 'gpt-5-mini'
TOKEN_RE = re.compile(r'\S+')
BLOCKQUOTE_RE = re.compile(r'<blockquote>(.*?)</blockquote>', re.S)

SCHEMA = {
    'name': 'dictionary_card_split_review',
    'schema': {
        'type': 'object',
        'properties': {
            'card_headword': {'type': 'string'},
            'notes': {'type': 'string'},
            'decisions': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'blockquote_id': {'type': 'string'},
                        'source_token_count': {'type': ['integer', 'null']},
                        'reason': {'type': 'string'},
                        'confidence': {'type': 'number'}
                    },
                    'required': ['blockquote_id', 'source_token_count', 'reason', 'confidence'],
                    'additionalProperties': False
                }
            }
        },
        'required': ['card_headword', 'notes', 'decisions'],
        'additionalProperties': False
    },
    'strict': True,
}


def extract_card_xml(headword: str) -> str:
    text = INPUT_XML.read_text(encoding='utf-8')
    m = re.search(rf'<card>\s*<k>{re.escape(headword)}</k>.*?</card>', text, re.S)
    if not m:
        raise SystemExit(f'Card not found: {headword}')
    card_xml = m.group(0)
    if card_xml.count('<blockquote>') < 5:
        raise SystemExit(f'Card has fewer than 5 blockquotes: {headword}')
    return card_xml


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


def build_prompt(card_xml: str, headword: str) -> list[dict]:
    items = iter_blockquotes(card_xml)
    enumerated = []
    for item in items:
        enumerated.append({
            'blockquote_id': item['blockquote_id'],
            'text': item['text'],
            'tokens': item['tokens'],
            'token_count': len(item['tokens']),
        })

    system = (
        'You review one XML dictionary card and split each blockquote into left side and right side. '
        'You are not allowed to copy XML or rewrite the original line. '
        'Your only job is to decide how many initial tokens belong to the left side.'
    )
    user = (
        f'Headword: {headword}\n\n'
        'Task: for every listed blockquote, decide the split point between the left side and the right side.\n\n'
        'Return one decision for every blockquote_id.\n\n'
        'Rules:\n'
        '- Set source_token_count to the number of initial tokens that belong to the left side.\n'
        '- source_token_count must be at least 1 and less than token_count if a split exists.\n'
        '- If you truly cannot identify any sensible split, set source_token_count to null.\n'
        '- Parenthetical Russian notes such as "(о больном)", "(о человеке)", "(дерево)", "(тираж)" belong to the right side.\n'
        '- Russian words like "горюя", "как", "мы", "он" do not belong in the left side.\n'
        '- If a line contains a Kyrgyz term, then meta like "собир.", then a Russian gloss, still produce the split; do not drop it.\n'
        '- Do not omit any blockquote_id.\n\n'
        'Card context:\n'
        f'{card_xml}\n\n'
        'Blockquotes to evaluate:\n'
        f'{json.dumps(enumerated, ensure_ascii=False, indent=2)}'
    )
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def call_responses_api(messages: list[dict], background: bool) -> dict:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('OPENAI_API_KEY is not set')

    payload = {
        'model': MODEL,
        'input': messages,
        'background': background,
        'text': {
            'format': {
                'type': 'json_schema',
                'name': SCHEMA['name'],
                'schema': SCHEMA['schema'],
                'strict': True,
            }
        }
    }

    req = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise SystemExit(f'HTTP {exc.code}: {body}')


def extract_output_json(response: dict) -> dict:
    if response.get('status') == 'queued':
        return {'status': 'queued', 'id': response.get('id')}
    for item in response.get('output', []):
        for content in item.get('content', []):
            if content.get('type') == 'output_text':
                return json.loads(content['text'])
    raise SystemExit('Could not find structured output in response')


def ascii_slug(headword: str) -> str:
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ү': 'u', 'ө': 'o', 'ң': 'ng', 'қ': 'k', 'һ': 'h', 'җ': 'j', 'і': 'i',
    }
    parts: list[str] = []
    for ch in headword.lower():
        if ch in mapping:
            parts.append(mapping[ch])
        elif ch.isascii() and (ch.isalnum() or ch in {'_', '-'}):
            parts.append(ch)
        else:
            parts.append('_')
    slug = ''.join(parts)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug or 'card'


def main() -> int:
    args = [a for a in sys.argv[1:] if a != '--no-background']
    headword = args[0] if args else DEFAULT_CARD
    background = '--no-background' not in sys.argv[1:]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    card_xml = extract_card_xml(headword)
    stem = f'card_{ascii_slug(headword)}'
    card_path = OUT_DIR / f'{stem}.card.xml'
    response_path = OUT_DIR / f'{stem}.response.json'
    review_path = OUT_DIR / f'{stem}.review.json'
    job_path = OUT_DIR / f'{stem}.job.json'

    card_path.write_text(card_xml + '\n', encoding='utf-8')
    response = call_responses_api(build_prompt(card_xml, headword), background=background)
    if background:
        job = {
            'card_headword': headword,
            'response_id': response.get('id'),
            'card_path': str(card_path),
            'response_path': str(response_path),
            'review_path': str(review_path),
        }
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Card XML: {card_path}')
        print(f'Background job file: {job_path}')
        print(f"Background response queued: {response.get('id')}")
        return 0

    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    review = extract_output_json(response)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Card XML: {card_path}')
    print(f'API response: {response_path}')
    print(f'Review JSON: {review_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
