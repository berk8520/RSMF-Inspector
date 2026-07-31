import os
import sys
import zipfile
import email

folder = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF\MalformedSplit"

sys.path.insert(0, r"c:\code\python\RsmfInspector")
from rsmf_inspector.services.rsmf_parser import RSMFParserService

def diff_zips(label1, path1, label2, path2):
    print(f"\n========================================================")
    print(f"COMPARING ZIP PAYLOADS: {label1} vs {label2}")
    print(f"========================================================")
    zf1, eml1 = RSMFParserService._open_zip_from_rsmf(path1)
    zf2, eml2 = RSMFParserService._open_zip_from_rsmf(path2)
    
    names1 = set(zf1.namelist())
    names2 = set(zf2.namelist())
    
    print(f"{label1} entries ({len(names1)}):", sorted(list(names1)))
    print(f"{label2} entries ({len(names2)}):", sorted(list(names2)))
    
    print(f"\nEntries in {label1} but not in {label2}:", sorted(list(names1 - names2)))
    print(f"Entries in {label2} but not in {label1}:", sorted(list(names2 - names1)))
    
    for common in sorted(list(names1 & names2)):
        i1 = zf1.getinfo(common)
        i2 = zf2.getinfo(common)
        print(f"\nComparing '{common}':")
        print(f"  {label1}: size={i1.file_size}, compress_size={i1.compress_size}, compress_type={i1.compress_type}, flag_bits={i1.flag_bits}")
        print(f"  {label2}: size={i2.file_size}, compress_size={i2.compress_size}, compress_type={i2.compress_type}, flag_bits={i2.flag_bits}")
    
    zf1.close()
    zf2.close()

mc_eml = os.path.join(folder, "CB0000049_MessageCrawlerStrippedAttachments.rsmf.eml")
ri_eml = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049_stripped.rsmf.eml")
orig_rsmf = os.path.join(folder, "CHAT - CB0000001 - 00001 - 2017-05-12 - CB0000049.rsmf")

diff_zips("MessageCrawler", mc_eml, "RSMFInspector", ri_eml)
diff_zips("Original", orig_rsmf, "RSMFInspector", ri_eml)
