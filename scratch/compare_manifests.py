import os
import sys
import zipfile
import json
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

mc_eml = os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml")
ri_eml = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml")
orig_rsmf = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf")

def get_manifest_dict(file_path):
    zf, _ = RSMFParserService._open_zip_from_rsmf(file_path)
    for name in zf.namelist():
        if name.lower().endswith('.json'):
            data = zf.read(name)
            zf.close()
            return json.loads(data.decode('utf-8'))
    zf.close()
    return None

mc_manifest = get_manifest_dict(mc_eml)
ri_manifest = get_manifest_dict(ri_eml)
orig_manifest = get_manifest_dict(orig_rsmf)

print("=== MANIFEST ATTACHMENTS COMPARISON ===")
print(f"Original Manifest Attachments Count: {len(orig_manifest.get('attachments', []))}")
print(f"MessageCrawler Manifest Attachments Count: {len(mc_manifest.get('attachments', []))}")
print(f"RSMFInspector Manifest Attachments Count: {len(ri_manifest.get('attachments', []))}")

print("\n--- Message Crawler Attachments Array ---")
print(json.dumps(mc_manifest.get('attachments', []), indent=2))

print("\n--- RSMF Inspector Attachments Array ---")
print(json.dumps(ri_manifest.get('attachments', []), indent=2))

print("\n--- Original Attachments Array ---")
print(json.dumps(orig_manifest.get('attachments', []), indent=2))
