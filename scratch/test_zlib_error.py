import os
import zipfile
import zlib
import io

# Create a zip containing a compressed 0-byte file or corrupted stream
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("test.txt", b"")

buf.seek(0)
zf_read = zipfile.ZipFile(buf, 'r')
print("Standard 0-byte ZIP_DEFLATED file size:", zf_read.getinfo("test.txt").file_size)
print("Standard 0-byte ZIP_DEFLATED compress_size:", zf_read.getinfo("test.txt").compress_size)
data = zf_read.read("test.txt")
print("Read data length:", len(data))

# Simulating corrupt/truncated zlib payload
corrupt_bytes = b"x\x9c\x03\x00\x00\x00\x00\x01"  # Invalid zlib block
try:
    zlib.decompress(corrupt_bytes)
except zlib.error as ex:
    print(f"Caught expected zlib error: {ex}")
