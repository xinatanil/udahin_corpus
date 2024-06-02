chatGPT_folder=../chatGPT_exp
source_dict=$chatGPT_folder/source_dict.xml
test_dict=$chatGPT_folder/test_dict.xml

saxon -xsl:copyCardsThatStartOnLetter.xsl -s:$source_dict -o:$test_dict letter="а"
export XMLLINT_INDENT=$'\t'
xmllint --format "$test_dict" -o "$test_dict"