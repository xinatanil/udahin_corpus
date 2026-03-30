#!/bin/bash
set -euo pipefail

input_dict=../../sources/corrected_source_dict.xml
converted_dict=../output/converted_dict.xml
fixed_source=../output/corrected_source_fixed.xml
colon_candidates_report=../output/colon_candidates.txt
colon_candidates_tsv=../output/colon_candidates.tsv
suspicious_links_report=../output/suspicious_links.txt
suspicious_links_tsv=../output/suspicious_links.tsv

notify_done() {
    local message="$1"
    if command -v osascript >/dev/null 2>&1; then
        osascript -e "display notification \"$message\" with title \"convert_source_dict_v2.sh\"" || true
    else
        printf '\a'
    fi
}

lint() {
    local file=$1
    export XMLLINT_INDENT=$'\t'
    local temp_file
    temp_file=$(mktemp)
    if xmllint --format "$file" --output "$temp_file"; then
        mv "$temp_file" "$file"
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

if [ -f "$converted_dict" ]; then
    cp "$converted_dict" "${converted_dict}.old"
fi

python3 apply_source_fixes.py "$input_dict" "$fixed_source"

saxon -xsl:sorting_xsl_template.xsl -s:$fixed_source -o:$converted_dict

python3 identify_glued_cards.py "$converted_dict" "$converted_dict"

temp_file=$(mktemp ../output/fix_homonyms.XXXXXX.xml)
saxon -xsl:fix_homonyms.xsl -s:$converted_dict -o:$temp_file
mv "$temp_file" "$converted_dict"
replace_in_file "$converted_dict" "openingCardTag" "<card>"
replace_in_file "$converted_dict" "closingCardTag" "</card>"

lint "$converted_dict"

temp_file=$(mktemp ../output/fix_lexical_meanings.XXXXXX.xml)
saxon -xsl:fix_lexical_meanings.xsl -s:$converted_dict -o:$temp_file
mv "$temp_file" "$converted_dict"
replace_in_file "$converted_dict" "openingMeaningTag" "<meaning>"
replace_in_file "$converted_dict" "closingMeaningTag" "</meaning>"

lint "$converted_dict"

python3 format_numbered_meanings.py "$converted_dict" "$converted_dict"

lint "$converted_dict"

python3 apply_tree_stage.py "$converted_dict" "$converted_dict"
python3 apply_pre_links_xr_stage.py "$converted_dict" "$converted_dict"
python3 identify_links.py "$converted_dict" "$converted_dict"
python3 apply_post_links_tree_stage.py "$converted_dict" "$converted_dict"
python3 apply_semantic_stage.py "$converted_dict" "$converted_dict"
python3 identify_examples.py "$converted_dict" "$converted_dict"

lint "$converted_dict"

replace_in_file "$converted_dict" "<blockquote/>" ""
replace_in_file "$converted_dict" "<blockquote />" ""
replace_in_file "$converted_dict" "--------" ""

lint "$converted_dict"

python3 compile_homonyms.py "$converted_dict" "$converted_dict"
lint "$converted_dict"
python3 apply_post_fixes.py "$converted_dict" "$converted_dict"
lint "$converted_dict"
python3 apply_colon_rules.py "$converted_dict" "$converted_dict"
lint "$converted_dict"

bash calculate_tag_counts.sh "$converted_dict"
python3 list_keyword_blockquotes.py "$converted_dict" ../output/keyword_blockquotes_no_colon.txt
python3 report_colon_candidates.py "$converted_dict" "$colon_candidates_report" "$colon_candidates_tsv"
python3 report_suspicious_links.py "$converted_dict" "$suspicious_links_report" "$suspicious_links_tsv"

if [ -f "${converted_dict}.old" ]; then
    echo "Generating diff..."
    diff -u "${converted_dict}.old" "$converted_dict" > "${converted_dict}.diff" || true
    echo "Diff saved to ${converted_dict}.diff"
fi

notify_done "Finished processing converted_dict.xml"
