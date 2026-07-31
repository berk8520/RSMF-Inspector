import os
import sys
import json
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def get_manifest_dict(file_path):
    zf, _ = RSMFParserService._open_zip_from_rsmf(file_path)
    for name in zf.namelist():
        if name.lower().endswith('.json'):
            data = zf.read(name)
            zf.close()
            return json.loads(data.decode('utf-8'))
    zf.close()
    return None

mc_manifest = get_manifest_dict(os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml"))
ri_manifest = get_manifest_dict(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml"))
orig_manifest = get_manifest_dict(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf"))

print("=== Message Crawler Manifest Keys ===")
print(list(mc_manifest.keys()))

def inspect_events(manifest, name):
    print(f"\n--- {name} Events (total: {len(manifest.get('events', []))}) ---")
    att_events = []
    for evt in manifest.get('events', []):
        if 'attachments' in evt or evt.get('type') == 'attachment':
            att_events.append(evt)
    print(f"Events with attachments / attachment type: {len(att_events)}")
    if att_events:
        print("Sample attachment event:")
        print(json.dumps(att_events[0], indent=2))

inspect_events(orig_manifest, "Original")
inspect_events(mc_manifest, "MessageCrawler")
inspect_events(ri_manifest, "RSMFInspector")
