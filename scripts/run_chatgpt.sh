chatGPT_folder=../chatGPT_exp
test_dict=$chatGPT_folder/test_dict.xml
debug_dict=$chatGPT_folder/debug_dict.xml

input_dict=$test_dict
converted_dict=$chatGPT_folder/chatGPT_output.xml

python3 chatgpt_test.py $input_dict $converted_dict

ksdiff $input_dict $converted_dict
