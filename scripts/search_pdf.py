import fitz  # PyMuPDF
import difflib
import sys
import re
import os
import base64

PDF_PATH = os.path.join(os.path.dirname(__file__), '..', 'sources', 'udahin_ocred_kyr_rus.pdf')


def strip_xml_tags(text):
    """Remove XML tags from text, returning just the content."""
    return re.sub(r'<[^>]+>', '', text).strip()


def build_page_index(doc):
    """Pre-extract and clean text for all pages once."""
    print("Indexing PDF pages...")
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text()
        clean = " ".join(raw_text.split()).lower()
        pages.append(clean)
    print(f"Indexed {len(pages)} pages")
    return pages


def find_text_in_pages(page_texts, target_text, min_ratio=0.5):
    """
    Search for target_text across pre-indexed page texts using sliding window.
    Returns (page_num, ratio) of the best match, or None.
    """
    target_clean = " ".join(target_text.split()).lower()
    if not target_clean:
        return None

    target_len = len(target_clean)
    best_ratio = 0
    best_page = -1
    step = max(1, target_len // 4)

    start_page = 16
    for page_num in range(start_page, len(page_texts)):
        page_clean = page_texts[page_num]
        if len(page_clean) < target_len:
            continue

        for start in range(0, len(page_clean) - target_len + 1, step):
            window = page_clean[start:start + target_len]
            ratio = difflib.SequenceMatcher(None, target_clean, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_page = page_num

    if best_ratio >= min_ratio and best_page >= 0:
        return (best_page, best_ratio)
    return None


def get_highlight_rect(doc, page_num, target_text):
    """Try to find a highlight rectangle on the given page for the target text."""
    page = doc[page_num]
    words = target_text.split()

    # Try progressively shorter search terms
    for n in range(min(4, len(words)), 0, -1):
        search_term = " ".join(words[:n])
        rects = page.search_for(search_term)
        if rects:
            r = rects[0]
            return fitz.Rect(r.x0 - 10, r.y0 - 20, r.x1 + 10, r.y1 + 20)

    # Fallback: highlight middle of page
    w, h = page.rect.width, page.rect.height
    return fitz.Rect(50, h * 0.3, w - 50, h * 0.7)


def render_page_with_highlight_data_uri(page_num, rect):
    """Render a highlighted PDF page and return a PNG data URI for embedding in HTML."""
    # Open a fresh copy so highlights don't accumulate
    doc = fitz.open(PDF_PATH)
    page = doc[page_num]

    shape = page.new_shape()
    shape.draw_rect(rect)
    yellow = (1, 1, 0)
    shape.finish(color=yellow, fill=yellow, fill_opacity=0.3, stroke_opacity=0.3, width=2)
    shape.commit()

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    png_bytes = pix.tobytes("png")
    doc.close()
    png_b64 = base64.b64encode(png_bytes).decode('ascii')
    return f"data:image/png;base64,{png_b64}"


def parse_blocks(file_path):
    """
    Parse the extract_colons.py output file into blocks.
    Each block is: target line, ---, context lines, then blank lines.
    Returns a list of (target_text, target_line, context) tuples.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_blocks = content.split('\n\n\n')
    blocks = []

    for raw_block in raw_blocks:
        raw_block = raw_block.strip()
        if not raw_block:
            continue

        lines = raw_block.split('\n')
        if len(lines) < 2:
            continue

        target_line = lines[0]
        target_text = strip_xml_tags(target_line)
        context = '\n'.join(lines[2:]) if len(lines) > 2 else ''

        if target_text:
            blocks.append((target_text, target_line, context))

    return blocks


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


HTML_HEADER = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PDF Search Results</title>
<style>
    body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
    .result { border: 1px solid #444; margin: 20px 0; padding: 15px; border-radius: 8px; background: #2d2d2d; }
    .result.not-found { border-color: #744; background: #2d2222; }
    .idx { color: #888; font-size: 0.9em; }
    .target { color: #ce9178; font-size: 1.1em; margin: 8px 0; }
    .info { color: #9cdcfe; margin: 4px 0; }
    .context { color: #888; font-size: 0.9em; margin-top: 10px; white-space: pre-wrap; border-top: 1px solid #444; padding-top: 10px; }
    img { max-width: 100%; cursor: zoom-in; margin-top: 10px; border: 1px solid #555; border-radius: 4px; }
    img.zoomed { max-width: none; cursor: zoom-out; }
    h1 { color: #569cd6; }
    .stats { color: #6a9955; margin-bottom: 20px; }
</style>
<script>
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'IMG') {
            e.target.classList.toggle('zoomed');
        }
    });
</script>
</head>
<body>
<h1>PDF Search Results</h1>
<div class="stats" id="stats"></div>
"""

HTML_FOOTER = """
</body></html>
"""


def result_to_html(r):
    """Convert a single result dict to an HTML block."""
    css_class = "result" if r['page'] else "result not-found"
    parts = []
    parts.append(f'<div class="{css_class}">')
    parts.append(f'  <div class="idx">#{r["idx"]}</div>')
    parts.append(f'  <div class="target">{escape_html(r["target_line"])}</div>')
    parts.append(f'  <div class="context">{escape_html(r["context"])}</div>')
    if r['page']:
        parts.append(f'  <div class="info">Page {r["page"]} &mdash; ratio: {r["ratio"]:.3f}</div>')
        if r['png']:
            parts.append(f'  <img src="{r["png"]}" alt="Page {r["page"]}">')
    else:
        parts.append(f'  <div class="info" style="color: #f44;">NOT FOUND</div>')
    parts.append(f'</div>')
    return '\n'.join(parts)


def write_single_result_html(output_path, result, found_count=1, total=1):
    with open(output_path, 'w', encoding='utf-8') as html_file:
        html_file.write(HTML_HEADER)
        html_file.write(result_to_html(result) + '\n')
        html_file.write(
            f'\n<script>document.getElementById("stats").textContent = "Found: {found_count} / {total}";</script>\n'
        )
        html_file.write(HTML_FOOTER)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 search_pdf.py <input_file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    os.makedirs(output_dir, exist_ok=True)

    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)

    page_texts = build_page_index(doc)

    blocks = parse_blocks(input_file)
    total = len(blocks)
    print(f"Found {total} target blocks to search for\n")

    found_count = 0

    for idx, (target_text, target_line, context) in enumerate(blocks):
        short_target = target_text[:80] + ('...' if len(target_text) > 80 else '')
        print(f"[{idx + 1}/{total}] Searching: {short_target}")

        match = find_text_in_pages(page_texts, target_text)
        result = {
            'idx': idx + 1,
            'target_line': target_line,
            'target_text': target_text,
            'context': context,
            'page': None,
            'ratio': 0,
            'png': None,
        }

        if match:
            page_num, ratio = match
            rect = get_highlight_rect(doc, page_num, target_text)
            png_data_uri = render_page_with_highlight_data_uri(page_num, rect)
            result['page'] = page_num + 1
            result['ratio'] = ratio
            result['png'] = png_data_uri
            print(f"  -> Found on page {page_num + 1} (ratio: {ratio:.3f})")
            found_count += 1
            found_in_file = 1
        else:
            print(f"  -> No match found")
            found_in_file = 0

        html_path = os.path.join(output_dir, f"{idx + 1:04d}.html")
        write_single_result_html(html_path, result, found_count=found_in_file, total=1)
        print(f"  -> Wrote {html_path}")

    print(f"\n{'=' * 40}")
    print(f"Done! Found {found_count}/{total} targets")
    print(f"Open any result file like: {os.path.join(output_dir, '0001.html')}")

    doc.close()


if __name__ == "__main__":
    main()
