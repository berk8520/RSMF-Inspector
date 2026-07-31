import os
import sys
import email
import zipfile
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

target_out = os.path.join(os.path.dirname(__file__), "debug_eml_export")
if os.path.exists(target_out):
    import shutil
    shutil.rmtree(target_out)

root_exp, stripped_rsmf, count, records = RSMFExportService.export_stripped_rsmf(sample_file, target_out)
print(f"Exported stripped RSMF to: {stripped_rsmf}")

# Check if stripped RSMF can be parsed by RSMFParserService
try:
    payload = RSMFParserService.parse_rsmf_file(stripped_rsmf)
    print("RSMFParserService successfully parsed stripped RSMF file!")
except Exception as ex:
    print(f"ERROR parsing stripped RSMF file with RSMFParserService: {type(ex).__name__}: {ex}")

# Check inner zip payload directly
try:
    zf, eml = RSMFParserService._open_zip_from_rsmf(stripped_rsmf)
    print("Inner zip entries:", zf.namelist())
    for name in zf.namelist():
        info = zf.getinfo(name)
        print(f"  Entry '{name}': file_size={info.file_size}, compress_size={info.compress_size}, compress_type={info.compress_type}")
    zf.close()
except Exception as ex:
    print(f"ERROR reading inner zip from stripped RSMF: {type(ex).__name__}: {ex}")
