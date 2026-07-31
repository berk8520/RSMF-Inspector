import os
import sys
import json
import zipfile

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.validator_bridge import ValidatorBridge

def create_sample_rsmf(output_zip_path: str):
    manifest_data = {
        "version": "2.0.0",
        "participants": [
            {
                "id": "p1@ediscovery.local",
                "display": "Sarah Jenkins",
                "email": "sarah.jenkins@ediscovery.local",
                "account_id": "ACC-1001"
            },
            {
                "id": "p2@ediscovery.local",
                "display": "David Ross",
                "email": "david.ross@ediscovery.local",
                "account_id": "ACC-1002"
            }
        ],
        "events": [
            {
                "id": "msg_001",
                "type": "message",
                "body": "Hello David, please send over the Q3 financial audit report.",
                "timestamp": "2026-07-15T09:30:00Z",
                "participant": "p1@ediscovery.local",
                "reactions": [{"value": "👍", "count": 1}]
            },
            {
                "id": "msg_002",
                "type": "message",
                "body": "Sure Sarah! Attached is the Q3 summary report pdf.",
                "timestamp": "2026-07-15T09:34:12Z",
                "participant": "p2@ediscovery.local",
                "attachments": ["att_001"]
            }
        ],
        "attachments": [
            {
                "id": "att_001",
                "display_name": "Q3_Summary_Report.pdf",
                "size": 15420,
                "mime_type": "application/pdf"
            }
        ]
    }

    os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
    with zipfile.ZipFile(output_zip_path, 'w') as zf:
        # Write manifest.json
        zf.writestr("manifest.json", json.dumps(manifest_data, indent=2))
        # Write dummy attachment
        zf.writestr("Q3_Summary_Report.pdf", b"%PDF-1.4 Mock PDF Content for Testing RSMF Inspector Application")

    print(f"Sample RSMF created at: {output_zip_path}")

def run_tests():
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    sample_file = os.path.join(sample_dir, "sample_thread.rsmf")
    create_sample_rsmf(sample_file)

    # 1. Test Parsing
    print("\n--- Testing RSMF Parser ---")
    payload = RSMFParserService.parse_rsmf_file(sample_file)
    print(f"File Name: {payload.file_name}")
    print(f"Participants Count: {payload.participant_count}")
    print(f"Event Count: {payload.event_count}")
    print(f"Attachment Count: {payload.attachment_count}")
    print(f"Date Range: {payload.date_range_str}")
    
    assert payload.participant_count == 2, "Expected 2 participants"
    assert payload.event_count == 2, "Expected 2 events"
    assert payload.attachment_count == 1, "Expected 1 attachment"

    # 2. Test HTML Chat Generation
    print("\n--- Testing HTML Chat Generator ---")
    html_str = RSMFParserService.generate_html_chat(payload)
    assert "Sarah Jenkins" in html_str
    assert "Q3 financial audit report" in html_str
    print("HTML Chat Generation: SUCCESS!")

    # 3. Test Temp Attachment Extraction
    print("\n--- Testing Temp Attachment Extraction ---")
    ext_path = RSMFParserService.extract_attachment_to_temp(sample_file, payload.attachments[0].archive_path)
    print(f"Extracted file path: {ext_path}")
    assert os.path.exists(ext_path), "Extracted attachment should exist"
    with open(ext_path, 'rb') as f:
        data = f.read()
        assert b"Mock PDF Content" in data
    print("Attachment Extraction: SUCCESS!")

    # 4. Test Validator Bridge
    print("\n--- Testing Validator Bridge ---")
    bridge = ValidatorBridge()
    avail, msg = bridge.is_validator_available()
    print(f"Validator Availability: {avail} ({msg})")
    val_res = bridge.validate_rsmf(sample_file)
    print(f"Validator Result Message: {val_res['message']}")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
