import time
import os
import zipfile
import io
import base64
import zlib
import struct

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"

def fast_extract_manifest(file_path):
    t0 = time.perf_counter()
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        f.seek(0)
        
        if magic == b'PK\x03\x04':
            zf = zipfile.ZipFile(f)
            for name in zf.namelist():
                if name.lower().endswith('.json'):
                    data = zf.read(name)
                    t1 = time.perf_counter()
                    return (t1 - t0) * 1000, len(data)

        b64_lines = []
        found_zip = False
        in_b64 = False
        
        for line in f:
            l_lower = line.lower()
            if b'rsmf.zip' in l_lower:
                found_zip = True
                continue
            if found_zip and not in_b64:
                if line.strip() == b'':
                    in_b64 = True
                    continue
            if in_b64:
                if line.startswith(b'--'):
                    break
                b64_lines.append(line.strip())
                
                if len(b64_lines) % 20 == 0:
                    try:
                        raw = b''.join(b64_lines)
                        pad = len(raw) % 4
                        if pad != 0:
                            raw += b'=' * (4 - pad)
                        temp_raw = base64.b64decode(raw)
                        idx = temp_raw.find(b'PK\x03\x04')
                        if idx != -1:
                            comp_meth, mod_time, mod_date, crc, comp_size, uncomp_size, fn_len, extra_len = struct.unpack('<HHHIIIHH', temp_raw[idx+8:idx+30])
                            data_start = idx + 30 + fn_len + extra_len
                            if len(temp_raw) >= data_start + comp_size:
                                comp_bytes = temp_raw[data_start:data_start+comp_size]
                                decomp_json = zlib.decompress(comp_bytes, -15) if comp_meth == 8 else comp_bytes
                                t1 = time.perf_counter()
                                return (t1 - t0) * 1000, len(decomp_json)
                    except Exception:
                        pass

    return 0, 0

print("--- BENCHMARK RESULTS ---")
for f in os.listdir(sample_dir):
    if f.endswith('.rsmf'):
        fpath = os.path.join(sample_dir, f)
        ms, sz = fast_extract_manifest(fpath)
        fsize = os.path.getsize(fpath)/(1024*1024)
        print(f"{f[:35]}... ({fsize:.1f} MB) -> Manifest extracted in {ms:.2f} ms ({sz} bytes)")
