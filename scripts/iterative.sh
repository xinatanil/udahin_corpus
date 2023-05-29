python3 python_script.py ../letter_wip.xml ../sources/letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < ../sources/letter_after.xml > ../sources/after_linting.xml
rm ../sources/letter_after.xml
mv ../sources/after_linting.xml ../sources/letter_after.xml

ksdiff ../letter_wip.xml ../sources/letter_after.xml
