saxon -xsl:convert_to_apple_dict.xsl -s:kg_ru_yudahin.xml -o:apple_dict_template/UdahinDictionary.xml

# export XMLLINT_INDENT=$'\t'
# xmllint --format - < apple_dict_output.xml > after_linting.xml
# rm apple_dict_output.xml
# mv after_linting.xml apple_dict_output.xml

cd apple_dict_template
make
make install

killall Dictionary
sleep 0.5
open -a Dictionary