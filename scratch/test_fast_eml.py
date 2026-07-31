import time
import os
import zipfile
import io
import base64

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, 'CHAT - CB0000001 - 00019 - 2019-01-01 - CB0002084.rsmf') # 154 MB file!

t0 = time.perf_counter()

# Fast RSMF Stream Reader: Extract ONLY rsmf.zip part and stop immediately!
zip_bytes = None
with open(sample_file, 'rb') as f:
    found_rsmf_zip = False
    in_b64 = False
    b64_chunks = []
    
    for line in f:
        l_strip = line.strip()
        if b'filename=rsmf.zip' in l_strip.lower() or b'name=rsmf.zip' in l_strip.lower() or b'filename="rsmf.zip"' in l_strip.lower():
            found_rsmf_zip = True
            continue
        if found_rsmf_zip and not in_b64:
            if l_strip == b'': # Blank line before Base64 data
                in_b64 = True
                continue
        if in_b64:
            if l_strip.startswith(b'--'): # Next MIME boundary reached! STOP READING FILE!
                break
            b64_chunks.append(l_strip)

    if b64_chunks:
        raw_b64 = b''.join(b64_chunks)
        zip_bytes = base64.b64decode(raw_b64)

t1 = time.perf_counter()

if zip_bytes:
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    manifest_data = zf.read('rsmf_manifest.json')
    t2 = time.perf_counter()
    print(f"FAST RSMF STREAM READER SUCCESS!")
    print(f"  Stream extraction time: {round((t1-t0)*1000, 2)} ms")
    print(f"  Total time (including zip read): {round((t2-t0)*1000, 2)} ms")
    print(f"  rsmf.zip size: {len(zip_bytes)} bytes | Manifest size: {len(manifest_data)} bytes")
else:
    print("Failed to find rsmf.zip via fast stream reader")
