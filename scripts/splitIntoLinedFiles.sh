LETTER_FOLDER=../letters/ш
WIP_FILE=$LETTER_FOLDER/letter_wip.xml

saxon -xsl:extractSimple_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_1.xml
saxon -xsl:extractSimple_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_2.xml
saxon -xsl:extractSimple_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_3.xml
saxon -xsl:extractSimple_4_and_more.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_4.xml
saxon -xsl:extractSimple_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_minicards.xml
saxon -xsl:extractMeanings_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_1.xml
saxon -xsl:extractMeanings_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_2.xml
saxon -xsl:extractMeanings_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_3.xml
saxon -xsl:extractMeanings_4.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_4.xml
saxon -xsl:extractMeanings_5.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_5.xml
saxon -xsl:extractMeanings_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_minicards.xml
saxon -xsl:extractHomonyms_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_1.xml
saxon -xsl:extractHomonyms_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_2.xml
saxon -xsl:extractHomonyms_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_3.xml
saxon -xsl:extractHomonyms_4.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_4.xml
saxon -xsl:extractHomonyms_5.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_5.xml
saxon -xsl:extractHomonyms_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_minicards.xml