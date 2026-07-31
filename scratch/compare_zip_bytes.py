import os
import sys
import zipfile
import json
import email
import io

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def get_zip_bytes(file_path):
    zf, eml = RSMFParserService._open_zip_from_rsmf(file_path)
    # Extract raw zip bytes from EML attachment part
    for part in eml.walk():
        p_bytes = part.get_payload(decode=True)
        if p_bytes and zipfile.is_zipfile(io.BytesIO(p_bytes)):
            zf.close()
            return p_bytes
    zf.close()
    return None

mc_bytes = get_zip_bytes(os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml"))
ri_bytes = get_zip_bytes(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml"))

print(f"MessageCrawler Zip Bytes Length: {len(mc_bytes)}")
print(f"RSMFInspector Zip Bytes Length: {len(ri_bytes)}")

# Inspect zip file entries and compression types
print("\n--- MessageCrawler Zip Entries ---")
with zipfile.ZipFile(io.BytesIO(mc_bytes), 'r') as zf:
    for info in zf.infolist():
        print(f"  {info.filename}: size={info.file_size}, compress_size={info.compress_size}, type={info.compress_type}")

print("\n--- RSMFInspector Zip Entries ---")
with zipfile.ZipFile(io.BytesIO(ri_bytes), 'r') as zf:
    for info in zf.infolist():
        print(f"  {info.filename}: size={info.file_size}, compress_size={info.compress_size}, type={info.compress_type}")
