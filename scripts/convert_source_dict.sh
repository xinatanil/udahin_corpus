input_dict=../sources/corrected_source_dict.xml
converted_dict=../chatGPT_exp/converted_dict.xml

lint() {
    local file=$1
    export XMLLINT_INDENT=$'\t'
    temp_file=$(mktemp)
    if xmllint --format "$file" --output "$temp_file"; then
        mv "$temp_file" "$file"
    else
        rm "$temp_file"
        echo "Error: xmllint failed for $file" >&2
        return 1
    fi
}

saxon -xsl:sorting_xsl_template.xsl -s:$input_dict -o:$converted_dict

temp_file=$(mktemp)
saxon -xsl:fix_homonyms.xsl -s:$converted_dict -o:$temp_file
mv $temp_file $converted_dict
sed -i '' 's/openingCardTag/<card>/g' $converted_dict
sed -i '' 's/closingCardTag/<\/card>/g' $converted_dict

lint "$converted_dict"

temp_file=$(mktemp)
saxon -xsl:fix_lexical_meanings.xsl -s:$converted_dict -o:$temp_file
mv $temp_file $converted_dict
sed -i '' 's/openingMeaningTag/<meaning>/g' $converted_dict
sed -i '' 's/closingMeaningTag/<\/meaning>/g' $converted_dict

lint "$converted_dict"

python3 format_numbered_meanings.py "$converted_dict" "$converted_dict"

python3 identify_synonyms.py $converted_dict $converted_dict
python3 identify_categories.py $converted_dict $converted_dict
python3 identify_minicards.py $converted_dict $converted_dict
python3 identify_links.py $converted_dict $converted_dict
python3 identify_meta.py $converted_dict $converted_dict
python3 identify_trn.py $converted_dict $converted_dict

lint "$converted_dict"

# ksdiff $input_dict $converted_dict

# Remove empty blockquotes
sed -i '' 's|<blockquote/>||g' $converted_dict
sed -i '' 's|<blockquote />||g' $converted_dict
sed -i '' 's|--------||g' $converted_dict

lint "$converted_dict"


process_cards() {
    local input_file="$1"
    local dir=$(dirname "$input_file")
    local filename=$(basename "$input_file" .xml)

    # Process cards
    local processed_file="$input_file"

    # Extract trn to a separate file
    local trn_only_file="${dir}/${filename}_trn_only.xml"
    python3 extract_trn.py "$processed_file" "$trn_only_file"
    lint "$trn_only_file"

    # Extract suspicious Kyrgyz items from TRN
    local kyrgyz_items_file="${dir}/${filename}_kyrgyz_in_trn.txt"
    python3 extract_kyrgyz_items.py "$trn_only_file" "$kyrgyz_items_file"

    # Filter cards with trn to a separate file
    local processed_filtered_file="${dir}/${filename}_cards_with_trn.xml"
    python3 filter_cards_with_trn.py "$processed_file" "$processed_filtered_file"
    lint "$processed_filtered_file"

    # Filter cards without trn to a separate file
    local processed_no_trn_file="${dir}/${filename}_cards_without_trn.xml"
    python3 filter_cards_without_trn.py "$processed_file" "$processed_no_trn_file"
    lint "$processed_no_trn_file"
}

# Extract "a" cards
# a_cards_file=../chatGPT_exp/a.xml
# python3 extract_a_cards.py "$converted_dict" "$a_cards_file"

# process_cards "$a_cards_file"
process_cards "$converted_dict"