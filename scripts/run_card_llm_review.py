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
MODEL = 'gpt-5.4'

SCHEMA = {
    'name': 'dictionary_card_example_review',
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
                        'blockquote_xml': {'type': 'string'},
                        'is_example': {'type': 'boolean'},
                        'leading_meta': {'type': ['string', 'null']},
                        'source': {'type': ['string', 'null']},
                        'target': {'type': ['string', 'null']},
                        'reason': {'type': 'string'},
                        'confidence': {'type': 'number'}
                    },
                    'required': ['blockquote_xml', 'is_example', 'leading_meta', 'source', 'target', 'reason', 'confidence'],
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
    return m.group(0)


def build_prompt(card_xml: str, headword: str) -> list[dict]:
    system = (
        'You review one XML dictionary card and classify each direct <blockquote> in that card as either an example '
        'or not an example. Be conservative, but do not miss clear example lines. '
        'An example usually has Kyrgyz text on the left and Russian text on the right in the same blockquote. '
        'If it is an example, split it into source and target. Do not invent text. Copy the original blockquote XML exactly.'
    )
    user = (
        f'Headword: {headword}\n\n'
        'Task: inspect this one card and evaluate each direct <blockquote> inside it.\n\n'
        'Mark is_example=true only when the blockquote is best understood as an example sentence or expression with '
        'Kyrgyz material on the left and Russian translation/explanation on the right.\n\n'
        'Important guidance:\n'
        '- Look for a split between Kyrgyz on the left and Russian on the right.\n'
        '- Many examples contain Kyrgyz function words, verb forms ending in "-", or full Kyrgyz clauses before the Russian gloss.\n'
        '- If a blockquote begins with a short Russian-style label such as "разг.", "фольк.", "полит.", "перен." and the rest is still an example, put that label into leading_meta instead of source or target.\n'
        '- Do not leave Kyrgyz text in target if it belongs on the left side of the split.\n'
        '- Do not classify pure definitions, meta notes, xr lines, or glosses without a left/right bilingual split as examples.\n'
        '- If a line is an example, fill source and target exactly, and set leading_meta if needed.\n'
        '- If it is not an example, set leading_meta, source and target to null.\n'
        '- Evaluate every direct blockquote you see in the card.\n\n'
        f'{card_xml}'
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
    headword = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CARD
    background = '--background' in sys.argv[2:] or '--background' in sys.argv[1:]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    card_xml = extract_card_xml(headword)
    safe = re.sub(r'[^0-9A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі_-]+', '_', headword)
    ascii_safe = f'card_{ascii_slug(headword)}'
    card_path = OUT_DIR / f'{safe}.card.xml'
    response_path = OUT_DIR / f'{safe}.response.json'
    review_path = OUT_DIR / f'{safe}.review.json'
    ascii_card_path = OUT_DIR / f'{ascii_safe}.card.xml'
    ascii_response_path = OUT_DIR / f'{ascii_safe}.response.json'
    ascii_review_path = OUT_DIR / f'{ascii_safe}.review.json'

    card_path.write_text(card_xml + '\n', encoding='utf-8')
    ascii_card_path.write_text(card_xml + '\n', encoding='utf-8')
    response = call_responses_api(build_prompt(card_xml, headword), background=background)
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ascii_response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    review = extract_output_json(response)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ascii_review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'Card XML: {card_path}')
    print(f'API response: {response_path}')
    print(f'Review JSON: {review_path}')
    print(f'ASCII card XML: {ascii_card_path}')
    print(f'ASCII API response: {ascii_response_path}')
    print(f'ASCII review JSON: {ascii_review_path}')
    if isinstance(review, dict) and review.get('status') == 'queued':
        print(f"Background response queued: {review.get('id')}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
