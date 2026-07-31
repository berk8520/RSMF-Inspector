import os
import sys
import zipfile
import json
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def check_all_events(p, name):
    zf, _ = RSMFParserService._open_zip_from_rsmf(p)
    m = json.loads(zf.read("rsmf_manifest.json").decode('utf-8'))
    zf.close()
    
    print(f"\n=== {name} ===")
    for idx, evt in enumerate(m['events']):
        atts = evt.get('attachments', [])
        if atts:
            print(f" Event {idx} ({evt['id']}): {len(atts)} attachment(s)")
            for a in atts:
                print(f"   - id: '{a.get('id')}', display: '{a.get('display')}', size: {a.get('size')}")

check_all_events(os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml"), "MessageCrawler")
check_all_events(os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml"), "RSMFInspector")
