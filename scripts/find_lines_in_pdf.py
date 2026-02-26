#!/usr/bin/env python3
"""
Find lines from a text file in an OCRed PDF, take screenshots,
and pair them as lineN.txt + lineN.png in an output directory.

Usage:
    python scripts/find_lines_in_pdf.py sources/tags_rest_blockquote.txt \
        --output-dir results/blockquote_results \
        --pdf sources/udahin_ocred_kyr_rus.pdf
"""

import argparse
import os
import re
import sys
import difflib
import random

import fitz  # PyMuPDF


# Letters that OCR doesn't recognize well in Kyrgyz
BAD_OCR_CHARS = set("өүңӨҮҢ")

# Russian-only Cyrillic letters (not shared with Kyrgyz-specific chars)
RUSSIAN_CYRILLIC = set("абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯёЁ")

# All Cyrillic letters
ALL_CYRILLIC = set("абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯёЁөүңӨҮҢ")


def parse_input_block(block_text):
    """
    Parse a block from the input file.
    Format: match_line\n---\ncontext_line1\ncontext_line2\n...
    Or legacy format: just lines (no --- separator).

    Returns (primary_text, context_texts_list).
    - primary_text: text from the match line (the one we're searching for)
    - context_texts: list of ALL blockquote/k texts in the context (for search help)
    """
    block_text = block_text.strip()
    if not block_text:
        return None, []

    # Split on --- separator
    if "\n---\n" in block_text:
        match_part, context_part = block_text.split("\n---\n", 1)
        match_lines = [match_part.strip()]
        context_lines = context_part.strip().split("\n")
    else:
        # Legacy format: all lines are both match and context
        match_lines = [block_text.strip().split("\n")[0]]
        context_lines = block_text.strip().split("\n")

    # Extract primary text from match line
    primary = None
    for line in match_lines:
        blockquotes = re.findall(r"<blockquote>(.*?)</blockquote>", line)
        for bq in blockquotes:
            text = bq.strip()
            if text and primary is None:
                primary = text
        k_matches = re.findall(r"<k>(.*?)</k>", line)
        for k in k_matches:
            text = k.strip()
            if text and primary is None:
                primary = text

    # Extract all context texts
    context_texts = []
    for line in context_lines:
        line = line.strip()
        if not line:
            continue
        blockquotes = re.findall(r"<blockquote>(.*?)</blockquote>", line)
        for bq in blockquotes:
            text = bq.strip()
            if text:
                context_texts.append(text)
        k_matches = re.findall(r"<k>(.*?)</k>", line)
        for k in k_matches:
            text = k.strip()
            if text:
                context_texts.append(text)

    return primary, context_texts


def extract_search_keywords(text, min_words=2, max_words=4):
    """
    Extract good search keywords from the text.
    Prefers Russian words (no өүң) since OCR handles them better.
    Returns a list of keyword strings to try searching for.
    """
    if not text:
        return []

    # Remove quotes and punctuation for cleaner word extraction
    clean = re.sub(r'["""«»\(\)\[\]:;!?,\.\-—–]', " ", text)
    words = clean.split()

    # Classify words
    russian_words = []  # Pure Russian Cyrillic, no bad OCR chars
    safe_kyrgyz_words = []  # Cyrillic but no bad OCR chars
    all_words = []

    for w in words:
        if len(w) < 3:
            continue
        has_bad_chars = any(c in BAD_OCR_CHARS for c in w)
        has_cyrillic = any(c in ALL_CYRILLIC for c in w)
        is_pure_russian = has_cyrillic and not has_bad_chars

        if is_pure_russian and len(w) >= 4:
            russian_words.append(w)
        elif has_cyrillic and not has_bad_chars:
            safe_kyrgyz_words.append(w)

        if has_cyrillic:
            all_words.append(w)

    # Build search queries - prefer Russian words, then safe Kyrgyz
    candidates = russian_words + safe_kyrgyz_words

    if len(candidates) < min_words:
        # Fall back to all words, even those with bad OCR chars
        candidates = all_words

    if not candidates:
        return []

    # Build a few different keyword combinations to try
    # Prefer multi-word queries (2+ words) over single words
    queries = []

    # Try consecutive pairs/triples/quads from the candidates
    if len(candidates) >= max_words:
        queries.append(" ".join(candidates[:max_words]))
    if len(candidates) >= 3:
        queries.append(" ".join(candidates[:3]))
    if len(candidates) >= min_words:
        queries.append(" ".join(candidates[:min_words]))
    if len(candidates) >= 3:
        # Try from the middle too
        mid = len(candidates) // 2
        queries.append(" ".join(candidates[mid : mid + min_words]))

    # Only add single words as last resort, and only long distinctive ones (6+ chars)
    for w in candidates:
        if len(w) >= 6:
            queries.append(w)
            if len(queries) >= 8:
                break

    return queries


def build_page_cache(doc):
    """
    Pre-extract text and word positions from all pages.
    Returns a list of dicts with 'text', 'words', 'page_num'.
    """
    cache = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        words = page.get_text("words")
        cache.append(
            {
                "page_num": page_num,
                "text": text,
                "text_lower": text.lower(),
                "words": words,
            }
        )
    return cache


def find_all_matching_pages(page_cache, queries):
    """
    Find ALL pages that contain any of the queries.
    Returns a list of (page_num, query_that_matched).
    """
    matches = []
    seen_pages = set()
    for query in queries:
        if len(query) < 4:
            continue
        query_lower = query.lower()
        for pc in page_cache:
            if pc["page_num"] not in seen_pages and query_lower in pc["text_lower"]:
                matches.append((pc["page_num"], query))
                seen_pages.add(pc["page_num"])
    return matches


def validate_page_with_helper(page_cache, page_num, helper_queries):
    """
    Check if the helper text keywords are also present on the given page.
    Returns a score that rewards diversity (many different keywords each appearing
    just once or twice) and penalizes repetition (a keyword appearing many times
    likely means this page is the entry FOR that word, not the page we want).
    """
    if not helper_queries:
        return 0
    pc = page_cache[page_num]
    page_text = pc["text_lower"]
    score = 0.0
    for q in helper_queries:
        if len(q) < 4:
            continue
        q_lower = q.lower()
        count = page_text.count(q_lower)
        if count == 0:
            continue
        elif count <= 2:
            # Appears once or twice — good, likely an incidental match near our target
            score += 1.0
        else:
            # Appears many times — this page is probably the entry FOR this word
            # Give reduced (or negative) weight
            score += 0.2
    return score


def search_with_validation(doc, page_cache, primary_queries, helper_queries):
    """
    Search using primary queries, then validate/rank results using helper queries.
    Returns (page_num, rects) or None.
    """
    # Find all pages matching primary queries
    primary_matches = find_all_matching_pages(page_cache, primary_queries)

    if not primary_matches:
        return None

    if len(primary_matches) == 1:
        # Only one match, use it
        page_num, query = primary_matches[0]
        page = doc[page_num]
        rects = page.search_for(query)
        return page_num, rects if rects else [], "exact-unique"

    # Multiple matches — rank by helper text presence
    best_page = None
    best_score = -1
    best_query = None

    for page_num, query in primary_matches:
        score = validate_page_with_helper(page_cache, page_num, helper_queries)
        if score > best_score:
            best_score = score
            best_page = page_num
            best_query = query

    if best_page is not None:
        page = doc[best_page]
        rects = page.search_for(best_query)
        method = f"exact-validated(score={best_score:.1f}/{len(primary_matches)}pages)"
        return best_page, rects if rects else [], method

    return None


def search_helper_only(doc, page_cache, helper_queries, primary_queries=None):
    """
    When primary text is too short, search using helper text keywords only.
    If primary_queries provided, validate/rank results with them.
    Returns (page_num, rects, method) or None.
    """
    matches = find_all_matching_pages(page_cache, helper_queries)
    if not matches:
        return None

    if len(matches) == 1 or not primary_queries:
        # Single match or no primary to validate with
        page_num, query = matches[0]
        page = doc[page_num]
        rects = page.search_for(query)
        return page_num, rects if rects else [], "helper-exact"

    # Multiple matches — rank by primary text presence (cross-validate)
    best_page = None
    best_score = -1
    best_query = None

    for page_num, query in matches:
        score = validate_page_with_helper(page_cache, page_num, primary_queries)
        if score > best_score:
            best_score = score
            best_page = page_num
            best_query = query

    if best_page is not None:
        page = doc[best_page]
        rects = page.search_for(best_query)
        method = f"helper-validated(score={best_score:.1f}/{len(matches)}pages)"
        return best_page, rects if rects else [], method

    return None


def search_fuzzy(page_cache, text, threshold=0.4):
    """
    Fuzzy search: find the page with the best match for the text.
    Uses SequenceMatcher on chunks of page text.
    Returns (page_num, ratio) or None.
    """
    target_clean = " ".join(text.split()).lower()
    target_len = len(target_clean)

    best_ratio = 0
    best_page = -1

    for pc in page_cache:
        page_text = pc["text_lower"]
        if not page_text.strip():
            continue

        # Sliding window approach - check windows of similar size to target
        window_size = min(len(page_text), target_len + 100)
        step = max(1, window_size // 4)

        for i in range(0, max(1, len(page_text) - window_size + 1), step):
            chunk = page_text[i : i + window_size]
            ratio = difflib.SequenceMatcher(None, target_clean, chunk).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_page = pc["page_num"]

    if best_ratio >= threshold and best_page >= 0:
        return best_page, best_ratio
    return None


def render_screenshot(doc, page_num, rects=None, padding=80, zoom=2):
    """
    Render a page (or cropped region) as a PNG pixmap.
    If rects are provided, crops around them with padding.
    Returns a fitz.Pixmap.
    """
    page = doc[page_num]
    mat = fitz.Matrix(zoom, zoom)

    h_padding = padding * 3.0  # Horizontal padding (much wider)
    v_padding = padding * 2.0  # Vertical padding (generous for context)

    if rects:
        # Compute bounding box around all rects
        combined = fitz.Rect()
        for r in rects:
            combined |= r

        # Add padding
        clip = fitz.Rect(
            max(0, combined.x0 - h_padding),
            max(0, combined.y0 - v_padding),
            min(page.rect.width, combined.x1 + h_padding),
            min(page.rect.height, combined.y1 + v_padding),
        )

        # Ensure minimum width: use full page width for narrow matches
        if clip.width < page.rect.width * 0.6:
            clip.x0 = 0
            clip.x1 = page.rect.width

        # Ensure minimum height (at least 15% of page height)
        min_height = page.rect.height * 0.15
        if clip.height < min_height:
            center_y = (clip.y0 + clip.y1) / 2
            clip.y0 = max(0, center_y - min_height / 2)
            clip.y1 = min(page.rect.height, center_y + min_height / 2)

        # Add semi-transparent yellow highlight annotation
        for r in rects:
            highlight = page.add_highlight_annot(r)
            highlight.set_colors(stroke=(1, 1, 0))  # Yellow
            highlight.set_opacity(0.35)
            highlight.update()

        pix = page.get_pixmap(matrix=mat, clip=clip)
    else:
        # Full page
        pix = page.get_pixmap(matrix=mat)

    return pix


def process_lines(input_file, output_dir, pdf_path, sample_n=None):
    """
    Main processing loop.
    """
    # Read input and split into blocks (separated by empty lines)
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by empty lines (one or more blank lines)
    raw_blocks = re.split(r"\n\s*\n", content.strip())

    # Also handle old single-line-per-entry format (no empty line separators)
    # If we got only one giant block, fall back to line-by-line parsing
    if len(raw_blocks) == 1 and content.count("\n") > 5:
        raw_blocks = content.strip().split("\n")

    # Parse each block
    entries = []
    for i, block in enumerate(raw_blocks):
        primary, context_texts = parse_input_block(block)
        if primary:
            entries.append({
                "block_num": i + 1,
                "text": primary,
                "context_texts": context_texts,
                "raw": block.strip(),
            })

    if sample_n and sample_n < len(entries):
        random.seed(42)
        entries = random.sample(entries, sample_n)
        entries.sort(key=lambda e: e["block_num"])

    print(f"Processing {len(entries)} lines from {input_file}")
    print(f"PDF: {pdf_path}")
    print(f"Output: {output_dir}")
    print()

    # Open PDF and build cache
    print("Loading PDF and building page cache...")
    doc = fitz.open(pdf_path)
    page_cache = build_page_cache(doc)
    print(f"  {len(doc)} pages cached.\n")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    found_count = 0
    not_found = []

    for idx, entry in enumerate(entries):
        block_num = entry["block_num"]
        text = entry["text"]
        context_texts = entry["context_texts"]
        label = f"line_{block_num:04d}"

        print(f"[{idx + 1}/{len(entries)}] Block {block_num}: {text[:60]}...")
        if len(context_texts) > 1:
            print(f"    Context: {len(context_texts)} text fragments")

        # Extract keywords from primary text AND all context texts
        primary_queries = extract_search_keywords(text)
        context_queries = []
        for ct in context_texts:
            if ct != text:  # Don't duplicate primary
                context_queries.extend(extract_search_keywords(ct))

        result = None
        rects = None
        method = None

        # Strategy 1: Search with primary queries, validate with context
        if primary_queries:
            found = search_with_validation(doc, page_cache, primary_queries, context_queries)
            if found:
                result, rects, method = found

        # Strategy 2: If primary text is too short or not found, try context queries
        if result is None and context_queries:
            found = search_helper_only(doc, page_cache, context_queries, primary_queries)
            if found:
                result, rects, method = found

        # Strategy 3: Fuzzy search combining all context texts
        if result is None:
            combined_text = " ".join(context_texts)
            fuzzy = search_fuzzy(page_cache, combined_text)
            if fuzzy:
                page_num, ratio = fuzzy
                result = page_num
                method = f"fuzzy (ratio={ratio:.2f})"

                # Try to get rects on the found page using any keywords
                all_queries = primary_queries + context_queries
                if all_queries:
                    page = doc[page_num]
                    for q in all_queries:
                        found_rects = page.search_for(q)
                        if found_rects:
                            rects = found_rects
                            break

        if result is not None:
            found_count += 1
            print(f"  → Found on page {result + 1} ({method})")

            # Save text
            txt_path = os.path.join(output_dir, f"{label}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Block {block_num} from {os.path.basename(input_file)}\n")
                f.write(f"Found on page {result + 1} ({method})\n")
                f.write(f"\n{text}\n")
                if len(context_texts) > 0:
                    f.write(f"\nContext:\n")
                    for ct in context_texts:
                        f.write(f"  {ct}\n")

            # Save screenshot
            png_path = os.path.join(output_dir, f"{label}.png")
            pix = render_screenshot(doc, result, rects)
            pix.save(png_path)
            print(f"  → Saved {txt_path} + {png_path}")
        else:
            not_found.append(entry)
            print(f"  → NOT FOUND")

        print()

    # Write not_found.txt
    if not_found:
        nf_path = os.path.join(output_dir, "not_found.txt")
        with open(nf_path, "w", encoding="utf-8") as f:
            for entry in not_found:
                f.write(f"Block {entry['block_num']}: {entry['text']}\n")
                for ct in entry['context_texts']:
                    if ct != entry['text']:
                        f.write(f"  Context: {ct}\n")
        print(f"\n{len(not_found)} lines not found. See {nf_path}")

    print(f"\nDone! Found {found_count}/{len(entries)} lines.")
    print(f"Results in {output_dir}/")

    doc.close()


def main():
    parser = argparse.ArgumentParser(
        description="Find lines from a text file in an OCRed PDF and produce paired screenshots."
    )
    parser.add_argument("input_file", help="Input text file (e.g., tags_rest_blockquote.txt)")
    parser.add_argument(
        "--pdf",
        default="sources/udahin_ocred_kyr_rus.pdf",
        help="Path to the OCRed PDF (default: sources/udahin_ocred_kyr_rus.pdf)",
    )
    parser.add_argument(
        "--output-dir",
        default="chatGPT_exp/pdf_line_results",
        help="Output directory for paired .txt/.png files",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Randomly sample N lines for testing (default: process all)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    if not os.path.exists(args.pdf):
        print(f"Error: PDF not found: {args.pdf}")
        sys.exit(1)

    process_lines(args.input_file, args.output_dir, args.pdf, sample_n=args.sample)


if __name__ == "__main__":
    main()
