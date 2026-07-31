import os
import sys
import shutil
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
target_export_dir = os.path.join(os.path.dirname(__file__), "batch_export_test_output")

if os.path.exists(target_export_dir):
    shutil.rmtree(target_export_dir)
os.makedirs(target_export_dir, exist_ok=True)

sample_files = [
    os.path.join(sample_dir, f) for f in os.listdir(sample_dir)
    if f.lower().endswith(('.rsmf', '.zip'))
]

print(f"Found {len(sample_files)} sample files for test run.")
assert len(sample_files) > 0, "No sample RSMF files found!"

csv_path = os.path.join(target_export_dir, "attachment_load_file.csv")

# Test 1: Export first file
file1 = sample_files[0]
print(f"\n--- Test 1: Exporting File 1 ({os.path.basename(file1)}) ---")
root_exp1, stripped_rsmf1, att_count1, att_records1 = RSMFExportService.export_stripped_rsmf(file1, target_export_dir)

# Verify Manifest JSON output
base_name_no_ext1 = os.path.splitext(os.path.basename(file1))[0]
expected_manifest_name1 = f"{base_name_no_ext1}_rsmf_manifest.json"
expected_manifest_path1 = os.path.join(root_exp1, expected_manifest_name1)
assert os.path.exists(expected_manifest_path1), f"Manifest file missing: {expected_manifest_path1}"
print(f"Manifest JSON verified: {expected_manifest_name1}")

# Write to CSV
RSMFExportService.write_attachment_load_file(csv_path, att_records1, append_mode=False)
assert os.path.exists(csv_path), "CSV load file should exist"

with open(csv_path, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))
    print(f"CSV line count after File 1: {len(reader)}")
    assert reader[0] == ["AttachmentID", "Relative Path"], "CSV Header mismatch"
    assert len(reader) == att_count1 + 1, f"Expected {att_count1 + 1} rows in CSV, got {len(reader)}"

# Test 2: If second sample file exists, export with append_mode=True
if len(sample_files) > 1:
    file2 = sample_files[1]
    print(f"\n--- Test 2: Exporting File 2 ({os.path.basename(file2)}) with append_mode=True ---")
    root_exp2, stripped_rsmf2, att_count2, att_records2 = RSMFExportService.export_stripped_rsmf(file2, target_export_dir)

    base_name_no_ext2 = os.path.splitext(os.path.basename(file2))[0]
    expected_manifest_name2 = f"{base_name_no_ext2}_rsmf_manifest.json"
    expected_manifest_path2 = os.path.join(root_exp2, expected_manifest_name2)
    assert os.path.exists(expected_manifest_path2), f"Manifest file missing: {expected_manifest_path2}"
    print(f"Manifest JSON verified: {expected_manifest_name2}")

    RSMFExportService.write_attachment_load_file(csv_path, att_records2, append_mode=True)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        print(f"CSV line count after File 2 (Appended): {len(reader)}")
        assert len(reader) == att_count1 + att_count2 + 1, "Appended CSV count mismatch"

print("\nALL VERIFICATION TESTS COMPLETED 100% SUCCESSFULLY!")

