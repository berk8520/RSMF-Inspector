import os
import sys
import zipfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
target_export_dir = os.path.join(os.path.dirname(__file__), "export_output")

if os.path.exists(target_export_dir):
    shutil.rmtree(target_export_dir)

sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])
print(f"Testing RSMFExportService on: {os.path.basename(sample_file)}")

root_export, stripped_rsmf, att_count = RSMFExportService.export_stripped_rsmf(sample_file, target_export_dir)

print(f"\nEXPORT RESULTS:")
print(f"  Root Export Dir: {root_export}")
print(f"  Stripped RSMF File: {stripped_rsmf}")
print(f"  Attachments Extracted Count: {att_count}")

# Verify Root Directory
assert os.path.exists(root_export), "Root export folder should exist"

# Verify Companion attachments/ folder
att_folder = os.path.join(root_export, "attachments")
assert os.path.exists(att_folder), "attachments folder should exist"
extracted_files = os.listdir(att_folder)
print(f"  Extracted files in companion folder: {extracted_files}")
assert len(extracted_files) == att_count, "Extracted file count mismatch"

# Verify Stripped RSMF contains 0-byte attachment placeholders
zf_stripped, _ = RSMFParserService._open_zip_from_rsmf(stripped_rsmf)
print("\nStripped ZIP payload contents:")
for name in zf_stripped.namelist():
    size = zf_stripped.getinfo(name).file_size
    print(f"  - {name}: {size} bytes")
    if not name.lower().endswith('.json') and not name.endswith('/'):
        assert size == 0, f"Attachment {name} should be 0 bytes in stripped RSMF"

zf_stripped.close()

print("\nALL EXPORT VERIFICATION TESTS PASSED 100%!")
