#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from itertools import zip_longest
from pathlib import Path
from typing import Any

from llm_split_utils import annotate_inner_xml, deannotate

ROOT = Path("/Users/xinatanil/Sources/udahin")
INPUT_PATH = ROOT / "chatGPT_exp" / "all_remaining_blockquotes.txt"
OUT_DIR = ROOT / "chatGPT_exp" / "llm_blockquote_experiment"
PROMPT_CONFIG_PATH = ROOT / "scripts" / "data" / "remaining_blockquote_review_prompt.json"
DEFAULT_MODEL = os.environ.get("OPENAI_LLM_REVIEW_MODEL", "gpt-5")
DEFAULT_LIMIT = 40
DEFAULT_SEED = 47
DEFAULT_CHUNK_SIZE = 5

BLOCKQUOTE_RE = re.compile(r"^(\s*<blockquote[^>]*>)(.*?)(</blockquote>\s*)$", re.DOTALL)

SCHEMA = {
    "name": "remaining_blockquote_split_review_v1",
    "schema": {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string", "enum": ["SPLIT", "NO_SPLIT"]},
                        "split_index": {"type": ["integer", "null"]},
                        "reason": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": [
                        "decision",
                        "split_index",
                        "reason",
                        "confidence",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["decisions"],
        "additionalProperties": False,
    },
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(INPUT_PATH))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--name")
    parser.add_argument("--random-sample", action="store_true", default=True)
    parser.add_argument("--ordered", action="store_true")
    return parser.parse_args()


def chunked(items: list[dict[str, Any]], chunk_size: int) -> list[list[dict[str, Any]]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def parse_blockquote_line(raw_line: str) -> tuple[str, str, str]:
    match = BLOCKQUOTE_RE.match(raw_line)
    if not match:
        raise ValueError(f"Not a blockquote line: {raw_line!r}")
    return match.group(1), match.group(2), match.group(3)


def sample_items(args: argparse.Namespace) -> list[dict[str, Any]]:
    lines = [line.rstrip("\n") for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed = list(enumerate(lines, start=1))
    if args.offset:
        indexed = indexed[args.offset:]
    if args.ordered:
        selected = indexed[: args.limit]
    else:
        selected = random.Random(args.seed).sample(indexed, min(args.limit, len(indexed)))
    items: list[dict[str, Any]] = []
    for source_index, raw_line in selected:
        open_tag, inner_xml, close_tag = parse_blockquote_line(raw_line)
        annotated_text, placeholders = annotate_inner_xml(inner_xml)
        items.append(
            {
                "source_index": source_index,
                "blockquote_id": f"line_{source_index}",
                "raw_line": raw_line,
                "open_tag": open_tag,
                "inner_xml": inner_xml,
                "close_tag": close_tag,
                "annotated_text": annotated_text,
                "placeholders": placeholders,
            }
        )
    return items


def load_prompt_config() -> dict[str, Any]:
    return json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))


def build_prompt_for_chunk(batch_name: str, items: list[dict[str, Any]]) -> list[dict[str, str]]:
    prompt_config = load_prompt_config()
    fewshot_examples = prompt_config["fewshot_examples"]
    example_lines: list[str] = []
    for idx, example in enumerate(fewshot_examples, 1):
        annotated = example["annotated_text"]
        decision = example["decision"]
        answer = example.get("rendered_suggestion")
        example_lines.append(f"Example {idx}")
        example_lines.append(f"Annotated text: {annotated}")
        if decision == "SPLIT":
            split_index = answer.index("##")  # type: ignore[union-attr]
            example_lines.append(f"Decision: SPLIT")
            example_lines.append(f"split_index: {split_index}")
            example_lines.append(f"Rendered suggestion: {answer}")
        else:
            example_lines.append("Decision: NO_SPLIT")
            example_lines.append("split_index: null")
            example_lines.append("Rendered suggestion: NO_SPLIT")
        example_lines.append("")

    sections: list[str] = []
    for idx, item in enumerate(items, 1):
        sections.append(f"{idx}. {item['annotated_text']}")

    user = (
        prompt_config["user_instructions"]
        + "\n\nExamples:\n"
        + "\n".join(example_lines)
        + "\nBlockquotes to review in order:\n\n"
        + "\n\n".join(sections)
        + "\n\nReturn only the structured result."
    )
    return [
        {"role": "system", "content": prompt_config["system_prompt"]},
        {"role": "user", "content": user},
    ]


def call_responses_api(messages: list[dict[str, str]], model: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set")

    payload = {
        "model": model,
        "input": messages,
        "text": {
            "format": {
                "type": "json_schema",
                "name": SCHEMA["name"],
                "schema": SCHEMA["schema"],
                "strict": True,
            }
        },
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"HTTP {exc.code}: {body}")
        except (urllib.error.URLError, ConnectionResetError, TimeoutError) as exc:
            last_error = exc
            if attempt == 2:
                break
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"API request failed after retries: {last_error}")


def extract_output_json(response: dict[str, Any]) -> dict[str, Any]:
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return json.loads(content["text"])
    raise SystemExit("Could not find structured output in response")


def build_raw_approved_line(item: dict[str, Any], split_index: int) -> tuple[str, str, int]:
    annotated = item["annotated_text"]
    while 0 < split_index <= len(annotated) and annotated[split_index - 1].isspace():
        split_index -= 1
    approved_annotated = annotated[:split_index] + "##" + annotated[split_index:]
    raw_approved_inner = deannotate(approved_annotated, item["placeholders"])
    raw_approved_line = f"{item['open_tag']}{raw_approved_inner}{item['close_tag']}"
    if raw_approved_line.replace("##", "", 1) != item["raw_line"]:
        raise ValueError("Approved line does not match original raw line after removing ##")
    raw_inner = raw_approved_inner
    raw_start_char = raw_inner.index("##")
    return approved_annotated, raw_approved_line, raw_start_char


def normalize_decisions(payload: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item, decision in zip_longest(items, payload.get("decisions", []), fillvalue=None):
        if item is None:
            break
        if decision is None:
            output.append(
                {
                    "index": item["source_index"],
                    "blockquote_id": item["blockquote_id"],
                    "input": item["raw_line"],
                    "annotated_text": item["annotated_text"],
                    "prediction": "NO_SPLIT",
                    "reason": "missing_decision",
                    "confidence": 0.0,
                }
            )
            continue
        blockquote_id = item["blockquote_id"]
        action = decision["decision"]
        split_index = decision["split_index"]
        reason = decision["reason"]
        confidence = float(decision["confidence"])
        if action == "NO_SPLIT":
            output.append(
                {
                    "index": item["source_index"],
                    "blockquote_id": blockquote_id,
                    "input": item["raw_line"],
                    "annotated_text": item["annotated_text"],
                    "prediction": "NO_SPLIT",
                    "reason": reason,
                    "confidence": confidence,
                }
            )
            continue
        if split_index is None:
            output.append(
                {
                    "index": item["source_index"],
                    "blockquote_id": blockquote_id,
                    "input": item["raw_line"],
                    "annotated_text": item["annotated_text"],
                    "prediction": "NO_SPLIT",
                    "reason": f"invalid_split_index: {reason}",
                    "confidence": confidence,
                }
            )
            continue
        if split_index < 0 or split_index >= len(item["annotated_text"]):
            output.append(
                {
                    "index": item["source_index"],
                    "blockquote_id": blockquote_id,
                    "input": item["raw_line"],
                    "annotated_text": item["annotated_text"],
                    "prediction": "NO_SPLIT",
                    "reason": f"out_of_range_split_index: {reason}",
                    "confidence": confidence,
                }
            )
            continue

        try:
            approved_annotated, approved_line, raw_start_char = build_raw_approved_line(item, split_index)
        except Exception as exc:  # noqa: BLE001
            output.append(
                {
                    "index": item["source_index"],
                    "blockquote_id": blockquote_id,
                    "input": item["raw_line"],
                    "annotated_text": item["annotated_text"],
                    "prediction": "NO_SPLIT",
                    "reason": f"render_failure: {reason} ({exc})",
                    "confidence": confidence,
                }
            )
            continue

        output.append(
            {
                "index": item["source_index"],
                "blockquote_id": blockquote_id,
                "input": item["raw_line"],
                "annotated_text": item["annotated_text"],
                "prediction": "SPLIT",
                "start_char": raw_start_char,
                "split_index": split_index,
                "approved_annotated_text": approved_annotated,
                "approved_line": approved_line,
                "reason": reason,
                "confidence": confidence,
            }
        )
    output.sort(key=lambda rec: int(rec["index"]))
    return output


def render_review(records: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for record in records:
        lines.append(f"[{record['index']}] {record['prediction']}")
        lines.append(f"CONFIDENCE: {record.get('confidence', 0.0):.3f}")
        lines.append(f"REASON: {record.get('reason', '')}")
        lines.append(f"INPUT: {record['input']}")
        if record["prediction"] == "SPLIT":
            lines.append(f"SUGGESTED: {record['approved_line']}")
        lines.append("")
    return "\n".join(lines)


def default_stem(args: argparse.Namespace) -> str:
    mode = "ordered" if args.ordered else f"seed{args.seed}"
    model_slug = args.model.replace("/", "_")
    return f"remaining_{mode}_n{args.limit}_{model_slug}"


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    items = sample_items(args)
    batch_name = args.name or default_stem(args)
    sample_path = OUT_DIR / f"{batch_name}.sample.json"
    response_path = OUT_DIR / f"{batch_name}.response.json"
    predictions_path = OUT_DIR / f"{batch_name}.predictions.jsonl"
    review_path = OUT_DIR / f"{batch_name}.review.txt"

    sample_path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Sample: {sample_path}")
    print(f"Model: {args.model}")
    print(f"Items: {len(items)}")
    print(f"Chunk size: {args.chunk_size}")

    chunks = chunked(items, args.chunk_size)
    raw_responses: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    run_started_at = time.perf_counter()
    for chunk_idx, chunk in enumerate(chunks, 1):
        chunk_started_at = time.perf_counter()
        print(
            f"Request {chunk_idx}/{len(chunks)} "
            f"(items {len(chunk)}, elapsed {time.perf_counter() - run_started_at:.1f}s)",
            flush=True,
        )
        response = call_responses_api(build_prompt_for_chunk(batch_name, chunk), model=args.model)
        chunk_elapsed = time.perf_counter() - chunk_started_at
        print(f"Completed chunk {chunk_idx}/{len(chunks)} in {chunk_elapsed:.1f}s", flush=True)
        raw_responses.append(
            {
                "chunk_index": chunk_idx,
                "blockquote_ids": [item["blockquote_id"] for item in chunk],
                "elapsed_seconds": round(chunk_elapsed, 3),
                "response": response,
            }
        )
        payload = extract_output_json(response)
        records.extend(normalize_decisions(payload, chunk))

    response_path.write_text(json.dumps(raw_responses, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with predictions_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    review_path.write_text(render_review(records) + "\n", encoding="utf-8")

    split_count = sum(1 for record in records if record["prediction"] == "SPLIT")
    nosplit_count = sum(1 for record in records if record["prediction"] == "NO_SPLIT")
    print(f"Responses: {response_path}")
    print(f"Predictions: {predictions_path}")
    print(f"Review: {review_path}")
    print(f"SPLIT: {split_count}")
    print(f"NO_SPLIT: {nosplit_count}")
    print(f"Total elapsed: {time.perf_counter() - run_started_at:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
