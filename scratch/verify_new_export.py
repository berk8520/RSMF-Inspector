import os
import zipfile
import tempfile
import csv
import shutil
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

def test_new_export_structure():
    # Use existing sample zip/eml if available or test directory
    temp_dir = tempfile.mkdtemp()
    target_out_dir = os.path.join(temp_dir, "export_output")
    
    # Create a mock zip rsmf file
    mock_rsmf_path = os.path.join(temp_dir, "sample_test.rsmf")
    with zipfile.ZipFile(mock_rsmf_path, "w") as zf:
        zf.writestr("rsmf_manifest.json", '{"attachments": [{"id": "att_101", "display_name": "doc.pdf"}]}')
        zf.writestr("att_101", b"Dummy attachment bytes 123456789")

    # Run export
    root_exp, stripped_rsmf, att_count, att_records = RSMFExportService.export_stripped_rsmf(
        mock_rsmf_path,
        target_out_dir
    )

    csv_path = os.path.join(target_out_dir, "attachment_load_file.csv")
    RSMFExportService.write_attachment_load_file(csv_path, att_records)

    # 1. Verify directory structure
    assert os.path.exists(os.path.join(target_out_dir, "Attachments")), "Attachments folder missing"
    assert os.path.exists(os.path.join(target_out_dir, "RSMF")), "RSMF folder missing"
    assert os.path.exists(os.path.join(target_out_dir, "JSON")), "JSON folder missing"
    assert os.path.exists(csv_path), "Load file CSV missing at root"

    # 2. Verify attachment record relative path
    assert len(att_records) == 1
    att_id, rel_path = att_records[0]
    assert rel_path == "Attachments/att_101.pdf", f"Unexpected relative path: {rel_path}"

    # 3. Verify stripped zip contains 0-byte attachment
    with zipfile.ZipFile(stripped_rsmf, "r") as zf_stripped:
        info = zf_stripped.getinfo("att_101")
        assert info.file_size == 0, f"Expected 0-byte file in zip payload, got {info.file_size}"
        manifest_data = zf_stripped.read("rsmf_manifest.json")
        assert len(manifest_data) > 0, "Manifest json in zip payload missing"

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_new_export_structure()
