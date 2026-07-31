import os
import sys
import shutil

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_export_service import RSMFExportService
from rsmf_inspector.services.rsmf_parser import RSMFParserService

out_dir = os.path.join(os.path.dirname(__file__), "test_all_stripped_parse")
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir, exist_ok=True)

for f in os.listdir(sample_dir):
    full_p = os.path.join(sample_dir, f)
    if os.path.isfile(full_p) and f.lower().endswith(('.rsmf', '.zip')):
        print(f"Exporting & validating stripped RSMF for: {f}")
        root_exp, stripped_rsmf, count, records = RSMFExportService.export_stripped_rsmf(full_p, out_dir)
        try:
            payload = RSMFParserService.parse_rsmf_file(stripped_rsmf)
            print(f"  OK! Manifest: {payload.manifest_name}, Attachments: {len(payload.attachments)}")
        except Exception as ex:
            print(f"  FAILED to parse stripped RSMF: {type(ex).__name__}: {ex}")
