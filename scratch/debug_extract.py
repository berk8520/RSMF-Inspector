import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.temp_cache_service import TempCacheService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"

print("--- TESTING ALL SAMPLE RSMF ATTACHMENT EXTRACTIONS ---")
for f in os.listdir(sample_dir):
    if f.endswith('.rsmf'):
        file_path = os.path.join(sample_dir, f)
        print(f"\nContainer: {f}")
        
        # Test standard parse
        zf, eml = RSMFParserService._open_zip_from_rsmf(file_path)
        try:
            file_list = zf.namelist()
            print(f"  Zip entries found ({len(file_list)}): {file_list}")
            for entry in file_list:
                if not entry.endswith('/') and not entry.lower().endswith('.json'):
                    info = zf.getinfo(entry)
                    print(f"    - Attachment: '{entry}' ({info.file_size} bytes)")
                    ext_path = RSMFParserService.extract_attachment_to_temp(file_path, entry)
                    print(f"      Extracted -> {os.path.basename(ext_path)}")
        finally:
            zf.close()
