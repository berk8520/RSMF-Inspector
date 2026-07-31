import os
import sys
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.async_workers import RSMFParseWorker, ThumbnailWorker, AttachmentExtractWorker

app = QApplication.instance() or QApplication(sys.argv)

sample_dir = r"C:\Users\BDoering\OneDrive - Page One Legal\Documents\__Working\_Throwaway\SampleRSMF"
sample_file = os.path.join(sample_dir, os.listdir(sample_dir)[0])

print(f"Testing Async Pipeline on: {os.path.basename(sample_file)}")

# 1. Test Async RSMFParseWorker QThread
parse_worker = RSMFParseWorker(sample_file)

def on_parsed(payload):
    print(f"\n1. RSMFParseWorker SUCCESS!")
    print(f"   Payload: {payload.file_name} | {payload.participant_count} Parts | {payload.event_count} Events")
    
    # 2. Test Instant Placeholder HTML Generation
    html_out = RSMFParserService.generate_html_chat(payload)
    print("2. Instant Placeholder HTML generated!")
    assert "thumb-placeholder" in html_out or "No message events" in html_out
    
    # 3. Test ThumbnailWorker
    media_tuples = RSMFParserService.get_media_attachment_tuples(payload)
    if media_tuples:
        print(f"   Found {len(media_tuples)} media attachments for background thumbnailing.")
        thumb_worker = ThumbnailWorker(sample_file, media_tuples)
        def on_thumb(att_id, thumb_uri, orig_uri):
            print(f"3. ThumbnailWorker SUCCESS! att_id={att_id} -> thumb={thumb_uri[:40]}...")
        thumb_worker.thumbnail_ready.connect(on_thumb)
        thumb_worker.finished.connect(test_attachment_worker)
        thumb_worker.start()
    else:
        test_attachment_worker()

def test_attachment_worker():
    print("\n4. Testing AttachmentExtractWorker QThread...")
    payload = RSMFParserService.parse_rsmf_file(sample_file)
    if payload.attachments:
        att = payload.attachments[0]
        ext_worker = AttachmentExtractWorker(sample_file, att.archive_path or att.display_name, att.id)
        
        def on_started(att_id):
            print(f"   Status Indicator: ⏳ Extracting {att_id}...")
        def on_finished(att_id, path):
            print(f"   Status Indicator: ✅ Ready 📎 Extracted to {path}")
            print("\nALL ASYNC PIPELINE VERIFICATION TESTS PASSED 100%!")
            app.quit()
            
        ext_worker.started.connect(on_started)
        ext_worker.finished.connect(on_finished)
        ext_worker.start()
    else:
        print("\nALL ASYNC PIPELINE VERIFICATION TESTS PASSED 100%!")
        app.quit()

parse_worker.finished.connect(on_parsed)
parse_worker.start()

app.exec()
