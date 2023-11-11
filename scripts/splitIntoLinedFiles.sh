LETTER_FOLDER=../letters/м
WIP_FILE=$LETTER_FOLDER/letter_wip.xml
EXTRACTION_FOLDER=extraction_scripts
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_0.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_0.xml
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_1.xml
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_2.xml
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_3.xml
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_4_and_more.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_4.xml
saxon -xsl:$EXTRACTION_FOLDER/extractSimple_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/simple_minicards.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_1.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_2.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_3.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_4.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_4.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_5.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_5.xml
saxon -xsl:$EXTRACTION_FOLDER/extractMeanings_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/meanings_minicards.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_1.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_1.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_2.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_2.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_3.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_3.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_4.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_4.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_5.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_5.xml
saxon -xsl:$EXTRACTION_FOLDER/extractHomonyms_minicards.xsl -s:$WIP_FILE -o:$LETTER_FOLDER/homonyms_minicards.xml

cd $LETTER_FOLDER

files=(*)

for file in "${files[@]}"; do
    fileExtension="${filename##*.}"
    filename_no_extension="${filename%.*}"
    fileAfterLinting="${filename_no_extension}_after_linting.${fileExtension}"
    
    export XMLLINT_INDENT=$'\t'
    xmllint --format - < $file > $fileAfterLinting
    rm $file
    mv $fileAfterLinting $file
done
