import os
import sys
import zipfile
import json
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

mc_path = os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml")
ri_path = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml")
orig_path = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf")

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def get_manifest(p):
    zf, _ = RSMFParserService._open_zip_from_rsmf(p)
    data = zf.read("rsmf_manifest.json")
    zf.close()
    return json.loads(data.decode('utf-8'))

mc_m = get_manifest(mc_path)
ri_m = get_manifest(ri_path)
orig_m = get_manifest(orig_path)

print("=== MANIFEST DIFF ===")
print("MC keys:", list(mc_m.keys()))
print("RI keys:", list(ri_m.keys()))

print("\n--- MC Event 0 vs RI Event 0 ---")
print("MC Event 0:", json.dumps(mc_m['events'][0], indent=2))
print("RI Event 0:", json.dumps(ri_m['events'][0], indent=2))
