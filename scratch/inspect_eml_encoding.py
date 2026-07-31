import os
import sys
import email

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

target_out = os.path.join(os.path.dirname(__file__), "debug_eml_export")

root_exp, stripped_rsmf, count, records = RSMFExportService.export_stripped_rsmf(sample_file, target_out)

with open(stripped_rsmf, 'rb') as f:
    msg = email.message_from_binary_file(f)

for part in msg.walk():
    cte = part.get('Content-Transfer-Encoding')
    ct = part.get_content_type()
    payload = part.get_payload(decode=False)
    print(f"Part content_type={ct}, encoding={cte}")
    if isinstance(payload, str):
        print(f"  First 100 chars of string payload: {payload[:100]}")
    else:
        print(f"  Payload type: {type(payload)}")
