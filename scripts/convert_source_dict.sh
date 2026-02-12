input_dict=../sources/corrected_source_dict.xml
converted_dict=../chatGPT_exp/converted_dict.xml

lint() {
    export XMLLINT_INDENT=$'\t'
    temp_file=$(mktemp)
    xmllint --format "$converted_dict" -o "$temp_file"
    mv "$temp_file" "$converted_dict"
}

saxon -xsl:sorting_xsl_template.xsl -s:$input_dict -o:$converted_dict

temp_file=$(mktemp)
saxon -xsl:fix_homonyms.xsl -s:$converted_dict -o:$temp_file
mv $temp_file $converted_dict
sed -i '' 's/openingCardTag/<card>/g' $converted_dict
sed -i '' 's/closingCardTag/<\/card>/g' $converted_dict

lint

temp_file=$(mktemp)
saxon -xsl:fix_lexical_meanings.xsl -s:$converted_dict -o:$temp_file
mv $temp_file $converted_dict
sed -i '' 's/openingMeaningTag/<meaning>/g' $converted_dict
sed -i '' 's/closingMeaningTag/<\/meaning>/g' $converted_dict

lint

python3 fix_python.py $converted_dict $converted_dict

lint

# ksdiff $input_dict $converted_dict
