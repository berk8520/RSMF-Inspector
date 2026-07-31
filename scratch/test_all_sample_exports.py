import os
import sys
import shutil

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_export_service import RSMFExportService

out_dir = os.path.join(os.path.dirname(__file__), "test_all_export")
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir, exist_ok=True)

for f in os.listdir(sample_dir):
    full_p = os.path.join(sample_dir, f)
    if os.path.isfile(full_p) and f.lower().endswith(('.rsmf', '.zip')):
        print(f"Exporting: {f}")
        try:
            RSMFExportService.export_stripped_rsmf(full_p, out_dir)
            print(f"  OK")
        except Exception as ex:
            print(f"  FAILED: {type(ex).__name__}: {ex}")
