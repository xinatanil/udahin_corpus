SOURCE_FILE=../letter_wip.xml
python3 python_script.py $SOURCE_FILE ../sources/letter_after.xml

export XMLLINT_INDENT=$'\t'
xmllint --format - < ../sources/letter_after.xml > ../sources/after_linting.xml
rm ../sources/letter_after.xml
mv ../sources/after_linting.xml ../sources/letter_after.xml

ksdiff $SOURCE_FILE ../sources/letter_after.xml
