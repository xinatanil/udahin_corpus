saxon -xsl:convert_to_dsl.xsl -s:unit-test.xml -o:unit_test_result.xml
ksdiff unit_test_gold_standard.xml unit_test_result.xml
