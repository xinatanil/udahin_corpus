#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

input_dict="$ROOT_DIR/sources/corrected_source_dict.xml"
converted_dict="$ROOT_DIR/chatGPT_exp/converted_dict.xml"
v2_scripts="$ROOT_DIR/pipeline_part1/scripts"

fixed_source=""

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
        return 1
    fi
}

replace_in_file() {
    local file=$1
    local old=$2
    local new=$3
    python3 - "$file" "$old" "$new" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
old = sys.argv[2]
new = sys.argv[3]
path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')
PY
}

compact_simple_xr_lines() {
    local file=$1
    python3 - "$file" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')

# xmllint sometimes formats simple xr tags with a single inline wordLink over
# two lines. Keep these compact for easier review.
text = re.sub(
    r'<xr>([^<\n]*?<wordLink\b[^>]*/>)\s*\n\s*</xr>',
    r'<xr>\1</xr>',
    text,
)

path.write_text(text, encoding='utf-8')
PY
}

cleanup() {
    if [ -n "${fixed_source:-}" ] && [ -f "$fixed_source" ]; then
        rm -f "$fixed_source"
    fi
}

trap cleanup EXIT

fixed_source=$(mktemp "$ROOT_DIR/chatGPT_exp/corrected_source_fixed_tmp.XXXXXX")

python3 "$v2_scripts/apply_source_fixes.py" "$input_dict" "$fixed_source"

saxon -xsl:$v2_scripts/sorting_xsl_template.xsl -s:$fixed_source -o:$converted_dict

python3 "$v2_scripts/identify_glued_cards.py" "$converted_dict" "$converted_dict"

temp_file=$(mktemp "$ROOT_DIR/chatGPT_exp/fix_homonyms_tmp.XXXXXX")
saxon -xsl:$v2_scripts/fix_homonyms.xsl -s:$converted_dict -o:$temp_file
mv "$temp_file" "$converted_dict"
replace_in_file "$converted_dict" "openingCardTag" "<card>"
replace_in_file "$converted_dict" "closingCardTag" "</card>"

lint "$converted_dict"

temp_file=$(mktemp "$ROOT_DIR/chatGPT_exp/fix_lexical_meanings_tmp.XXXXXX")
saxon -xsl:$v2_scripts/fix_lexical_meanings.xsl -s:$converted_dict -o:$temp_file
mv "$temp_file" "$converted_dict"
replace_in_file "$converted_dict" "openingMeaningTag" "<meaning>"
replace_in_file "$converted_dict" "closingMeaningTag" "</meaning>"

lint "$converted_dict"

python3 "$v2_scripts/format_numbered_meanings.py" "$converted_dict" "$converted_dict"

lint "$converted_dict"

python3 "$v2_scripts/apply_tree_stage.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/apply_pre_links_xr_stage.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/identify_links.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/apply_post_links_tree_stage.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/apply_semantic_stage.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/apply_post_fixes.py" --mode pre_trn "$converted_dict" "$converted_dict"
python3 "$v2_scripts/identify_trn.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/identify_examples.py" "$converted_dict" "$converted_dict"

lint "$converted_dict"

replace_in_file "$converted_dict" "<blockquote/>" ""
replace_in_file "$converted_dict" "<blockquote />" ""
replace_in_file "$converted_dict" "--------" ""

lint "$converted_dict"

python3 "$v2_scripts/compile_homonyms.py" "$converted_dict" "$converted_dict"
lint "$converted_dict"
python3 "$v2_scripts/apply_post_fixes.py" "$converted_dict" "$converted_dict"
lint "$converted_dict"
python3 "$v2_scripts/apply_colon_rules.py" "$converted_dict" "$converted_dict"
python3 "$v2_scripts/normalize_wordlinks.py" "$converted_dict" "$converted_dict"
lint "$converted_dict"
compact_simple_xr_lines "$converted_dict"
