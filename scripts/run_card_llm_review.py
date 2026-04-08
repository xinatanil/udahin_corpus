#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from llm_split_utils import iter_blockquotes

ROOT = Path('/Users/xinatanil/Sources/udahin')
INPUT_XML = ROOT / 'chatGPT_exp' / 'converted_dict.xml'
OUT_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'
ARTIFACTS_DIR = OUT_DIR / 'artifacts'
DEFAULT_CARD = 'партия'
DEFAULT_MODEL = 'gpt-5-mini'
DEFAULT_CHUNK_SIZE = 10

SCHEMA = {
    'name': 'dictionary_blockquote_chunk_split_review',
    'schema': {
        'type': 'object',
        'properties': {
            'card_headword': {'type': 'string'},
            'decisions': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'blockquote_id': {'type': 'string'},
                        'target_starts_at_char': {'type': ['integer', 'null']},
                        'target_starts_with': {'type': ['string', 'null']},
                        'reason': {'type': 'string'},
                        'confidence': {'type': 'number'},
                    },
                    'required': [
                        'blockquote_id',
                        'target_starts_at_char',
                        'target_starts_with',
                        'reason',
                        'confidence',
                    ],
                    'additionalProperties': False,
                },
            },
        },
        'required': [
            'card_headword',
            'decisions',
        ],
        'additionalProperties': False,
    },
    'strict': True,
}


def make_index_guide(text: str) -> str:
    tens = ''.join(str((idx // 10) % 10) for idx, _ in enumerate(text))
    ones = ''.join(str(idx % 10) for idx, _ in enumerate(text))
    return f'tens: {tens}\nones: {ones}'


def chunked(items: list[dict[str, object]], chunk_size: int) -> list[list[dict[str, object]]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def extract_card_xml(headword: str) -> str:
    text = INPUT_XML.read_text(encoding='utf-8')
    m = re.search(rf'<card>\s*<k>{re.escape(headword)}</k>.*?</card>', text, re.S)
    if not m:
        raise SystemExit(f'Card not found: {headword}')
    card_xml = m.group(0)
    if card_xml.count('<blockquote>') < 5:
        raise SystemExit(f'Card has fewer than 5 blockquotes: {headword}')
    return card_xml


def build_prompt_for_chunk(headword: str, items: list[dict[str, object]]) -> list[dict[str, str]]:
    sections: list[str] = []
    for item in items:
        annotated_text = item['annotated_text']
        blockquote_id = item['blockquote_id']
        index_guide = make_index_guide(annotated_text)
        sections.append(
            f'blockquote_id: {blockquote_id}\n'
            'Annotated text:\n'
            f'{annotated_text}\n'
            'Character index guide:\n'
            f'{index_guide}'
        )
    system = (
        'You review a small batch of annotated Kyrgyz-Russian dictionary blockquotes. '
        'For each blockquote, your only job is to decide the exact 0-based character index where the Russian/right side starts. '
        'Do not rewrite the text. Do not normalize punctuation. Do not invent text. '
        'The left side must stay a complete Kyrgyz expression, and the right side must start at the earliest coherent Russian gloss, Russian meta, or Russian reference.'
    )
    user = (
        f'Headword: {headword}\n'
        f'Blockquote count: {len(items)}\n\n'
        'Decision procedure:\n'
        '1. Keep the shortest complete Kyrgyz expression on the left.\n'
        '2. Start the right side at the earliest point where a coherent Russian gloss, Russian meta note, or Russian reference already begins.\n'
        '3. If Russian material remains on the left, the split is too late.\n'
        '4. If a Kyrgyz continuation remains at the start of the right side, the split is too early.\n\n'
        'Rules:\n'
        '- Return one decision for every listed blockquote_id.\n'
        '- For each blockquote, return target_starts_at_char as a 0-based character index into that blockquote\'s Annotated text.\n'
        '- Also return target_starts_with: the exact first 8 to 16 characters of the right side as they appear in Annotated text, or the full right side if shorter. If target_starts_at_char is null, target_starts_with must be null.\n'
        '- If there is no sensible split, return null.\n'
        '- The index must point to the first non-space character of the right side.\n'
        '- The index must not point inside a placeholder such as [[WL1|...]] or [[SPD1|-]].\n'
        '- In most lines the right side begins at the first lexical Russian word.\n'
        '- If the right side begins with a separate Russian parenthetical or quoted note, point to the opening punctuation.\n'
        '- If a lexical Russian word already appears before a later parenthetical or dash explanation, the right side begins at that lexical word, not later.\n'
        '- The source must not end with a comma, opening parenthesis, or opening quote.\n'
        '- The target must not start with a comma.\n'
        '- If a Russian parenthetical note like (о человеке), (о раскосом человеке), (там), (даже), or (букв. ...) appears between the Kyrgyz phrase and the rest of the Russian gloss, that parenthetical belongs to the right side.\n'
        '- But a parenthetical variant marker such as (вместо тай жеңе), where the parenthesis introduces another Kyrgyz form rather than Russian gloss text, belongs to the left side together with the Kyrgyz expression.\n'
        '- If the only Russian material is a bare classifier like (конь); and there is no real gloss after it, return null.\n'
        '- Keep Kyrgyz alternative chains on the left, including chains joined by или, иногда, or regional labels, until the Russian gloss really begins.\n'
        '- If или is followed by a single ambiguous token that could still be Kyrgyz, and the first unambiguously Russian word appears later, start the right side at that later Russian word.\n'
        '- Some words are ambiguous and can look valid on either side, for example кара, как, бери, рекорд. Do not decide from one ambiguous token alone; decide from the shortest coherent phrase.\n'
        '- If a repeated bridge noun still belongs naturally to the Kyrgyz side, keep it on the left and start the Russian gloss at the first clearly Russian adjective or explanatory phrase that follows.\n'
        '- If a Russian gloss has the form X - explanation, the right side begins at X, not after the dash.\n'
        '- Prefer the earliest boundary that yields a coherent Russian phrase without leaving Russian material on the left.\n\n'
        'Examples:\n'
        '- жоого ант жок врагу клятвы нет (...) -> right side starts at "в" in "врагу".\n'
        '- көзү бар или көзү тирүү (о человеке) живой, здравствующий; -> right side starts at "(".\n'
        '- бир көзүн аса, бир көзүн баса караган неме (о раскосом человеке) у него один глаз ... -> right side starts at "(".\n'
        '- көзгө басар жалгыз боз үй жок эле (там) не было ни одной юрты ... -> right side starts at "(".\n'
        '- тамактан көзү каткан он (так голоден, что) ... -> right side starts at "о" in "он".\n'
        '- көзү жок баатыр или көзү жок эр бесстрашный или бесшабашный молодец ... -> right side starts at "б" in "бесстрашный".\n'
        '- көз көрбөгөн рекорд невиданный рекорд; -> right side starts at "н" in "невиданный".\n'
        '- караңгы түндө көз тапкан (даже) ночью находящий ... -> right side starts at "(".\n'
        '- Манастын көрөр көзү - Каныкей любимая Манаса - Каныкей; -> right side starts at "л" in "любимая".\n'
        '- көз байланган кез сумерки, начало вечерней темноты; -> right side starts at "с" in "сумерки".\n'
        '- кара кесек или кара мясо (...) -> right side starts at "м" in "мясо".\n'
        '- карап ганатурарлык ат конь - прямо загляденье; -> right side starts at "к" in "конь".\n\n'
        '- таажеңе (вместо тай жеңе) старшая родственница матери ... -> right side starts at "с" in "старшая"; the parenthetical stays on the left because it names a Kyrgyz alternative form.\n\n'
        'Blockquotes to review:\n\n'
        + '\n\n'.join(sections)
        + '\n\nReturn only the structured result.'
    )
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user},
    ]


def call_responses_api(messages: list[dict], background: bool, model: str) -> dict:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('OPENAI_API_KEY is not set')

    payload = {
        'model': model,
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
    raw_args = sys.argv[1:]
    background = True
    model = os.environ.get('OPENAI_LLM_REVIEW_MODEL', DEFAULT_MODEL)
    chunk_size = DEFAULT_CHUNK_SIZE
    args: list[str] = []
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg == '--no-background':
            background = False
            i += 1
            continue
        if arg == '--model':
            if i + 1 >= len(raw_args):
                raise SystemExit('--model requires a value')
            model = raw_args[i + 1]
            i += 2
            continue
        if arg == '--chunk-size':
            if i + 1 >= len(raw_args):
                raise SystemExit('--chunk-size requires a value')
            chunk_size = int(raw_args[i + 1])
            if chunk_size <= 0:
                raise SystemExit('--chunk-size must be positive')
            i += 2
            continue
        args.append(arg)
        i += 1

    headword = args[0] if args else DEFAULT_CARD
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    card_xml = extract_card_xml(headword)
    items = iter_blockquotes(card_xml)
    chunks = chunked(items, chunk_size)
    stem = f'card_{ascii_slug(headword)}'
    card_path = ARTIFACTS_DIR / f'{stem}.card.xml'
    response_path = ARTIFACTS_DIR / f'{stem}.response.json'
    review_path = ARTIFACTS_DIR / f'{stem}.review.json'
    job_path = ARTIFACTS_DIR / f'{stem}.job.json'

    card_path.write_text(card_xml + '\n', encoding='utf-8')

    if background:
        responses = []
        for idx, chunk in enumerate(chunks, 1):
            response = call_responses_api(build_prompt_for_chunk(headword, chunk), background=True, model=model)
            responses.append({
                'chunk_index': idx,
                'blockquote_ids': [item['blockquote_id'] for item in chunk],
                'response_id': response.get('id'),
            })
        job = {
            'schema_version': 'char_split_chunk_v1',
            'card_headword': headword,
            'model': model,
            'chunk_size': chunk_size,
            'responses': responses,
            'card_path': str(card_path),
            'response_path': str(response_path),
            'review_path': str(review_path),
        }
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Card XML: {card_path}')
        print(f'Background job file: {job_path}')
        print(f'Model: {model}')
        print(f'Chunk size: {chunk_size}')
        print(f'Queued {len(responses)} chunk request(s) for {len(items)} blockquotes')
        return 0

    raw_responses = []
    decisions = []
    for idx, chunk in enumerate(chunks, 1):
        response = call_responses_api(build_prompt_for_chunk(headword, chunk), background=False, model=model)
        raw_responses.append({
            'chunk_index': idx,
            'blockquote_ids': [item['blockquote_id'] for item in chunk],
            'response': response,
        })
        chunk_review = extract_output_json(response)
        decisions.extend(chunk_review.get('decisions', []))

    response_path.write_text(json.dumps(raw_responses, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    review = {
        'card_headword': headword,
        'notes': f'Char-index review, up to {chunk_size} blockquotes per request.',
        'decisions': decisions,
    }
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Card XML: {card_path}')
    print(f'Model: {model}')
    print(f'API response: {response_path}')
    print(f'Review JSON: {review_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
