#!/usr/bin/env python3
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path('/Users/xinatanil/Sources/udahin')
CONVERT = ROOT / 'scripts' / 'convert_card_review_to_fixes.py'
APPLY = ROOT / 'scripts' / 'apply_card_review_fixes.py'
REVIEW_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'
ARTIFACTS_DIR = REVIEW_DIR / 'artifacts'


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


def count_blockquotes(card_xml: str) -> int:
    return len(re.findall(r'<blockquote>.*?</blockquote>', card_xml, re.S))


def make_unified_diff(old_text: str, new_text: str, old_name: str, new_name: str) -> str:
    return ''.join(difflib.unified_diff(
        (old_text + '\n').splitlines(keepends=True),
        (new_text + '\n').splitlines(keepends=True),
        fromfile=old_name,
        tofile=new_name,
    ))


def history_dir_for(stem: str) -> Path:
    return ARTIFACTS_DIR / 'history' / stem


def archive_previous_iteration(stem: str, paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    base = history_dir_for(stem)
    base.mkdir(parents=True, exist_ok=True)
    nums = []
    for child in base.iterdir():
        m = re.fullmatch(r'iter_(\d+)', child.name)
        if m:
            nums.append(int(m.group(1)))
    target = base / f'iter_{(max(nums) + 1) if nums else 1:03d}'
    target.mkdir(parents=True, exist_ok=False)
    for path in existing:
        shutil.copy2(path, target / path.name)
    return target


def build_preview(review_path: Path, previous_patched_text: str | None = None) -> tuple[Path, Path, Path, Path | None]:
    stem = review_path.name.removesuffix('.review.json')
    card_path = review_path.parent / f'{stem}.card.xml'
    fixes_path = review_path.parent / f'{stem}.approved_fixes.json'
    patched_card_path = review_path.parent / f'{stem}.patched_card.xml'
    diff_path = REVIEW_DIR / f'diff_{stem}.review.diff'
    iter_diff_path = REVIEW_DIR / f'diff_iter_{stem}.review.diff'

    subprocess.run(['python3', str(CONVERT), str(review_path), str(fixes_path)], check=True)
    subprocess.run(['python3', str(APPLY), str(card_path), str(fixes_path), str(patched_card_path)], check=True)

    original_card = card_path.read_text(encoding='utf-8').strip()
    patched_card = patched_card_path.read_text(encoding='utf-8').strip()

    diff_text = make_unified_diff(
        original_card,
        patched_card,
        f'{stem}.card.xml',
        f'{stem}.patched_card.xml',
    )
    diff_path.write_text(diff_text, encoding='utf-8')
    if previous_patched_text is not None:
        iter_diff_text = make_unified_diff(
            previous_patched_text,
            patched_card,
            f'{stem}.prev_patched_card.xml',
            f'{stem}.patched_card.xml',
        )
        iter_diff_path.write_text(iter_diff_text, encoding='utf-8')
    return fixes_path, patched_card_path, diff_path, (iter_diff_path if previous_patched_text is not None else None)


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: fetch_card_llm_review.py <job.json>', file=sys.stderr)
        return 1

    job_path = Path(sys.argv[1]).resolve()
    if not job_path.exists():
        print(f'Job file not found: {job_path}', file=sys.stderr)
        return 1

    job = json.loads(job_path.read_text(encoding='utf-8'))
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    response = fetch_response(job['response_id'])
    review = extract_output_json(response)
    if review is None:
        print(f"Still running: {response.get('id')} ({response.get('status')})")
        return 0

    stem = Path(job['review_path']).name.removesuffix('.review.json')
    response_path = Path(job['response_path'])
    review_path = Path(job['review_path'])
    fixes_path = review_path.parent / f'{stem}.approved_fixes.json'
    patched_card_path = review_path.parent / f'{stem}.patched_card.xml'
    diff_path = REVIEW_DIR / f'diff_{stem}.review.diff'
    iter_diff_path = REVIEW_DIR / f'diff_iter_{stem}.review.diff'
    previous_patched_text = patched_card_path.read_text(encoding='utf-8').strip() if patched_card_path.exists() else None
    archive_previous_iteration(
        stem,
        [response_path, review_path, fixes_path, patched_card_path, diff_path, iter_diff_path],
    )
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    card_xml = Path(job['card_path']).read_text(encoding='utf-8')
    blockquote_count = count_blockquotes(card_xml)
    decision_count = len(review.get('decisions', []))
    if decision_count != blockquote_count:
        print(f"Warning: blockquote/decision count mismatch for {job['card_headword']}: {blockquote_count} blockquotes vs {decision_count} decisions")
    fixes_path, patched_card_path, diff_path, latest_iter_diff = build_preview(review_path, previous_patched_text=previous_patched_text)
    print(f'Response JSON: {response_path}')
    print(f'Review JSON: {review_path}')
    print(f'Approved fixes preview JSON: {fixes_path}')
    print(f'Patched card preview XML: {patched_card_path}')
    print(f'Review diff: {diff_path}')
    if latest_iter_diff is not None:
        print(f'Iteration diff: {latest_iter_diff}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
