chatGPT_folder=../chatGPT_exp
source_dict=$chatGPT_folder/source_dict.xml
converted_dict=$chatGPT_folder/converted_dict.xml

lint() {
    export XMLLINT_INDENT=$'\t'
    xmllint --format "$converted_dict" -o "$converted_dict"
}

saxon -xsl:detect_homonyms.xsl -s:$source_dict -o:$converted_dict
sed -i '' 's/homonym/<homonym>/g' $converted_dict
sed -i '' 's/closingHomonym/<\/homonym>/g' $converted_dict

lint

# ksdiff $source_dict $converted_dict
