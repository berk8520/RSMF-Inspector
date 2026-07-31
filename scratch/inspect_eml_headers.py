import os
import sys
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

mc_eml = os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml")
ri_eml = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml")
orig_rsmf = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf")

def inspect_eml_full(label, path):
    print(f"\n========================================================")
    print(f"FULL EML INSPECTION: {label}")
    print(f"========================================================")
    with open(path, 'rb') as f:
        msg = email.message_from_binary_file(f)
        
    print("Top-level headers:")
    for k, v in msg.items():
        print(f"  {k}: {v}")
        
    print(f"\nMultipart walk (total parts: {len(list(msg.walk()))}):")
    for idx, part in enumerate(msg.walk()):
        print(f" Part {idx}:")
        print(f"   Content-Type: {part.get_content_type()}")
        print(f"   Content-Transfer-Encoding: {part.get('Content-Transfer-Encoding')}")
        print(f"   Content-Disposition: {part.get('Content-Disposition')}")
        print(f"   Filename: {part.get_filename()}")

inspect_eml_full("MessageCrawler EML", mc_eml)
inspect_eml_full("RSMFInspector EML", ri_eml)
inspect_eml_full("Original EML", orig_rsmf)
