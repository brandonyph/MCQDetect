python .\1-sheet_generator\mcq_generator.py --output .\Output\mcq_answer_sheet.png

python .\2-filled_generator\mcq_auto_filler.py --intensity 0.8 .\Output\mcq_answer_sheet.png --output .\Output\filled_answer_sheet.png

python .\3-crop_straighted\image_straightener.py

python .\4-mcq_detect\mcq_scanner.py .\Output\croppedstraighten_answer_sheet.png -o .\Output\ -f my_answers.json --debug

python .\5-jsontocsv\json_to_csv_exporter.py --input .\Output\my_answers.json --output .\Output\results.csv
