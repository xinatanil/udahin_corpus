chatGPT_folder=../chatGPT_exp
source_dict=$chatGPT_folder/source_dict.xml
test_dict=$chatGPT_folder/test_dict.xml
input_dict=$test_dict
converted_dict=$chatGPT_folder/converted_dict.xml

lint() {
    export XMLLINT_INDENT=$'\t'
    xmllint --format "$converted_dict" -o "$converted_dict"
}

saxon -xsl:sorting_xsl_template.xsl -s:$input_dict -o:$converted_dict

saxon -xsl:fix_homonyms.xsl -s:$converted_dict -o:$converted_dict
sed -i '' 's/openingCardTag/<card>/g' $converted_dict
sed -i '' 's/closingCardTag/<\/card>/g' $converted_dict

lint

saxon -xsl:fix_lexical_meanings.xsl -s:$converted_dict -o:$converted_dict
sed -i '' 's/openingMeaningTag/<meaning>/g' $converted_dict
sed -i '' 's/closingMeaningTag/<\/meaning>/g' $converted_dict

lint

# ksdiff $input_dict $converted_dict
