#!/usr/bin/env python3
from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/Users/xinatanil/Sources/udahin')
CONVERT = ROOT / 'scripts' / 'convert_card_review_to_fixes.py'
APPLY = ROOT / 'scripts' / 'apply_card_review_fixes.py'
XML = ROOT / 'chatGPT_exp' / 'converted_dict.xml'


def fetch_response(response_id: str) -> dict:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('OPENAI_API_KEY is not set')
    req = urllib.request.Request(
        f'https://api.openai.com/v1/responses/{response_id}',
        headers={'Authorization': f'Bearer {api_key}'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise SystemExit(f'HTTP {exc.code}: {body}')


def extract_output_json(response: dict) -> dict | None:
    if response.get('status') in {'queued', 'in_progress'}:
        return None
    for item in response.get('output', []):
        for content in item.get('content', []):
            if content.get('type') == 'output_text':
                return json.loads(content['text'])
    raise SystemExit('Could not find structured output in response')


def extract_headword(review_path: Path) -> str:
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


def build_preview(review_path: Path) -> tuple[Path, Path, Path]:
    stem = review_path.name.removesuffix('.review.json')
    fixes_path = review_path.parent / f'{stem}.approved_fixes.json'
    patched_card_path = review_path.parent / f'{stem}.patched_card.xml'
    diff_path = review_path.parent / f'diff_{stem}.review.diff'
    tmp_xml = review_path.parent / f'{stem}.tmp.xml'

    subprocess.run(['python3', str(CONVERT), str(review_path), str(fixes_path)], check=True)
    subprocess.run(['python3', str(APPLY), str(XML), str(fixes_path), str(tmp_xml)], check=True)

    headword = extract_headword(review_path)
    original_card = extract_card(XML.read_text(encoding='utf-8'), headword)
    patched_card = extract_card(tmp_xml.read_text(encoding='utf-8'), headword)
    patched_card_path.write_text(patched_card + '\n', encoding='utf-8')

    diff_text = ''.join(difflib.unified_diff(
        (original_card + '\n').splitlines(keepends=True),
        (patched_card + '\n').splitlines(keepends=True),
        fromfile=f'{stem}.card.xml',
        tofile=f'{stem}.patched_card.xml',
    ))
    diff_path.write_text(diff_text, encoding='utf-8')
    tmp_xml.unlink()
    return fixes_path, patched_card_path, diff_path


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: fetch_card_llm_review.py <job.json>', file=sys.stderr)
        return 1

    job_path = Path(sys.argv[1]).resolve()
    if not job_path.exists():
        print(f'Job file not found: {job_path}', file=sys.stderr)
        return 1

    job = json.loads(job_path.read_text(encoding='utf-8'))
    response = fetch_response(job['response_id'])

    response_path = Path(job['response_path'])
    review_path = Path(job['review_path'])
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    review = extract_output_json(response)
    if review is None:
        print(f"Still running: {response.get('id')} ({response.get('status')})")
        return 0

    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fixes_path, patched_card_path, diff_path = build_preview(review_path)
    print(f'Response JSON: {response_path}')
    print(f'Review JSON: {review_path}')
    print(f'Approved fixes preview JSON: {fixes_path}')
    print(f'Patched card preview XML: {patched_card_path}')
    print(f'Review diff: {diff_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
