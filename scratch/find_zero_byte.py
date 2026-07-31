import os
import sys
import zipfile

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

for f in os.listdir(sample_dir):
    full_p = os.path.join(sample_dir, f)
    if os.path.isfile(full_p):
        try:
            zf, _ = RSMFParserService._open_zip_from_rsmf(full_p)
            for name in zf.namelist():
                info = zf.getinfo(name)
                # Check for 0-byte or compressed data issues
                if info.file_size == 0 and not name.endswith('/'):
                    print(f"File {f} has 0-byte file: {name} (compress_type={info.compress_type})")
            zf.close()
        except Exception as ex:
            print(f"Error inspecting {f}: {ex}")
