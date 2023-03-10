python3 scripts/remove_weird_formatting.py letter_wip.xml letter_after.xml

saxon -xsl:scripts/detect_homonyms.xsl -s:letter_after.xml -o:letter_after.xml
sed -i '' 's/homonym/<homonym>/g' letter_after.xml
sed -i '' 's/closingHomonym/<\/homonym>/g' letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < letter_after.xml > after_linting.xml
rm letter_after.xml
mv after_linting.xml letter_after.xml

saxon -xsl:scripts/detect_lexical_meanings.xsl -s:letter_after.xml -o:letter_after.xml
sed -i '' 's/meaning/<meaning>/g' letter_after.xml
sed -i '' 's/closingMeaning/<\/meaning>/g' letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < letter_after.xml > after_linting.xml
rm letter_after.xml
mv after_linting.xml letter_after.xml

python3 scripts/python_script.py letter_after.xml letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < letter_after.xml > after_linting.xml
rm letter_after.xml
mv after_linting.xml letter_after.xml

ksdiff letter_wip.xml letter_after.xml
