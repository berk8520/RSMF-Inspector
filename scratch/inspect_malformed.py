import os
import sys
import zipfile
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

print("=== 1. Inspecting File List & Sizes ===")
for f in os.listdir(folder):
    p = os.path.join(folder, f)
    print(f"File: {f} ({os.path.getsize(p)} bytes)")

def inspect_rsmf(file_path):
    print(f"\n========================================================")
    print(f"INSPECTING: {os.path.basename(file_path)}")
    print(f"========================================================")
    zf, eml_msg = RSMFParserService._open_zip_from_rsmf(file_path)
    
    if eml_msg:
        print("EML Container detected.")
        print("  EML Headers:")
        for k, v in eml_msg.items():
            if k.lower() in ('subject', 'from', 'to', 'content-type', 'mime-version'):
                print(f"    {k}: {v}")
    else:
        print("Raw ZIP Container detected.")

    print("\nZIP Payload Entry List:")
    for name in zf.namelist():
        info = zf.getinfo(name)
        print(f"  - {name} (size: {info.file_size} bytes, compress_size: {info.compress_size} bytes, compress_type: {info.compress_type})")

    # Read manifest json
    manifest_name = None
    for n in zf.namelist():
        if n.lower().endswith('.json'):
            manifest_name = n
            break
    if manifest_name:
        data = zf.read(manifest_name).decode('utf-8', errors='ignore')
        print(f"\nManifest Name: {manifest_name}")
        print(f"Manifest JSON snippet (first 300 chars):\n{data[:300]}")
    zf.close()

# Inspect Message Crawler output
mc_eml = os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml")
if os.path.exists(mc_eml):
    inspect_rsmf(mc_eml)

# Inspect RSMF Inspector stripped output
ri_eml = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml")
if os.path.exists(ri_eml):
    inspect_rsmf(ri_eml)

# Inspect original RSMF
orig_rsmf = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf")
if os.path.exists(orig_rsmf):
    inspect_rsmf(orig_rsmf)

# Also check MC.zip and RI.zip if present
for zname in ("MC.zip", "RI.zip"):
    zp = os.path.join(folder, zname)
    if os.path.exists(zp):
        print(f"\n--- Direct ZIP Inspection: {zname} ---")
        with zipfile.ZipFile(zp, 'r') as zf:
            for name in zf.namelist():
                info = zf.getinfo(name)
                print(f"  - {name} (size: {info.file_size} bytes, compress_size: {info.compress_size} bytes)")
