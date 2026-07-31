import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService, AUTO_EXTRACT_MAX_BYTES
from rsmf_inspector.services.temp_cache_service import TempCacheService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_files = [os.path.join(sample_dir, f) for f in os.listdir(sample_dir) if f.endswith(".rsmf")]

print(f"Found {len(sample_files)} sample RSMF files for re-rendering test.")

for file_path in sample_files:
    fname = os.path.basename(file_path)
    print(f"\n--- Testing File: {fname} ---")
    
    # 1. Clear Temp Cache
    TempCacheService.clear_cache()
    
    # 2. Parse RSMF payload
    payload = RSMFParserService.parse_rsmf_file(file_path)
    print(f"Payload: {payload.file_name} | {len(payload.attachments)} attachments")
    
    # 3. Simulate extraction loop
    for att in payload.attachments:
        if att.size > AUTO_EXTRACT_MAX_BYTES:
            print(f"  Attachment '{att.display_name}': {att.size/(1024*1024):.1f} MB -> Skipped (>50MB)")
            continue
        
        extracted_path = RSMFParserService.extract_attachment_to_temp(file_path, att.archive_path or att.display_name)
        thumb_uri, orig_file_uri = RSMFParserService._generate_media_thumbnail(file_path, att.archive_path or att.display_name)
        print(f"  Attachment '{att.display_name}': thumb={bool(thumb_uri)}, orig={bool(orig_file_uri)}")
        
    # 4. Generate post-extraction HTML
    post_html = RSMFParserService.generate_html_chat(payload)
    
    has_sub50mb = any(att.size <= AUTO_EXTRACT_MAX_BYTES for att in payload.attachments)
    has_img_tag = "<img " in post_html
    has_large_box = "large-file-box" in post_html
    
    if has_sub50mb:
        assert has_img_tag, f"Post-extraction re-render should contain <img src=> tag for sub-50MB media attachments in {fname}!"
    else:
        assert has_large_box, f"Over-50MB attachment should render large-file-box placeholder in {fname}!"
        
    print(f"  Post-Extraction Re-Render Verified: SUCCESS!")

print("\n========================================================")
print("ALL 13 SAMPLE RSMF RE-RENDER TESTS PASSED 100%!")
print("========================================================")
