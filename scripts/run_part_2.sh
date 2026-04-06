#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

input_xml="$ROOT_DIR/sources/pipeline_part1_result.xml"
output_xml="$ROOT_DIR/chatGPT_exp/converted_dict.xml"
diff_xml="$ROOT_DIR/chatGPT_exp/converted_dict.part2.diff"
snapshot_xml="$ROOT_DIR/chatGPT_exp/converted_dict.snapshot.xml"

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
dst.write_text(text, encoding='utf-8')
PY
        rm -f "$temp_file"
    else
        rm -f "$temp_file"
        echo "Error: xmllint failed for $file" >&2
        exit 1
    fi
}

cp "$input_xml" "$output_xml"
python3 "$SCRIPT_DIR/apply_part_2_fixes.py" "$output_xml" "$output_xml"
lint "$output_xml"

diff -u "$input_xml" "$output_xml" > "$diff_xml" || true
if [ -f "$snapshot_xml" ]; then
	diff -u "$snapshot_xml" "$output_xml" > "$diff_xml" || true
	echo "Part 2 diff saved to $diff_xml"
else
	echo "No snapshot found at $snapshot_xml; skipping diff generation"
fi
