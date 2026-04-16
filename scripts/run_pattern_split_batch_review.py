#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from ai_markdown_utils import AI_MARKDOWN_XML, merge_ai_markdown_lines
from llm_split_utils import annotate_inner_xml
from run_remaining_blockquote_llm_review import (
    build_raw_approved_line,
    call_responses_api,
    extract_output_json,
    parse_blockquote_line,
)

ROOT = Path("/Users/xinatanil/Sources/udahin")
DEFAULT_MODEL = os.environ.get("OPENAI_LLM_REVIEW_MODEL", "gpt-5")
DEFAULT_BATCH_SIZE = 20
PATTERN_MINER_DIR = ROOT / "pattern_miner"
PATTERN_REVIEW_DIR = ROOT / "pattern_review"
DEFAULT_OUT_DIR = PATTERN_REVIEW_DIR / "review_runs"
PROMPT_TEMPLATE_PATH = ROOT / "scripts" / "prompt_templates" / "pattern_001_split_prompt.txt"

SCHEMA = {
    "name": "pattern_batch_split_review_v1",
    "schema": {
        "type": "object",
        "properties": {
            "pattern_id": {"type": "string"},
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "line_id": {"type": "integer"},
                        "decision": {"type": "string", "enum": ["SPLIT", "NO_SPLIT"]},
                        "split_index": {"type": ["integer", "null"]},
                        "reason": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": ["line_id", "decision", "split_index", "reason", "confidence"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["pattern_id", "decisions"],
        "additionalProperties": False,
    },
}

def load_prompt_parts() -> tuple[str, str]:
    text = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    if not text.startswith("SYSTEM:\n") or "\n\nUSER:\n" not in text:
        raise ValueError(f"Unexpected prompt template format: {PROMPT_TEMPLATE_PATH}")
    system_part, user_part = text.split("\n\nUSER:\n", 1)
    system_prompt = system_part.removeprefix("SYSTEM:\n").strip()
    user_instructions = user_part.strip()
    return system_prompt, user_instructions


SYSTEM_PROMPT, USER_INSTRUCTIONS = load_prompt_parts()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern-file", required=True)
    parser.add_argument("--pattern-id")
    parser.add_argument("--abstract-pattern")
    parser.add_argument("--batch-index", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--name")
    return parser.parse_args()


def extract_items(pattern_file: Path) -> tuple[str | None, list[tuple[int, str]]]:
    pattern: str | None = None
    items: list[tuple[int, str]] = []
    for raw in pattern_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("pattern: "):
            pattern = line.removeprefix("pattern: ").strip()
            continue
        if not line.startswith("["):
            continue
        end = line.find("]")
        if end == -1:
            continue
        line_id = int(line[1:end])
        blockquote = line[end + 1 :].strip()
        items.append((line_id, blockquote))
    return pattern, items


def prepare_batch(pattern_file: Path, batch_index: int, batch_size: int) -> tuple[str | None, list[dict[str, Any]]]:
    pattern, raw_items = extract_items(pattern_file)
    start = (batch_index - 1) * batch_size
    batch = raw_items[start : start + batch_size]
    prepared: list[dict[str, Any]] = []
    for line_id, raw_line in batch:
        open_tag, inner_xml, close_tag = parse_blockquote_line(raw_line)
        annotated_text, placeholders = annotate_inner_xml(inner_xml)
        prepared.append(
            {
                "line_id": line_id,
                "raw_line": raw_line,
                "open_tag": open_tag,
                "inner_xml": inner_xml,
                "close_tag": close_tag,
                "annotated_text": annotated_text,
                "placeholders": placeholders,
            }
        )
    return pattern, prepared


def build_messages(pattern_id: str, abstract_pattern: str | None, items: list[dict[str, Any]]) -> list[dict[str, str]]:
    payload = {
        "pattern_id": pattern_id,
        "abstract_pattern": abstract_pattern,
        "items": [
            {"line_id": item["line_id"], "annotated_text": item["annotated_text"]}
            for item in items
        ],
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_INSTRUCTIONS
            + "\n\nPattern metadata and batch data:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n\nReturn only the structured result.",
        },
    ]


def normalize_decisions(pattern_id: str, items: list[dict[str, Any]], payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_line_id = {item["line_id"]: item for item in items}
    output: list[dict[str, Any]] = []
    decisions = payload.get("decisions", [])
    for idx, decision in enumerate(decisions):
        raw_line_id = decision.get("line_id")
        if raw_line_id is None:
            if idx >= len(items):
                continue
            item = items[idx]
            line_id = int(item["line_id"])
        else:
            line_id = int(raw_line_id)
            item = by_line_id.get(line_id)
        if item is None:
            continue
        action = decision["decision"]
        split_index = decision["split_index"]
        common = {
            "pattern_id": pattern_id,
            "line_id": line_id,
            "input": item["raw_line"],
            "annotated_text": item["annotated_text"],
            "reason": decision["reason"],
            "confidence": float(decision["confidence"]),
            "prediction": action,
        }
        if action == "NO_SPLIT" or split_index is None:
            output.append({**common, "split_index": None})
            continue
        approved_annotated, approved_line, start_char = build_raw_approved_line(item, int(split_index))
        output.append(
            {
                **common,
                "split_index": int(split_index),
                "approved_annotated": approved_annotated,
                "approved_line": approved_line,
                "start_char": start_char,
            }
        )
    seen = {record["line_id"] for record in output}
    for item in items:
        if item["line_id"] in seen:
            continue
        output.append(
            {
                "pattern_id": pattern_id,
                "line_id": item["line_id"],
                "input": item["raw_line"],
                "annotated_text": item["annotated_text"],
                "prediction": "NO_SPLIT",
                "split_index": None,
                "reason": "missing_decision",
                "confidence": 0.0,
            }
        )
    output.sort(key=lambda record: int(record["line_id"]))
    return output


def render_review(records: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for record in records:
        lines.append(f"[{record['line_id']}] {record['prediction']}")
        lines.append(f"CONFIDENCE: {record['confidence']:.3f}")
        lines.append(f"REASON: {record['reason']}")
        lines.append(f"INPUT: {record['input']}")
        if record["prediction"] == "SPLIT":
            lines.append(f"SUGGESTED: {record['approved_line']}")
        lines.append("")
    return "\n".join(lines).rstrip()


def rebuild_ai_markdown_xml(review_runs_dir: Path, output_path: Path) -> int:
    lines: list[str] = []
    for predictions_path in sorted(review_runs_dir.glob("*.predictions.jsonl")):
        for raw in predictions_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("prediction") != "SPLIT":
                continue
            approved_line = record.get("approved_line")
            if approved_line and "##" in approved_line:
                lines.append(approved_line)
    return merge_ai_markdown_lines(lines, path=output_path)


def main() -> int:
    args = parse_args()
    pattern_file = Path(args.pattern_file).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    inferred_pattern, items = prepare_batch(pattern_file, args.batch_index, args.batch_size)
    pattern_root = PATTERN_MINER_DIR.resolve()
    pattern_id = args.pattern_id or str(pattern_file.relative_to(pattern_root))
    abstract_pattern = args.abstract_pattern or inferred_pattern
    if not items:
        raise SystemExit("No items selected for this batch")

    stem = args.name or f"{pattern_file.stem}.batch{args.batch_index:02d}"
    data_path = out_dir / f"{stem}.data.json"
    prompt_path = out_dir / f"{stem}.prompt.json"
    response_path = out_dir / f"{stem}.response.json"
    predictions_path = out_dir / f"{stem}.predictions.jsonl"
    review_path = out_dir / f"{stem}.review.txt"

    data_payload = {
        "pattern_id": pattern_id,
        "abstract_pattern": abstract_pattern,
        "items": [{"line_id": item["line_id"], "annotated_text": item["annotated_text"]} for item in items],
    }
    messages = build_messages(pattern_id, abstract_pattern, items)

    data_path.write_text(json.dumps(data_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prompt_path.write_text(json.dumps(messages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    payload = {
        "model": args.model,
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
    response = call_responses_api(messages, args.model)
    response_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    normalized = normalize_decisions(pattern_id, items, extract_output_json(response))
    with predictions_path.open("w", encoding="utf-8") as fh:
        for record in normalized:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    review_path.write_text(render_review(normalized) + "\n", encoding="utf-8")
    merged_into_ai = merge_ai_markdown_lines(
        [
            record["approved_line"]
            for record in normalized
            if record.get("prediction") == "SPLIT" and record.get("approved_line")
        ],
        path=AI_MARKDOWN_XML,
    )

    print(f"Data: {data_path}")
    print(f"Prompt: {prompt_path}")
    print(f"Response: {response_path}")
    print(f"Predictions: {predictions_path}")
    print(f"Review: {review_path}")
    print(f"AI markdown XML: {AI_MARKDOWN_XML}")
    print(f"Merged into AI markdown: {merged_into_ai}")
    print(f"Items: {len(items)}")
    print(f"SPLIT: {sum(1 for record in normalized if record['prediction'] == 'SPLIT')}")
    print(f"NO_SPLIT: {sum(1 for record in normalized if record['prediction'] == 'NO_SPLIT')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
