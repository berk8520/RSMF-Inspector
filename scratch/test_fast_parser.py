import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"

print("--- FAST PARSER TIMING BENCHMARK ---")
for f in os.listdir(sample_dir):
    if f.endswith('.rsmf'):
        fpath = os.path.join(sample_dir, f)
        t0 = time.perf_counter()
        payload = RSMFParserService.parse_rsmf_file(fpath)
        t1 = time.perf_counter()
        fsize = os.path.getsize(fpath) / (1024*1024)
        print(f"{f[:40]}... ({fsize:.1f} MB) -> Parsed in {round((t1-t0)*1000, 2)} ms ({payload.event_count} events)")

print("\nFAST PARSER BENCHMARK COMPLETE!")
