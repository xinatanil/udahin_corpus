#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

input_xml="$ROOT_DIR/sources/pipeline_part1_result.xml"
pipeline_output_dir="$ROOT_DIR/pipeline_output"
output_xml="$pipeline_output_dir/converted_dict.xml"
approved_llm_dir="$ROOT_DIR/pipeline_part2/data/approved_llm_fixes"

lint() {
    local file=$1
    local temp_file
    temp_file=$(mktemp)
    if xmllint --format "$file" --output "$temp_file"; then
        python3 - "$temp_file" "$file" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
text = re.sub(r'^( +)', lambda m: '\t' * (len(m.group(1)) // 2), text, flags=re.M)
# Collapse blockquotes whose content ends with a self-closing inline tag so the
# closing </blockquote> does not sit alone on its own line.
text = re.sub(r'(<blockquote>.*?/>)\s*\n[ \t]*(</blockquote>)', r'\1\2', text)
dst.write_text(text, encoding='utf-8')
PY
        rm -f "$temp_file"
    else
        rm -f "$temp_file"
        echo "Error: xmllint failed for $file" >&2
        exit 1
    fi
}

retag_final_part2_tags() {
    local file=$1
    python3 - "$file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
text = text.replace('<alternativeForm>', '<altForm>')
text = text.replace('</alternativeForm>', '</altForm>')
text = text.replace('<synonym>', '<altForm>')
text = text.replace('</synonym>', '</altForm>')
path.write_text(text, encoding='utf-8')
PY
}

mkdir -p "$pipeline_output_dir"

cp "$input_xml" "$output_xml"
lint "$output_xml"
python3 "$SCRIPT_DIR/apply_ili_bad_fixes.py" "$output_xml" "$output_xml"
python3 "$SCRIPT_DIR/apply_part_2_fixes.py" "$output_xml" "$output_xml"
python3 "$SCRIPT_DIR/apply_part_2_examples.py" "$output_xml" "$output_xml"
python3 "$SCRIPT_DIR/apply_manual_markdown_examples.py" "$output_xml" "$output_xml"
python3 "$SCRIPT_DIR/apply_approved_llm_fixes.py" "$output_xml" "$approved_llm_dir" "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_with_word.py" 'фольк.' --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_with_stikh.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_with_pogov.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_simple_xr_examples.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_parenthesized_xr_examples.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_three_word_sm_wordlink.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_two_word_source_last_hyphen_strict.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_middle_hyphen_two_words_no_links.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_three_words_second_contains_uu.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_two_words_first3_match.py" --input "$output_xml" --apply-output "$output_xml"
python3 "$SCRIPT_DIR/find_blockquotes_four_words_paired_first2_match.py" --input "$output_xml" --apply-output "$output_xml"
lint "$output_xml"
retag_final_part2_tags "$output_xml"
lint "$output_xml"

osascript -e 'display notification "Part 2 pipeline finished" with title "Udahin" sound name "Glass"'
