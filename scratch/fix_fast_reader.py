import time
import os
import zipfile
import base64
import zlib
import struct

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
file_path = os.path.join(sample_dir, 'CHAT - CB0000001 - 00019 - 2019-01-01 - CB0002084.rsmf') # 154 MB file!

def fast_extract_manifest_bytes(file_path: str):
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        f.seek(0)
        
        # Case 1: Raw ZIP file on disk
        if magic == b'PK\x03\x04':
            with zipfile.ZipFile(f) as zf:
                for name in zf.namelist():
                    if name.lower().endswith('.json'):
                        return zf.read(name)
            return None

        # Case 2: EML MIME Wrapper
        b64_chunks = []
        found_zip_part = False
        in_b64 = False
        
        for line in f:
            l_strip = line.strip()
            l_lower = l_strip.lower()
            if b'rsmf.zip' in l_lower:
                found_zip_part = True
                continue
            if found_zip_part and not in_b64:
                if l_strip == b'':
                    in_b64 = True
                    continue
            if in_b64:
                if l_strip.startswith(b'--'):
                    break
                b64_chunks.append(l_strip)
                
                # Check header chunk every 10 lines
                if len(b64_chunks) >= 20 and len(b64_chunks) % 10 == 0:
                    raw_b64 = b''.join(b64_chunks)
                    pad_needed = (4 - (len(raw_b64) % 4)) % 4
                    if pad_needed:
                        raw_b64 += b'=' * pad_needed
                    try:
                        temp_raw = base64.b64decode(raw_b64)
                        idx = temp_raw.find(b'PK\x03\x04')
                        if idx != -1:
                            comp_meth, mod_time, mod_date, crc, comp_size, uncomp_size, fn_len, extra_len = struct.unpack('<HHHIIIHH', temp_raw[idx+8:idx+30])
                            data_start = idx + 30 + fn_len + extra_len
                            if len(temp_raw) >= data_start + comp_size:
                                comp_bytes = temp_raw[data_start:data_start+comp_size]
                                return zlib.decompress(comp_bytes, -15) if comp_meth == 8 else comp_bytes
                    except Exception:
                        pass
                    
                if len(b64_chunks) >= 500:
                    break

    return None

t0 = time.perf_counter()
manifest_bytes = fast_extract_manifest_bytes(file_path)
t1 = time.perf_counter()

print("FIXED FAST MANIFEST STREAM READER RESULT:")
print(f"  Time taken: {round((t1-t0)*1000, 2)} ms!")
print(f"  Manifest bytes found: {manifest_bytes is not None}")
if manifest_bytes:
    print(f"  Manifest size: {len(manifest_bytes)} bytes")
