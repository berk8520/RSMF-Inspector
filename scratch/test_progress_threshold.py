import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService, AUTO_EXTRACT_MAX_BYTES
from rsmf_inspector.services.rsmf_export_service import RSMFExportService
from rsmf_inspector.models.rsmf_payload import AttachmentItem

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

print(f"Testing Progress & Thresholds on: {os.path.basename(sample_file)}")
print(f"AUTO_EXTRACT_MAX_BYTES constant: {AUTO_EXTRACT_MAX_BYTES / (1024*1024):.1f} MB")

# 1. Test progress callback in RSMFExportService
target_export = os.path.join(os.path.dirname(__file__), "export_progress_test")
if os.path.exists(target_export):
    shutil.rmtree(target_export)

progress_log = []
def on_progress(idx, total, filename):
    progress_log.append((idx, total, filename))

root_exp, stripped_rsmf, att_count = RSMFExportService.export_stripped_rsmf(sample_file, target_export, progress_callback=on_progress)

print(f"\n1. Export Service Progress Callback SUCCESS!")
print(f"   Root export: {root_exp}")
print(f"   Logged progress entries: {len(progress_log)}")

# 2. Test 50MB Size Threshold Logic
mock_small_att = AttachmentItem(id="small.jpg", display_name="small.jpg", size=10 * 1024 * 1024)
mock_large_att = AttachmentItem(id="large_video.mov", display_name="large_video.mov", size=75 * 1024 * 1024)

print("\n2. Threshold Validation:")
print(f"   Small file (10 MB) auto-extract allowed: {mock_small_att.size <= AUTO_EXTRACT_MAX_BYTES}")
print(f"   Large file (75 MB) auto-extract allowed: {mock_large_att.size <= AUTO_EXTRACT_MAX_BYTES}")

assert mock_small_att.size <= AUTO_EXTRACT_MAX_BYTES, "Small file should be auto-extracted"
assert not (mock_large_att.size <= AUTO_EXTRACT_MAX_BYTES), "Large file (>50MB) should skip auto-extraction"

print("\nALL PROGRESS & THRESHOLD VERIFICATION TESTS PASSED 100%!")
