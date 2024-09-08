LETTER_FOLDER=../letters/ш
FILENAME=simple_minicards.xml
cd $LETTER_FOLDER

fileExtension="${FILENAME##*.}"
filename_no_extension="${FILENAME%.*}"
fileAfterScript="${filename_no_extension}_after_script.${fileExtension}"
fileAfterLinting="${filename_no_extension}_after_linting.${fileExtension}"

python3 ../../scripts/python_script.py $FILENAME $fileAfterScript

export XMLLINT_INDENT=$'\t'
xmllint --format - < $fileAfterScript > $fileAfterLinting
rm $fileAfterScript

ksdiff $FILENAME $fileAfterLinting