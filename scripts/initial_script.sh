python3 remove_weird_formatting.py ../letter_wip.xml ../sources/letter_after.xml

saxon -xsl:detect_homonyms.xsl -s:../sources/letter_after.xml -o:../sources/letter_after.xml
sed -i '' 's/homonym/<homonym>/g' ../sources/letter_after.xml
sed -i '' 's/closingHomonym/<\/homonym>/g' ../sources/letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < ../sources/letter_after.xml > ../sources/after_linting.xml
rm ../sources/letter_after.xml
mv ../sources/after_linting.xml ../sources/letter_after.xml

saxon -xsl:detect_lexical_meanings.xsl -s:../sources/letter_after.xml -o:../sources/letter_after.xml
sed -i '' 's/meaning/<meaning>/g' ../sources/letter_after.xml
sed -i '' 's/closingMeaning/<\/meaning>/g' ../sources/letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < ../sources/letter_after.xml > ../sources/after_linting.xml
rm ../sources/letter_after.xml
mv ../sources/after_linting.xml ../sources/letter_after.xml

python3 python_script.py ../sources/letter_after.xml ../sources/letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < ../sources/letter_after.xml > ../sources/after_linting.xml
rm ../sources/letter_after.xml
mv ../sources/after_linting.xml ../sources/letter_after.xml

ksdiff ../letter_wip.xml ../sources/letter_after.xml
