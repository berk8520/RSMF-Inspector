import os

csv_path = r"c:\code\python\RsmfInspector\scratch\batch_export_test_output\attachment_load_file.csv"
if os.path.exists(csv_path):
    with open(csv_path, "r", encoding="utf-8") as f:
        print(f.read())
