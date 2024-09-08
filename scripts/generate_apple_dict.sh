templatePath=../apple_dict/apple_dict_template

saxon -xsl:convert_to_apple_dict.xsl -s:../chatGPT_exp/converted_dict.xml -o:$templatePath/UdahinDictionary.xml
saxon -xsl:replace_refs.xsl -s:$templatePath/UdahinDictionary.xml -o:$templatePath/UdahinDictionary.xml

# export XMLLINT_INDENT=$'\t'
# xmllint --format - < apple_dict_output.xml > after_linting.xml
# rm apple_dict_output.xml
# mv after_linting.xml apple_dict_output.xml

cd $templatePath
make
make install

killall Dictionary
sleep 0.5
open -a Dictionary