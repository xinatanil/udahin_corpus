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
                        'target_starts_at_atom': {'type': ['integer', 'null']},
                        'target_first_atom': {'type': ['string', 'null']},
                        'reason': {'type': 'string'},
                        'confidence': {'type': 'number'}
                    },
                    'required': [
                        'blockquote_id',
                        'target_starts_at_atom',
                        'target_first_atom',
                        'reason',
                        'confidence',
                    ],
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
def build_prompt(card_xml: str, headword: str) -> list[dict]:
    items = iter_blockquotes(card_xml)
    enumerated = []
    for item in items:
        enumerated.append({
            'blockquote_id': item['blockquote_id'],
            'annotated_text': item['annotated_text'],
            'atoms': [{'i': idx, 'atom': atom} for idx, atom in enumerate(item['atoms'], 1)],
            'atom_count': len(item['atoms']),
        })

    system = (
        'You review one XML dictionary card and split each blockquote into left side and right side. '
        'You are not allowed to copy XML or rewrite the original line. '
        'Your only job is to decide the exact first atom that belongs to the right side. '
        'Be conservative: the left side should be the Kyrgyz expression only, and the right side should start as soon as Russian glossing, Russian meta, or Russian reference text begins. '
        'There is no downstream semantic correction. Your chosen boundary must already be correct. '
        'When in doubt, split earlier, not later.'
    )
    user = (
        f'Headword: {headword}\n\n'
        'Task: for every listed blockquote, decide the split point between the left side and the right side.\n\n'
        'Return one decision for every blockquote_id.\n\n'
        'Rules:\n'
        '- Set target_starts_at_atom to the 1-based index of the first atom that belongs to the right side.\n'
        '- target_starts_at_atom must be at least 2 and at most atom_count if a split exists.\n'
        '- If you truly cannot identify any sensible split, set target_starts_at_atom to null.\n'
        '- Also return target_first_atom exactly as it appears in the atom list. If target_starts_at_atom is null, target_first_atom must be null.\n'
        '- Atoms preserve punctuation and hyphens as separate items, so you may split before or after commas, periods, and hyphens when needed.\n'
        '- Placeholders like [[WL1|төр]] represent inline tags. Keep them on the semantically correct side of the split.\n'
        '- The left side must stay Kyrgyz. If a Russian word, Russian gloss label, or Russian explanatory fragment remains in the left side, your split is too late.\n'
        '- The right side must start with Russian gloss, Russian meta, or Russian reference text. If a Kyrgyz continuation remains at the start of the right side, your split is too early.\n'
        '- In general, the first clearly Russian atom begins the right side.\n'
        '- target_starts_at_atom must point to the first meaningful atom of the right side.\n'
        '- Usually that means the first lexical Russian atom, not delimiter punctuation such as a comma, semicolon, or dash.\n'
        '- Exception: if the right side begins with a parenthetical or quoted Russian note, target_starts_at_atom must point to the opening punctuation, for example "(" or "\\"".\n'
        '- If the source-side Kyrgyz phrase ends with sentence punctuation such as "!" or "?", and the Russian gloss starts immediately after it, the punctuation still belongs to the left side. In that case target_starts_at_atom must point to the first Russian atom after the punctuation.\n'
        '- A split directly before a comma or semicolon is highly suspicious. Do not make the first atom of the right side punctuation unless the punctuation itself is genuinely the start of the gloss, which is rare.\n'
        '- A source ending with a comma is almost always wrong. If your split would leave a trailing comma on the left side, reconsider it very carefully.\n'
        '- Rare exception: if a complete Kyrgyz term or clarified Kyrgyz phrase is followed by a comma and then a clearly Russian participial or descriptive gloss, that comma belongs to the right side, not the left.\n'
        '- A source ending with an opening parenthesis or opening quote is almost always wrong. If the right side begins with "(о ...)", "(букв. ...)" or a quoted Russian note, include the opening punctuation on the right side.\n'
        '- If the only Russian material is a bare short classifier in parentheses, such as "(конь);", "(овца);", "(птица);", and there is no real Russian gloss after it, there is usually no sensible split. In that case set target_starts_at_atom to null.\n'
        '- If the right side already contains Russian glossing, do not delay the split to a later Russian paraphrase after another comma or semicolon. The right side must start at the first Russian gloss, not the second one.\n'
        '- If the Russian gloss begins with a lexical Russian word and only then continues with a parenthetical clarification or a dash explanation, target_starts_at_atom must point to that first lexical Russian word, not to later punctuation.\n'
        '- Some tokens are homographs and can look valid in both Kyrgyz and Russian, for example "бери", "как", and sometimes "кара". Never decide from one ambiguous token alone. Decide from the shortest coherent phrase on each side.\n'
        '- If an ambiguous token appears at the start of the line and is followed by a clearly Kyrgyz sequence before the Russian gloss begins, do not treat that first token as Russian by itself.\n'
        '- If the ambiguous token is followed by clearly Russian continuation such as "не", "он", "говори", a Russian noun phrase, or another clearly Russian explanatory phrase, it belongs to the right side.\n'
        '- If moving the boundary one atom earlier turns the right side into a coherent Russian phrase and avoids leaving a dangling ambiguous token or dangling comma on the left, prefer the earlier boundary.\n'
        '- "или" by itself does not decide the boundary. It can join Kyrgyz alternatives on the left or Russian alternatives on the right.\n'
        '- If "или" is followed by a single ambiguous token that could still be a Kyrgyz alternative, and the first unambiguously Russian atom appears later, keep "или" plus that ambiguous token on the left and start the right side at the first unambiguously Russian atom.\n'
        '- Only start the right side at "или" when the phrase from "или" onward is already clearly Russian immediately, without relying on a later atom to disambiguate it.\n'
        '- Be careful with names and capitalized words. A capital letter by itself does not decide the split. Proper names can appear on either side.\n'
        '- If a Russian gloss begins with a proper name or contains a capitalized Russian personal name, that capitalized name still belongs to the right side.\n'
        '- If the left side starts with a capitalized Kyrgyz word only because it begins the sentence, that does not mean the split should start there.\n'
        '- Never leave any part of a Russian gloss on the left side, even if it is attached with a hyphen or looks short.\n'
        '- Parenthetical Russian notes such as "(о больном)", "(о человеке)", "(дерево)", "(тираж)" belong to the right side.\n'
        '- Russian words and gloss markers like "горюя", "мы", "он", "кошма", "собир.", "погов.", "фольк.", "стих." do not belong in the left side.\n'
        '- Be careful with "как": it may be Russian, but in some Kyrgyz phrases it can appear on the left side. Do not force it to the right without checking the following atoms.\n'
        '- If a line contains a Kyrgyz term, then meta like "собир.", then a Russian gloss, still produce the split; do not drop it.\n'
        '- If OCR collapsed a space, for example a source ending with a hyphen followed immediately by Russian gloss, split at the semantic boundary anyway.\n'
        '- Distinguish two dash patterns carefully. If a hyphen or spaced dash belongs to the end of the Kyrgyz side, target_starts_at_atom must point to the first Russian atom after that hyphen or dash.\n'
        '- But if a Russian gloss has the form "X - explanation", then the right side begins at X, not after the dash. Never postpone the boundary to the atom after the dash in that pattern.\n'
        '- If the Russian gloss begins with a hyphenated Russian expression such as "уходи-ка", "гляди-ка", "смотри-ка", the entire expression belongs to the right side. target_starts_at_atom must point to the first Russian word of that expression, not to the hyphen and not to the particle.\n'
        '- If the line has Kyrgyz alternatives joined by "или", keep the whole Kyrgyz alternative chain on the left until the Russian gloss begins.\n'
        '- If "или" is followed by more Kyrgyz words, keep them on the left. If "или" is followed by Russian gloss, keep "или" on the left only if it is clearly joining Kyrgyz alternatives.\n'
        '- For patterns like "см. [[WL1|...]]" or "то же, что [[WL1|...]]", that reference phrase belongs to the right side, not the left. target_starts_at_atom must point to "см" or "то".\n'
        '- Meta labels like "погов.", "фольк.", "стих.", "разг." usually belong to the right side.\n'
        '- Regional labels like "сев.", "южн.", "чатк." are special: they belong to the left side only when they clearly mark Kyrgyz variant chains.\n'
        '- Treat them as source-side variant markers only if there are at least two Kyrgyz variants in the line, or if the label is followed by another Kyrgyz variant before the Russian gloss begins.\n'
        '- A good hint is lexical similarity: regional variants are often very similar forms, differing by only a small change, for example one to three letters, while still clearly remaining Kyrgyz words.\n'
        '- If there is only one Kyrgyz form before the regional label and the label is followed directly by Russian gloss, then the regional label belongs to the right side, not the left.\n'
        '- Variant-introducing Russian adverbs such as "иногда" can behave like source-side markers if they are immediately followed by another Kyrgyz variant form before the Russian gloss begins. In that case keep "иногда" plus that Kyrgyz variant on the left.\n'
        '- If "иногда" is followed by a Kyrgyz alternative form and only then by the Russian gloss, do not split before "иногда". Split only when the actual Russian gloss begins.\n'
        '- Parenthetical clarifications such as "(авто)" may belong to the right side if they act as an explanatory gloss or classifier for the Russian translation rather than the Kyrgyz expression.\n'
        '- If a regional label is followed by one short word or exclamation and then a parenthetical Russian explanation, do not treat that short word as a second Kyrgyz variant by default. In that pattern, the gloss usually starts at the regional label.\n'
        '- Do not delay the split to "(" just because a parenthetical explanation follows. If words immediately before "(" already form a Russian gloss introduced by a regional label, the gloss starts at the regional label, not at the parenthesis.\n'
        '- If a line alternates Kyrgyz variant + regional label + Kyrgyz variant + regional label + Kyrgyz variant, keep that whole chain on the left until the actual Russian gloss begins.\n'
        '- If a regional label is immediately followed by Russian gloss and no further Kyrgyz variant, then it belongs to the right side.\n'
        '- For one-line bilingual examples, the left side is usually a complete Kyrgyz phrase or chain of Kyrgyz alternatives, and the right side is the complete Russian gloss.\n'
        '- Prefer an earlier split over an overgeneralized later split.\n'
        '- Example: atoms ["батың","барда","кете","бер","уходи","-","ка",",",...] => target_starts_at_atom = 5, target_first_atom = "уходи".\n'
        '- Example: atoms ["башыңарга","май","кайнатып","жиберейин","!","я","вас",...] => target_starts_at_atom = 6, target_first_atom = "я".\n'
        '- Example: atoms ["депкири","качып","калды","или","депкирин","таппай","калды","он","испугался",...] => target_starts_at_atom = 8, target_first_atom = "он".\n'
        '- Example: atoms ["алал","дөөлөт","-","малыңды","булгабагын","арамга","стих",".",...] => target_starts_at_atom = 7, target_first_atom = "стих".\n'
        '- Example: atoms ["казан","карма","-","готовить",...] => target_starts_at_atom = 4, target_first_atom = "готовить".\n'
        '- Example: atoms ["эл","деген","[[SPD1|-]]","казан","народа",...] => target_starts_at_atom = 4, target_first_atom = "казан". The spaced dash still belongs to the Kyrgyz side; do not delay or shift the target boundary because of it.\n'
        '- Example: atoms ["чот","как","-","щёлкать",...] => target_starts_at_atom = 4, target_first_atom = "щёлкать".\n'
        '- Example: atoms ["шак","-","шак","или","шак","-","шук","звукоподражание",...] => target_starts_at_atom = 8, target_first_atom = "звукоподражание".\n'
        '- Example: atoms ["ала","бер","бери",",","не","обращая","внимания",";"] => target_starts_at_atom = 3, target_first_atom = "бери".\n'
        '- Example: atoms ["айта","бер","говори",",","говори",";","продолжай","говорить",";"] => target_starts_at_atom = 3, target_first_atom = "говори". The Russian gloss begins at the first "говори", not later at "продолжай".\n'
        '- Example: atoms ["мени","карап","глядя","(","именно",")","на","меня",";"] => target_starts_at_atom = 3, target_first_atom = "глядя". The Russian gloss starts at the lexical word "глядя", not later at "(".\n'
        '- Example: atoms ["карап","ганатурарлык","ат","конь","[[SPD1|-]]","прямо","загляденье",";"] => target_starts_at_atom = 4, target_first_atom = "конь". This is a Russian-side dash explanation: "конь - прямо загляденье". Starting later at "прямо" is wrong.\n'
        '- Example: atoms ["кара","кесек","или","кара","мясо","(","без","жира",...] => target_starts_at_atom = 5, target_first_atom = "мясо". Here "или кара" is still the left-side alternative, and the Russian gloss begins only at the first unambiguously Russian noun "мясо". Starting at "или" is wrong.\n'
        '- Example: atoms ["как","талаада","калып",",","көзүмдөн","кара","учуп","отурат","остался","я",...] => target_starts_at_atom = 9, target_first_atom = "остался". Here line-initial "как" is part of the Kyrgyz phrase, not the start of the Russian gloss.\n'
        '- Example: atoms ["төрт","дөңгөлөгү","асманды","караган","машина","(","авто",")","машина",",","перевернувшаяся","вверх","колёсами",";"] => target_starts_at_atom = 6, target_first_atom = "(". Here "(авто) машина, перевернувшаяся вверх колёсами" belongs to the Russian gloss side, and the parenthetical clarification stays with that gloss.\n'
        '- Example: atoms ["жууган","май","сев",".",",","пышкан","май","южн",".",",","каймак","май","чатк",".","сливочное","масло",";"] => target_starts_at_atom = 15, target_first_atom = "сливочное". The regional labels stay on the left because they introduce more Kyrgyz variants.\n'
        '- Example: atoms ["кересин","май","или","сев",".","лампа","май",",","жер","май","или","южн",".","жел","май","керосин",";"] => target_starts_at_atom = 16, target_first_atom = "керосин". The regional labels and Kyrgyz variants stay on the left.\n'
        '- Example: atoms ["жаман","жер",",","иногда","жаман","жай","срамные","части",";"] => target_starts_at_atom = 7, target_first_atom = "срамные". Here "иногда жаман жай" is an alternative-form marker plus Kyrgyz variant, so it stays on the left. A split after "жер" that leaves the comma on the left is wrong.\n'
        '- Example: atoms ["май","-","май","южн",".","коли","!","(","выкрик",...] => target_starts_at_atom = 4, target_first_atom = "южн". Here "южн. коли!" is already the Russian gloss, and the parenthetical only explains it further.\n'
        '- Bad split example for the same line: target_starts_at_atom = 8 at "(" is wrong, because that would leave "южн. коли!" on the left even though it is already gloss text.\n'
        '- Example: atoms ["чүкөдөй","(","о","человеке",")","маленький",...] => target_starts_at_atom = 2, target_first_atom = "(".\n'
        '- Example: atoms ["оозу","катуу","тугоуздый","(","конь",")",";"] => target_starts_at_atom = null, target_first_atom = null, because "(конь)" is only a bare classifier and there is no real Russian gloss.\n'
        '- Example: if a line contains a Kyrgyz phrase followed by a Russian gloss mentioning a person such as "Медетбек родился в Таласе", the capitalized name "Медетбек" may belong to the right side if it is part of the Russian gloss.\n'
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
        args.append(arg)
        i += 1

    headword = args[0] if args else DEFAULT_CARD
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    card_xml = extract_card_xml(headword)
    stem = f'card_{ascii_slug(headword)}'
    card_path = ARTIFACTS_DIR / f'{stem}.card.xml'
    response_path = ARTIFACTS_DIR / f'{stem}.response.json'
    review_path = ARTIFACTS_DIR / f'{stem}.review.json'
    job_path = ARTIFACTS_DIR / f'{stem}.job.json'

    card_path.write_text(card_xml + '\n', encoding='utf-8')
    response = call_responses_api(build_prompt(card_xml, headword), background=background, model=model)
    if background:
        job = {
            'card_headword': headword,
            'model': model,
            'response_id': response.get('id'),
            'card_path': str(card_path),
            'response_path': str(response_path),
            'review_path': str(review_path),
        }
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Card XML: {card_path}')
        print(f'Background job file: {job_path}')
        print(f'Model: {model}')
        print(f"Background response queued: {response.get('id')}")
        return 0

    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    review = extract_output_json(response)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Card XML: {card_path}')
    print(f'Model: {model}')
    print(f'API response: {response_path}')
    print(f'Review JSON: {review_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
