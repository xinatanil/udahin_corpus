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

from llm_split_utils import iter_blockquotes

ROOT = Path('/Users/xinatanil/Sources/udahin')
CONVERT = ROOT / 'scripts' / 'convert_card_review_to_fixes.py'
APPLY = ROOT / 'scripts' / 'apply_card_review_fixes.py'
REVIEW_DIR = ROOT / 'chatGPT_exp' / 'llm_card_experiment'
ARTIFACTS_DIR = REVIEW_DIR / 'artifacts'
RUSSIAN_CLUE_WORDS = {
    'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они', 'не', 'как', 'кто',
    'что', 'это', 'этот', 'эта', 'эти', 'то', 'же', 'см', 'дорожный',
    'заставить', 'готовить', 'народ', 'народа', 'великое', 'множество',
}
RUSSIAN_META_RE = re.compile(r'\((?:о|об|букв\.?|разг\.?|фольк\.?|погов\.?|собир\.?|этн\.?|поэт\.?|прост\.?)', re.I)
REFERENCE_RE = re.compile(r'\bсм\.|\bто же,? что\b', re.I)
RUSSIAN_UNIQUE_RE = re.compile(r'[ыэёъ]')
SOURCE_ENDS_COMMA_RE = re.compile(r',\s*$')
SOURCE_BAD_HYPHEN_PAREN_RE = re.compile(r'\s-\(')
SOURCE_BAD_HYPHEN_ILI_RE = re.compile(r'-или\b', re.I)
SOURCE_BAD_HYPHEN_CLOSE_RE = re.compile(r'\s-\)')


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


def pretty_xml_snippet(xml: str) -> list[str]:
    text = xml.strip()
    if not text:
        return []
    text = re.sub(r'>\s*<', '>\n<', text)
    lines = [line.rstrip() for line in text.splitlines()]
    return lines


def make_fix_review_diff(fixes_payload: dict) -> str:
    lines: list[str] = []
    for idx, fix in enumerate(fixes_payload.get('fixes', []), 1):
        lines.append(f'@@ fix {idx} @@')
        for line in pretty_xml_snippet(fix["find_xml"]):
            lines.append(f'- {line}')
        for line in pretty_xml_snippet(fix["replace_with_xml"]):
            lines.append(f'+ {line}')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def strip_tags(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def suspicious_remaining_reason(inner_xml: str) -> str | None:
    plain = strip_tags(inner_xml).strip()
    if not plain:
        return None
    if REFERENCE_RE.search(plain):
        return 'reference phrase remained in blockquote'
    if RUSSIAN_META_RE.search(plain):
        return 'Russian parenthetical/meta remained in blockquote'
    atoms = re.findall(r"[A-Za-zА-Яа-яЁёҮүӨөҢңҚқҺһҖҗІі'-]+|[^\w\s]", plain, re.UNICODE)
    for idx, atom in enumerate(atoms):
        low = atom.lower().strip('.,;:!?')
        if not low:
            continue
        if idx >= 1 and (low in RUSSIAN_CLUE_WORDS or RUSSIAN_UNIQUE_RE.search(low)):
            return f'possible Russian gloss starts near "{atom}"'
    return None


def write_remaining_blockquote_report(patched_card_path: Path, stem: str) -> Path | None:
    warn_path = REVIEW_DIR / f'warn_{stem}.remaining_blockquotes.txt'
    patched_card = patched_card_path.read_text(encoding='utf-8')
    items = []
    for item in iter_blockquotes(patched_card):
        reason = suspicious_remaining_reason(item['inner_xml'])
        if reason:
            items.append((item['blockquote_id'], reason, item['blockquote_xml']))
    if not items:
        if warn_path.exists():
            warn_path.unlink()
        return None
    lines = ['Potentially suspicious remaining blockquotes:\n']
    for bq_id, reason, blockquote_xml in items:
        lines.append(f'- {bq_id}: {reason}')
        lines.append(f'  {blockquote_xml}')
        lines.append('')
    warn_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    return warn_path


def suspicious_source_reason(source_text: str) -> str | None:
    source = strip_tags(source_text).strip()
    if not source:
        return None
    if SOURCE_ENDS_COMMA_RE.search(source):
        return 'source ends with comma'
    if SOURCE_BAD_HYPHEN_PAREN_RE.search(source):
        return 'source has malformed "-(" spacing'
    if SOURCE_BAD_HYPHEN_ILI_RE.search(source):
        return 'source has malformed "-или" spacing'
    if SOURCE_BAD_HYPHEN_CLOSE_RE.search(source):
        return 'source has malformed "-)" spacing'
    return None


def write_suspicious_fix_report(fixes_payload: dict, stem: str) -> Path | None:
    warn_path = REVIEW_DIR / f'warn_{stem}.suspicious_fixes.txt'
    items = []
    for idx, fix in enumerate(fixes_payload.get('fixes', []), 1):
        replace_xml = fix.get('replace_with_xml', '')
        m = re.search(r'<source>(.*?)</source>', replace_xml, re.S)
        if not m:
            continue
        reason = suspicious_source_reason(m.group(1))
        if reason:
            items.append((idx, reason, replace_xml))
    if not items:
        if warn_path.exists():
            warn_path.unlink()
        return None
    lines = ['Potentially suspicious reconstructed fixes:\n']
    for idx, reason, replace_xml in items:
        lines.append(f'- fix {idx}: {reason}')
        for line in pretty_xml_snippet(replace_xml):
            lines.append(f'  {line}')
        lines.append('')
    warn_path.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    return warn_path


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


def build_preview(review_path: Path, previous_patched_text: str | None = None) -> tuple[Path, Path, Path, Path, Path | None, Path | None, Path | None]:
    stem = review_path.name.removesuffix('.review.json')
    card_path = review_path.parent / f'{stem}.card.xml'
    fixes_path = review_path.parent / f'{stem}.approved_fixes.json'
    patched_card_path = review_path.parent / f'{stem}.patched_card.xml'
    diff_path = REVIEW_DIR / f'diff_{stem}.review.diff'
    fix_diff_path = REVIEW_DIR / f'diff_fix_{stem}.review.diff'
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
    fixes_payload = json.loads(fixes_path.read_text(encoding='utf-8'))
    fix_diff_path.write_text(make_fix_review_diff(fixes_payload), encoding='utf-8')
    warn_path = write_remaining_blockquote_report(patched_card_path, stem)
    suspicious_fix_warn_path = write_suspicious_fix_report(fixes_payload, stem)
    if previous_patched_text is not None:
        iter_diff_text = make_unified_diff(
            previous_patched_text,
            patched_card,
            f'{stem}.prev_patched_card.xml',
            f'{stem}.patched_card.xml',
        )
        iter_diff_path.write_text(iter_diff_text, encoding='utf-8')
    return fixes_path, patched_card_path, diff_path, fix_diff_path, (iter_diff_path if previous_patched_text is not None else None), warn_path, suspicious_fix_warn_path


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
    fix_diff_path = REVIEW_DIR / f'diff_fix_{stem}.review.diff'
    iter_diff_path = REVIEW_DIR / f'diff_iter_{stem}.review.diff'
    warn_path = REVIEW_DIR / f'warn_{stem}.remaining_blockquotes.txt'
    suspicious_fix_warn_path = REVIEW_DIR / f'warn_{stem}.suspicious_fixes.txt'
    previous_patched_text = patched_card_path.read_text(encoding='utf-8').strip() if patched_card_path.exists() else None
    archive_previous_iteration(
        stem,
        [response_path, review_path, fixes_path, patched_card_path, diff_path, fix_diff_path, iter_diff_path, warn_path, suspicious_fix_warn_path],
    )
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    card_xml = Path(job['card_path']).read_text(encoding='utf-8')
    blockquote_count = count_blockquotes(card_xml)
    decision_count = len(review.get('decisions', []))
    if decision_count != blockquote_count:
        print(f"Warning: blockquote/decision count mismatch for {job['card_headword']}: {blockquote_count} blockquotes vs {decision_count} decisions")
    fixes_path, patched_card_path, diff_path, fix_diff_path, latest_iter_diff, latest_warn_path, latest_suspicious_fix_warn_path = build_preview(review_path, previous_patched_text=previous_patched_text)
    print(f'Response JSON: {response_path}')
    print(f'Review JSON: {review_path}')
    print(f'Approved fixes preview JSON: {fixes_path}')
    print(f'Patched card preview XML: {patched_card_path}')
    print(f'Review diff: {diff_path}')
    print(f'Fix review diff: {fix_diff_path}')
    if latest_iter_diff is not None:
        print(f'Iteration diff: {latest_iter_diff}')
    if latest_warn_path is not None:
        print(f'Suspicious remaining blockquotes: {latest_warn_path}')
    if latest_suspicious_fix_warn_path is not None:
        print(f'Suspicious reconstructed fixes: {latest_suspicious_fix_warn_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
