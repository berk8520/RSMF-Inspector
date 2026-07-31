import os
import zipfile
import io
import shutil

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"

for f in os.listdir(sample_dir):
    full_p = os.path.join(sample_dir, f)
    if os.path.isfile(full_p) and f.lower().endswith(('.rsmf', '.zip')):
        if zipfile.is_zipfile(full_p):
            zf = zipfile.ZipFile(full_p, 'r')
            zip_entries = zf.namelist()
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                for entry in zip_entries:
                    if entry.endswith('/'):
                        continue
                    zf_out.writestr(entry, b"")
            bytes_out = buf.getvalue()
            # Try reading back zip file
            try:
                zf_check = zipfile.ZipFile(io.BytesIO(bytes_out), 'r')
                for name in zf_check.namelist():
                    data = zf_check.read(name)
                zf_check.close()
            except Exception as ex:
                print(f"FAILED on file {f}: {ex}")
            zf.close()
