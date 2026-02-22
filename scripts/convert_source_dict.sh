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
python3 identify_collocation.py $converted_dict $converted_dict
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

    # local special_file="${dir}/${filename}_special_cards.xml"
    # python3 extract_special_cards.py "$processed_file" "$special_file"
    # lint "$special_file"
}

process_cards "$converted_dict"