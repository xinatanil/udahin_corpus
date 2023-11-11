letterFolder=../letters/м
letter_wip=$letterFolder/letter_wip.xml
letter_after=$letterFolder/letter_after.xml
after_linting=$letterFolder/after_linting.xml

lint () {
    export XMLLINT_INDENT=$'\t'
    xmllint --format - < $letter_after > $after_linting
    rm $letter_after
    mv $after_linting $letter_after
}

python3 remove_weird_formatting.py $letter_wip $letter_after

saxon -xsl:detect_homonyms.xsl -s:$letter_after -o:$letter_after
sed -i '' 's/homonym/<homonym>/g' $letter_after
sed -i '' 's/closingHomonym/<\/homonym>/g' $letter_after

lint

saxon -xsl:detect_lexical_meanings.xsl -s:$letter_after -o:$letter_after
sed -i '' 's/meaning/<meaning>/g' $letter_after
sed -i '' 's/closingMeaning/<\/meaning>/g' $letter_after

lint

python3 python_script.py $letter_after $letter_after

lint

ksdiff $letter_wip $letter_after
