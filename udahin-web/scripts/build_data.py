#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

HEADER_TAGS = {
    "k",
    "xr",
    "synonym",
    "alternativeForm",
    "meta",
    "origin",
    "collocationIdentifier",
}
HOMONYM_POST_META_TAGS = {
    "synonym",
    "alternativeForm",
    "meta",
    "origin",
    "xr",
    "collocationIdentifier",
}
INLINE_META_TAGS = {"meta", "origin"}
WHITESPACE_RE = re.compile(r"\s+")


def normalize_space(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text.strip())


def normalize_lookup(text: str) -> str:
    return normalize_space(text).lower()


def strip_wrapping(text: str) -> str:
    stripped = normalize_space(text)
    while stripped.startswith(("(", "[", "{")) and stripped.endswith((")", "]", "}")):
        stripped = stripped[1:-1].strip()
    return stripped


def text_content(node: ET.Element) -> str:
    return normalize_space("".join(node.itertext()))


def has_renderable_content(node: ET.Element) -> bool:
    if text_content(node):
        return True
    return any(desc.tag == "wordLink" for desc in node.iter())


def note_can_inline(node: ET.Element) -> bool:
    if node.tag not in INLINE_META_TAGS:
        return False
    text = text_content(node)
    return text.endswith(".") or text == "редко"


def entry_bucket(headword: str) -> str:
    normalized = normalize_lookup(headword)
    if not normalized:
        return "other"
    first = normalized[0]
    if first.isalnum():
        return f"u{ord(first):04x}"
    return "other"


def render_inline_children(node: ET.Element) -> str:
    parts: list[str] = []
    if node.text:
        parts.append(html.escape(node.text))
    for child in node:
        parts.append(render_inline_node(child))
        if child.tail:
            parts.append(html.escape(child.tail))
    return "".join(parts)


def render_inline_node(node: ET.Element) -> str:
    if node.tag == "wordLink":
        word = normalize_space(node.attrib.get("word", ""))
        label = normalize_space("".join(node.itertext())) or word
        href = "#" + word
        return (
            f'<a class="wordLink" href="{html.escape(href, quote=True)}" '
            f'data-headword="{html.escape(word, quote=True)}">{html.escape(label)}</a>'
        )
    return render_inline_children(node)


def render_node_content(node: ET.Element) -> str:
    if node.tag == "collocationIdentifier":
        return "(встречается преимущественно в одном или нескольких сочетаниях)"
    return render_inline_children(node)


def render_block_node(node: ET.Element) -> str:
    if node.tag == "ex":
        source = node.find("source")
        target = node.find("target")
        parts = ['<div class="ex">']
        if source is not None and has_renderable_content(source):
            parts.append(f'<div class="source">{render_node_content(source)}</div>')
        if target is not None and has_renderable_content(target):
            parts.append(f'<div class="target">{render_node_content(target)}</div>')
        parts.append("</div>")
        return "".join(parts)

    if node.tag == "miniCard":
        parts = ['<div class="miniCard">']
        for child in list(node):
            if child.tag in {"miniK", "miniTrn"} and has_renderable_content(child):
                parts.append(
                    f'<div class="{child.tag}">{render_node_content(child)}</div>'
                )
        parts.append("</div>")
        return "".join(parts)

    if not has_renderable_content(node):
        return ""

    return f'<div class="{node.tag}">{render_node_content(node)}</div>'


def render_grouped_note_sequence(nodes: list[ET.Element]) -> str:
    parts: list[str] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if note_can_inline(node):
            group = [node]
            j = i + 1
            while j < len(nodes) and note_can_inline(nodes[j]):
                group.append(nodes[j])
                j += 1
            if len(group) > 1:
                spans = []
                for idx, item in enumerate(group):
                    spans.append(
                        f'<span class="{item.tag}">{render_node_content(item)}</span>'
                    )
                    if idx != len(group) - 1:
                        spans.append('<span class="meta-separator"> • </span>')
                parts.append(f'<div class="meta-inline-group">{"".join(spans)}</div>')
            else:
                parts.append(render_block_node(node))
            i = j
        else:
            parts.append(render_block_node(node))
            i += 1
    return "".join(parts)


def render_header(nodes: list[ET.Element]) -> str:
    if not nodes or nodes[0].tag != "k":
        return ""

    parts = ['<div class="header">']
    parts.append(f"<h1>{render_node_content(nodes[0])}</h1>")
    if len(nodes) > 1:
        parts.append(render_grouped_note_sequence(nodes[1:]))
    parts.append("</div>")
    return "".join(parts)


def render_node_sequence(nodes: list[ET.Element]) -> str:
    parts: list[str] = []
    i = 0
    while i < len(nodes):
        if nodes[i].tag == "trn":
            j = i + 1
            while j < len(nodes) and nodes[j].tag != "trn":
                j += 1
            parts.append('<div class="trnSection">')
            for node in nodes[i:j]:
                parts.append(render_block_node(node))
            parts.append("</div>")
            i = j
        else:
            parts.append(render_block_node(nodes[i]))
            i += 1
    return "".join(parts)


def render_lines(nodes: list[ET.Element]) -> str:
    if not nodes:
        return ""

    parts: list[str] = []
    index = 0
    if nodes[0].tag == "k":
        header_nodes: list[ET.Element] = []
        while index < len(nodes) and nodes[index].tag in HEADER_TAGS:
            header_nodes.append(nodes[index])
            index += 1
        parts.append(render_header(header_nodes))
    parts.append(render_node_sequence(nodes[index:]))
    return "".join(parts)


def render_meaning(node: ET.Element) -> str:
    content_nodes = [child for child in list(node) if child.tag != "meaningIndex"]
    first_trn_index = next(
        (index for index, child in enumerate(content_nodes) if child.tag == "trn"),
        None,
    )

    if first_trn_index is not None:
        parts = ['<div class="meaning meaning-has-trn">']
        if first_trn_index > 0:
            parts.append('<div class="preTrnZone">')
            parts.append(render_grouped_note_sequence(content_nodes[:first_trn_index]))
            parts.append("</div>")
        parts.append('<div class="meaningMain">')
        parts.append(render_node_sequence(content_nodes[first_trn_index:]))
        parts.append("</div></div>")
        return "".join(parts)

    parts = ['<div class="meaning meaning-has-trn meaning-empty-trn">']
    parts.append('<div class="meaningMain"><div class="trnSection">')
    parts.append('<div class="emptyTrn">&nbsp;</div>')
    parts.append(render_node_sequence(content_nodes))
    parts.append("</div></div></div>")
    return "".join(parts)


def render_homonym(
    node: ET.Element,
    has_any_meanings: bool,
) -> str:
    meaning_nodes = [child for child in list(node) if child.tag == "meaning"]
    content_nodes = [
        child
        for child in list(node)
        if child.tag not in {"k", "meaning", "homonymIndex"}
    ]

    prefix_nodes: list[ET.Element] = []
    if content_nodes and content_nodes[0].tag in HOMONYM_POST_META_TAGS:
        for child in content_nodes:
            if child.tag in HOMONYM_POST_META_TAGS:
                prefix_nodes.append(child)
            else:
                break

    remaining_nodes = content_nodes[len(prefix_nodes) :]

    classes = ["homonym"]
    if len(meaning_nodes) >= 10:
        classes.append("many-meanings")
    if meaning_nodes:
        classes.append("homonym-with-meanings")

    parts = [f'<div class="{" ".join(classes)}">']
    homonym_index = node.find("homonymIndex")
    if homonym_index is not None and text_content(homonym_index):
        parts.append(
            f'<div class="homonymIndex">{html.escape(text_content(homonym_index))}</div>'
        )

    if prefix_nodes:
        parts.append('<div class="homonymPostMetaZone">')
        parts.append(render_grouped_note_sequence(prefix_nodes))
        parts.append("</div>")

    if meaning_nodes:
        for meaning in meaning_nodes:
            parts.append(render_meaning(meaning))
    else:
        if has_any_meanings:
            parts.append('<div class="homonymBody">')
            parts.append(render_lines(remaining_nodes))
            parts.append("</div>")
        else:
            parts.append(render_lines(remaining_nodes))

    parts.append("</div>")
    return "".join(parts)


def render_card(card: ET.Element) -> str:
    children = list(card)
    has_homonyms = any(child.tag == "homonym" for child in children)
    top_level_meanings = [child for child in children if child.tag == "meaning"]
    homonyms = [child for child in children if child.tag == "homonym"]

    has_any_meanings = bool(top_level_meanings) or any(
        any(grand.tag == "meaning" for grand in list(homonym)) for homonym in homonyms
    )
    shared_meaning_gutter = (
        bool(homonyms)
        and sum(
            1 for homonym in homonyms if any(child.tag == "meaning" for child in list(homonym))
        )
        >= 2
        and any(
            sum(1 for child in list(homonym) if child.tag == "meaning") >= 10
            for homonym in homonyms
        )
    )

    classes = ["entry-body"]
    if not has_homonyms and len(top_level_meanings) >= 10:
        classes.append("many-meanings")
    if has_any_meanings:
        classes.append("has-meanings")
    if shared_meaning_gutter:
        classes.append("shared-meaning-gutter")

    parts = [f'<div class="{" ".join(classes)}">']

    if has_homonyms:
        header_nodes = [
            child for child in children if child.tag not in {"homonym", "meaning"}
        ]
        parts.append(render_header(header_nodes))
        for homonym in homonyms:
            parts.append(render_homonym(homonym, has_any_meanings))
    elif top_level_meanings:
        header_nodes = [child for child in children if child.tag != "meaning"]
        parts.append(render_header(header_nodes))
        for meaning in top_level_meanings:
            parts.append(render_meaning(meaning))
    else:
        parts.append(render_lines(children))

    parts.append("</div>")
    return "".join(parts)


def collect_search_terms(card: ET.Element, headword: str) -> list[str]:
    terms = [headword]
    for node in card.iter():
        if node.tag in {"synonym", "alternativeForm"}:
            content = text_content(node)
            if content:
                terms.append(content)
                stripped = strip_wrapping(content)
                if stripped:
                    terms.append(stripped)

    seen: set[str] = set()
    normalized_terms: list[str] = []
    for term in terms:
        normalized = normalize_lookup(term)
        if normalized and normalized not in seen:
            seen.add(normalized)
            normalized_terms.append(normalized)
    return normalized_terms


def build_dataset(input_path: Path, output_dir: Path) -> None:
    tree = ET.parse(input_path)
    root = tree.getroot()

    entries_dir = output_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    for old_json in entries_dir.glob("*.json"):
        old_json.unlink()

    buckets: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    index_rows: list[dict[str, object]] = []

    for card in root.findall("card"):
        k = card.find("k")
        if k is None:
            continue

        headword = text_content(k)
        if not headword:
            continue

        bucket = entry_bucket(headword)
        html_fragment = render_card(card)
        buckets[bucket][headword] = {
            "headword": headword,
            "html": html_fragment,
        }
        index_rows.append(
            {
                "headword": headword,
                "bucket": bucket,
                "terms": collect_search_terms(card, headword),
            }
        )

    index_rows.sort(key=lambda row: normalize_lookup(str(row["headword"])))

    for bucket, entries in buckets.items():
        bucket_path = entries_dir / f"{bucket}.json"
        bucket_path.write_text(
            json.dumps({"entries": entries}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    index_payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(index_rows),
        "entries": index_rows,
    }
    (output_dir / "index.json").write_text(
        json.dumps(index_payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Build static web JSON for the Udahin dictionary site."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=root_dir / "chatGPT_exp" / "converted_dict.xml",
        help="Path to converted_dict.xml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root_dir / "udahin-web" / "site" / "data",
        help="Directory where web JSON should be written",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    build_dataset(input_path, output_dir)


if __name__ == "__main__":
    main()
