import os
import zipfile
import io

# Create a zip containing duplicate entry names
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr("attachments/test.txt", b"Hello World")
    zf.writestr("attachments/test.txt", b"Hello World Duplicate")

buf.seek(0)
zf_in = zipfile.ZipFile(buf, 'r')
print(f"Zip namelist: {zf_in.namelist()}")

# Write stripped zip
buf_out = io.BytesIO()
with zipfile.ZipFile(buf_out, 'w', zipfile.ZIP_DEFLATED) as zf_out:
    for entry in zf_in.namelist():
        zf_out.writestr(entry, b"")

buf_out.seek(0)
try:
    zf_check = zipfile.ZipFile(buf_out, 'r')
    for name in zf_check.namelist():
        data = zf_check.read(name)
        print(f"Read '{name}': {len(data)} bytes")
    zf_check.close()
    print("Duplicate name zip read cleanly!")
except Exception as ex:
    print(f"Duplicate zip read error: {type(ex).__name__}: {ex}")
