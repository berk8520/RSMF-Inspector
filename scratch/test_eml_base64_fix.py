import os
import sys
import email
import base64
import zipfile
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rsmf_inspector.services.rsmf_export_service import RSMFExportService
from rsmf_inspector.services.rsmf_parser import RSMFParserService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

target_out = os.path.join(os.path.dirname(__file__), "test_base64_fix")

root_exp, stripped_rsmf, count, records = RSMFExportService.export_stripped_rsmf(sample_file, target_out)

print("Exported stripped file:", stripped_rsmf)

# Test reading with RSMFParserService
try:
    payload = RSMFParserService.parse_rsmf_file(stripped_rsmf)
    print("SUCCESSFULLY PARSED STRIPPED RSMF FILE WITH RSMFParserService!")
    print(f"Manifest Name: {payload.manifest_name}, Attachments: {len(payload.attachments)}")
except Exception as ex:
    print(f"FAILED to parse stripped file: {type(ex).__name__}: {ex}")
