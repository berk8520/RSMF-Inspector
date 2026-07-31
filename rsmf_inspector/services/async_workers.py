import os
from typing import List, Tuple, Optional
from PySide6.QtCore import QThread, Signal
from rsmf_inspector.models.rsmf_payload import RSMFPayload, AttachmentItem
from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService

# 50 MB Smart Size Threshold for Auto-Extraction
AUTO_EXTRACT_MAX_BYTES = 50 * 1024 * 1024

class RSMFParseWorker(QThread):
    """
    Background QThread worker for lazy streaming and parsing of RSMF manifests.
    Keeps the main GUI thread 100% responsive when opening large 1GB-2GB containers.
    """
    finished = Signal(object)  # Emits parsed RSMFPayload
    error = Signal(str)        # Emits error message

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            payload = RSMFParserService.parse_rsmf_file(self.file_path)
            self.finished.emit(payload)
        except Exception as ex:
            self.error.emit(str(ex))


class AutoExtractionWorker(QThread):
    """
    Autonomous background worker that loops through container attachments automatically.
    Applies 50 MB smart size threshold: files > 50 MB are skipped during initial load
    and left as clean placeholders until explicitly requested by the user.
    """
    item_started = Signal(str, str, int, int)       # (att_id, display_name, current_idx, total_count)
    item_skipped = Signal(str, str, int, str)       # (att_id, display_name, size, reason)
    item_finished = Signal(str, str, object, object) # (att_id, extracted_path, thumb_uri, orig_file_uri)
    all_finished = Signal(int, int, int)            # (total_extracted, total_skipped, total_failed)

    def __init__(self, zip_path: str, attachments: List[AttachmentItem], parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.attachments = attachments

    def run(self):
        total = len(self.attachments)
        success_count = 0
        skip_count = 0
        fail_count = 0

        for idx, att in enumerate(self.attachments, start=1):
            att_id = att.id
            disp_name = att.display_name
            arch_path = att.archive_path or disp_name or att_id
            
            # Smart 50MB Size Threshold Check
            if att.size > AUTO_EXTRACT_MAX_BYTES:
                skip_count += 1
                self.item_skipped.emit(att_id, disp_name, att.size, "Exceeds 50 MB limit")
                continue

            self.item_started.emit(att_id, disp_name, idx, total)

            try:
                extracted_path = RSMFParserService.extract_attachment_to_temp(self.zip_path, arch_path)
                thumb_uri, orig_file_uri = RSMFParserService._generate_media_thumbnail(self.zip_path, arch_path)
                
                success_count += 1
                self.item_finished.emit(att_id, extracted_path, thumb_uri, orig_file_uri)
            except Exception:
                fail_count += 1

        self.all_finished.emit(success_count, skip_count, fail_count)


class ExportWorker(QThread):
    """
    Background QThread worker for executing single RSMF asset-stripping & export operation.
    Emits real-time progress callbacks for QProgressDialog updates.
    """
    progress = Signal(int, int, str)               # (current_idx, total_count, filename)
    finished = Signal(str, str, int, str)         # (root_export_dir, stripped_rsmf, att_count, csv_path)
    failed = Signal(str)                           # (error_message)

    def __init__(self, source_rsmf_path: str, output_dir: str, append_csv: bool = False, parent=None):
        super().__init__(parent)
        self.source_rsmf_path = source_rsmf_path
        self.output_dir = output_dir
        self.append_csv = append_csv

    def run(self):
        def _cb(curr, tot, fname):
            self.progress.emit(curr, tot, fname)

        try:
            root_exp, stripped_rsmf, att_count, att_records = RSMFExportService.export_stripped_rsmf(
                self.source_rsmf_path,
                self.output_dir,
                progress_callback=_cb
            )
            csv_path = os.path.join(self.output_dir, "attachment_load_file.csv")
            RSMFExportService.write_attachment_load_file(
                csv_path,
                att_records,
                append_mode=self.append_csv
            )
            self.finished.emit(root_exp, stripped_rsmf, att_count, csv_path)
        except Exception as ex:
            self.failed.emit(str(ex))


class BatchExportWorker(QThread):
    """
    Background QThread worker for executing batch RSMF asset-stripping & export operations.
    Emits real-time progress callbacks across multiple RSMF files for QProgressDialog updates.
    """
    progress = Signal(int, int, str)        # (file_idx, total_files, status_msg)
    file_finished = Signal(str, int)        # (rsmf_name, att_count)
    finished = Signal(int, int, str)        # (total_files_processed, total_att_count, csv_path)
    failed = Signal(str)                    # (error_message)

    def __init__(self, source_rsmf_paths: List[str], output_dir: str, append_csv: bool = False, parent=None):
        super().__init__(parent)
        self.source_rsmf_paths = source_rsmf_paths
        self.output_dir = output_dir
        self.append_csv = append_csv

    def run(self):
        total_files = len(self.source_rsmf_paths)
        total_att_count = 0
        all_att_records = []
        csv_path = os.path.join(self.output_dir, "attachment_load_file.csv")

        try:
            for idx, rsmf_path in enumerate(self.source_rsmf_paths, start=1):
                fname = os.path.basename(rsmf_path)
                self.progress.emit(idx, total_files, f"Processing {idx}/{total_files}: {fname}")

                def _cb(curr, tot, entry_name):
                    self.progress.emit(idx, total_files, f"File {idx}/{total_files} ({fname}): Unpacking {entry_name}")

                root_exp, stripped_rsmf, att_count, att_records = RSMFExportService.export_stripped_rsmf(
                    rsmf_path,
                    self.output_dir,
                    progress_callback=_cb
                )
                total_att_count += att_count
                all_att_records.extend(att_records)
                self.file_finished.emit(fname, att_count)

            # Write combined CSV load file for all processed RSMF containers
            RSMFExportService.write_attachment_load_file(
                csv_path,
                all_att_records,
                append_mode=self.append_csv
            )
            self.finished.emit(total_files, total_att_count, csv_path)
        except Exception as ex:
            self.failed.emit(str(ex))



class ThumbnailWorker(QThread):
    """
    Background QThread worker for extracting and decoding image/HEIC/video thumbnails.
    """
    thumbnail_ready = Signal(str, str, str)  # (att_id, thumb_uri, orig_file_uri)

    def __init__(self, zip_path: str, media_attachments: List[Tuple[str, str]], parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.media_attachments = media_attachments

    def run(self):
        for att_id, arch_path in self.media_attachments:
            try:
                thumb_uri, orig_uri = RSMFParserService._generate_media_thumbnail(self.zip_path, arch_path or att_id)
                if thumb_uri and orig_uri:
                    self.thumbnail_ready.emit(att_id, thumb_uri, orig_uri)
            except Exception:
                continue


class AttachmentExtractWorker(QThread):
    """
    Background QThread worker for offloading single attachment file extraction.
    """
    started = Signal(str)                  # att_id
    finished = Signal(str, str)            # (att_id, extracted_path)
    failed = Signal(str, str)              # (att_id, error_message)

    def __init__(self, zip_path: str, archive_internal_path: str, att_id: str, parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.archive_internal_path = archive_internal_path
        self.att_id = att_id

    def run(self):
        self.started.emit(self.att_id)
        try:
            extracted_path = RSMFParserService.extract_attachment_to_temp(
                self.zip_path, 
                self.archive_internal_path
            )
            self.finished.emit(self.att_id, extracted_path)
        except Exception as ex:
            self.failed.emit(self.att_id, str(ex))
