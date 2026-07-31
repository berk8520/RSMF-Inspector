import time
import os
import zipfile
import io
import base64
import zlib
import struct

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, 'CHAT - CB0000001 - 00019 - 2019-01-01 - CB0002084.rsmf') # 154 MB file!

t0 = time.perf_counter()

manifest_json_str = None
with open(sample_file, 'rb') as f:
    found_rsmf_zip = False
    in_b64 = False
    b64_chunks = []
    
    for line in f:
        l_strip = line.strip()
        if b'rsmf.zip' in l_strip.lower():
            found_rsmf_zip = True
            continue
        if found_rsmf_zip and not in_b64:
            if l_strip == b'':
                in_b64 = True
                continue
        if in_b64:
            if l_strip.startswith(b'--'):
                break
            b64_chunks.append(l_strip)
            
            # Read until local header for manifest is satisfied
            if len(b64_chunks) % 15 == 0:
                raw_b64 = b''.join(b64_chunks)
                pad = len(raw_b64) % 4
                if pad != 0:
                    raw_b64 += b'=' * (4 - pad)
                try:
                    zip_prefix = base64.b64decode(raw_b64)
                    idx = zip_prefix.find(b'PK\x03\x04')
                    if idx != -1:
                        comp_meth, mod_time, mod_date, crc, comp_size, uncomp_size, fn_len, extra_len = struct.unpack('<HHHIIIHH', zip_prefix[idx+8:idx+30])
                        fname = zip_prefix[idx+30:idx+30+fn_len].decode('utf-8', errors='ignore')
                        data_start = idx + 30 + fn_len + extra_len
                        if len(zip_prefix) >= data_start + comp_size:
                            comp_bytes = zip_prefix[data_start:data_start+comp_size]
                            manifest_bytes = zlib.decompress(comp_bytes, -15) if comp_meth == 8 else comp_bytes
                            manifest_json_str = manifest_bytes.decode('utf-8', errors='replace')
                            break
                except Exception:
                    pass

t1 = time.perf_counter()

print("INSTANT MANIFEST STREAM READER RESULT:")
print(f"  Time taken: {round((t1-t0)*1000, 2)} ms!")
print(f"  Manifest filename: {fname}")
print(f"  Manifest JSON length: {len(manifest_json_str)} characters")
