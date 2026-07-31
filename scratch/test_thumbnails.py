import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"

for fname in os.listdir(sample_dir):
    fpath = os.path.join(sample_dir, fname)
    payload = RSMFParserService.parse_rsmf_file(fpath)
    html_out = RSMFParserService.generate_html_chat(payload)
    has_img = "<img src=" in html_out
    has_outgoing = 'align="right"' in html_out
    has_incoming = 'align="left"' in html_out
    print(f"FILE: {fname}")
    print(f"  Events: {payload.event_count} | Inline Thumbnails: {has_img} | Right (Out): {has_outgoing} | Left (In): {has_incoming}")
    for ev in payload.events:
        print(f"    - Event {ev.id}: dir={ev.direction}, body={repr(ev.body[:40])}")
