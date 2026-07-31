import os
import sys
import email
import zipfile
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rsmf_inspector.services.rsmf_parser import RSMFParserService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

with open(sample_file, 'rb') as f:
    msg = email.message_from_binary_file(f)

for part in msg.walk():
    p_bytes = part.get_payload(decode=True)
    if p_bytes and zipfile.is_zipfile(io.BytesIO(p_bytes)):
        print("Found ZIP part:")
        print("  Content-Type:", part.get_content_type())
        print("  Content-Transfer-Encoding:", part.get('Content-Transfer-Encoding'))
        print("  Filename:", part.get_filename())
