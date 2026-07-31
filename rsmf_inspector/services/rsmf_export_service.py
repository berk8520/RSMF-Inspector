import os
import zipfile
import shutil
import io
import email
import email.generator
import base64
import csv
from email.message import Message
from typing import Tuple, Optional, Callable, List


from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.temp_cache_service import TempCacheService

class RSMFExportService:
    """
    Service for asset-stripping RSMF containers, creating companion attachments directories,
    exporting companion manifest JSON files, and generating CSV attachment load files.
    Supports progress callbacks for non-blocking UI progress bars.
    """

    @staticmethod
    def write_attachment_load_file(
        csv_path: str,
        att_records: List[Tuple[str, str]],
        append_mode: bool = False
    ) -> None:
        """
        Writes or appends attachment load records to a CSV file.
        Header: AttachmentID, Relative Path
        """
        file_exists = os.path.exists(csv_path)
        mode = 'a' if append_mode else 'w'
        
        with open(csv_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            # Write header if creating new file or file was 0 bytes
            if not append_mode or not file_exists or os.path.getsize(csv_path) == 0:
                writer.writerow(["AttachmentID", "Relative Path"])
            
            for att_id, rel_path in att_records:
                writer.writerow([att_id, rel_path])


    @staticmethod
    def export_stripped_rsmf(
        source_rsmf_path: str, 
        output_dir: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[str, str, int, List[Tuple[str, str]]]:
        """
        Exports a modified RSMF container where all internal attachments are replaced with 0-byte files,
        saves original attachments into a companion attachments/ folder renamed by Attachment ID,
        and extracts raw manifest JSON to <RSMF_BaseName>_rsmf_manifest.json next to the stripped RSMF file.

        progress_callback(current_idx, total_count, filename)
        Returns: (root_export_dir, stripped_rsmf_file_path, extracted_attachment_count, att_records)
        att_records is a list of tuples: [(AttachmentID, RelativePath)]
        """
        if not os.path.exists(source_rsmf_path):
            raise FileNotFoundError(f"Source RSMF file not found: {source_rsmf_path}")

        source_basename = os.path.basename(source_rsmf_path)
        base_name_no_ext, ext = os.path.splitext(source_basename)

        # Root Export Directory (target directory passed as output_dir)
        root_export_dir = output_dir
        os.makedirs(root_export_dir, exist_ok=True)

        # Top-level directories: Attachments, RSMF, JSON
        att_dir = os.path.join(root_export_dir, "Attachments")
        rsmf_dir = os.path.join(root_export_dir, "RSMF")
        json_dir = os.path.join(root_export_dir, "JSON")
        os.makedirs(att_dir, exist_ok=True)
        os.makedirs(rsmf_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)

        # Parse source payload to map attachments by ID / display_name
        payload = RSMFParserService.parse_rsmf_file(source_rsmf_path)
        zf_source, eml_msg = RSMFParserService._open_zip_from_rsmf(source_rsmf_path)

        extracted_att_count = 0
        att_records = []  # [(AttachmentID, Relative Path)]

        try:
            zip_entries = zf_source.namelist()
            total_entries = len(zip_entries)

            # Map of internal zip entry name -> destination companion filename & att_id
            att_entry_map = {}
            used_companion_names = set()

            for att in payload.attachments:
                internal_path = att.archive_path or att.display_name or att.id
                matched = None
                if internal_path in zip_entries:
                    matched = internal_path
                else:
                    for entry in zip_entries:
                        if entry.endswith(internal_path) or os.path.basename(entry) == os.path.basename(internal_path):
                            matched = entry
                            break
                
                if matched:
                    # Rename companion file strictly by attachment_id or display_name
                    orig_ext = os.path.splitext(att.display_name)[1] or os.path.splitext(matched)[1]
                    clean_id = att.id.replace(" ", "_")
                    if not clean_id.lower().endswith(orig_ext.lower()):
                        target_att_name = f"{clean_id}{orig_ext}"
                    else:
                        target_att_name = clean_id
                    
                    # Deduplicate companion filenames if duplicate attachment IDs or names exist inside container
                    if target_att_name in used_companion_names:
                        base_stem, ext_part = os.path.splitext(target_att_name)
                        counter = 1
                        while f"{base_stem}_{counter}{ext_part}" in used_companion_names:
                            counter += 1
                        target_att_name = f"{base_stem}_{counter}{ext_part}"
                    
                    used_companion_names.add(target_att_name)
                    att_entry_map[matched] = (target_att_name, att.id)


            # Extract companion attachments
            for idx, entry in enumerate(zip_entries, start=1):
                if progress_callback:
                    progress_callback(idx, total_entries, os.path.basename(entry))

                if entry in att_entry_map:
                    target_filename, att_id = att_entry_map[entry]
                    dest_file_path = os.path.join(att_dir, target_filename)
                    try:
                        info = zf_source.getinfo(entry)
                        if info.file_size == 0:
                            # 0-byte attachment: Create empty companion file directly without reading compressed stream
                            with open(dest_file_path, "wb") as dst:
                                pass
                        else:
                            with zf_source.open(entry) as src, open(dest_file_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                        extracted_att_count += 1
                        
                        # Store relative path for load file CSV (relative to root export dir: Attachments/filename)
                        rel_path = f"Attachments/{target_filename}"
                        att_records.append((att_id, rel_path))
                    except Exception as ex:
                        # Fallback for corrupt compressed stream or 0-byte entries: write empty file
                        with open(dest_file_path, "wb") as dst:
                            pass
                        extracted_att_count += 1
                        rel_path = f"Attachments/{target_filename}"
                        att_records.append((att_id, rel_path))

            # Write manifest JSON to JSON/ directory
            if payload.raw_json_str:
                manifest_out_filename = f"{base_name_no_ext}_rsmf_manifest.json"
                manifest_out_path = os.path.join(json_dir, manifest_out_filename)
                with open(manifest_out_path, "w", encoding="utf-8") as f_manifest:
                    f_manifest.write(payload.raw_json_str)

            # 3. Create Stripped ZIP Payload (Preserves manifest JSON and replaces attachment files with 0-byte entries)
            stripped_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(stripped_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf_stripped:
                for entry in zip_entries:
                    if entry.lower().endswith('.json'):
                        try:
                            data = zf_source.read(entry)
                        except Exception:
                            data = b"{}"
                        zf_stripped.writestr(entry, data)
                    else:
                        # Replace attachment file with a 0-byte entry in the zip container
                        zf_stripped.writestr(entry, b"")

            stripped_zip_bytes = stripped_zip_buffer.getvalue()


            # 4. Construct Modified RSMF Output File in RSMF/ directory
            stripped_rsmf_filename = f"{base_name_no_ext}_stripped{ext}"
            stripped_rsmf_path = os.path.join(rsmf_dir, stripped_rsmf_filename)

            if eml_msg:
                # EML wrapper: Replace zip attachment payload with base64 encoded stripped_zip_bytes
                modified_eml = email.message_from_bytes(eml_msg.as_bytes())
                b64_raw = base64.b64encode(stripped_zip_bytes).decode('ascii')
                # Wrap base64 string to line length 76 per MIME RFC 2045 specification
                b64_stripped_str = "\n".join(b64_raw[i:i + 76] for i in range(0, len(b64_raw), 76))
                
                # Update payload bytes in EML part
                if modified_eml.is_multipart():
                    replaced = False
                    for part in modified_eml.walk():
                        p_bytes = part.get_payload(decode=True)
                        if p_bytes and zipfile.is_zipfile(io.BytesIO(p_bytes)):
                            part.set_payload(b64_stripped_str)
                            if 'Content-Transfer-Encoding' in part:
                                part.replace_header('Content-Transfer-Encoding', 'base64')
                            else:
                                part.add_header('Content-Transfer-Encoding', 'base64')
                            replaced = True
                            break
                    if not replaced:
                        modified_eml.set_payload(b64_stripped_str)
                else:
                    modified_eml.set_payload(b64_stripped_str)

                with open(stripped_rsmf_path, 'wb') as f_out:
                    f_out.write(modified_eml.as_bytes())
            else:
                # Direct ZIP file
                with open(stripped_rsmf_path, 'wb') as f_out:
                    f_out.write(stripped_zip_bytes)


        finally:
            zf_source.close()

        return root_export_dir, stripped_rsmf_path, extracted_att_count, att_records

