cp letter_wip.xml letter_after.xml

python3 remove_weird_formatting.py
python3 python_script.py

export XMLLINT_INDENT=$'\t'
xmllint --format - < letter_after.xml > after_linting.xml
rm letter_after.xml
mv after_linting.xml letter_after.xml

ksdiff letter_wip.xml letter_after.xml
