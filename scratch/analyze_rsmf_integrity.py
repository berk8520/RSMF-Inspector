import os
import sys
import zipfile
import json

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def analyze_rsmf(p, name):
    print(f"\n==========================================")
    print(f"ANALYZING: {name}")
    print(f"==========================================")
    zf, eml = RSMFParserService._open_zip_from_rsmf(p)
    
    zip_files = set(zf.namelist())
    manifest_bytes = zf.read("rsmf_manifest.json")
    m = json.loads(manifest_bytes.decode('utf-8'))
    zf.close()
    
    manifest_att_ids = []
    for evt in m.get('events', []):
        for att in evt.get('attachments', []):
            manifest_att_ids.append((att.get('id'), att.get('display'), att.get('size')))
            
    print(f"ZIP File Entries ({len(zip_files)}): {sorted(list(zip_files))}")
    print(f"Manifest Attachment References ({len(manifest_att_ids)}):")
    for att_id, display, size in manifest_att_ids:
        in_zip = att_id in zip_files
        print(f"  - Manifest ID: '{att_id}' | Exists in ZIP: {in_zip} | Display: '{display}' | Size: {size}")

analyze_rsmf(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf"), "Original RSMF")
analyze_rsmf(os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml"), "MessageCrawler Stripped RSMF")
analyze_rsmf(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml"), "RSMFInspector Stripped RSMF")
