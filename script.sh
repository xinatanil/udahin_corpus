DSL_PATH="/Users/xinatanil/Desktop/abbyy_udahin_kg_ru.dsl"
UTF8_DSL_PATH="/Users/xinatanil/Desktop/udahin_utf8.dsl"
UTF16_DSL_PATH="/Users/xinatanil/Desktop/compiling_stuff/udahin_kg_ru.dsl"

saxon -xsl:convert_to_dsl.xsl -s:kg_ru_yudahin.xml -o:$DSL_PATH
iconv -f utf-16le -t utf-8 $DSL_PATH > $UTF8_DSL_PATH
sed -i '' 's/</[/g' $UTF8_DSL_PATH
sed -i '' 's/>/]/g' $UTF8_DSL_PATH
sed -i '' '1d' $UTF8_DSL_PATH
iconv -f utf-8 -t utf-16le $UTF8_DSL_PATH > $UTF16_DSL_PATH

rm $DSL_PATH
rm $UTF8_DSL_PATH
