import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QLabel,
    QStatusBar, QMessageBox, QFileDialog, QProgressDialog
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QCloseEvent, QPixmap


from rsmf_inspector.ui.file_list_pane import FileListPane
from rsmf_inspector.ui.attachment_pane import AttachmentPane
from rsmf_inspector.ui.metric_cards import TopMetricCardsPane
from rsmf_inspector.ui.tabbed_viewer import TabbedViewerPane
from rsmf_inspector.ui.participants_dialog import ParticipantsDialog
from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.services.rsmf_export_service import RSMFExportService
from rsmf_inspector.services.temp_cache_service import TempCacheService
from rsmf_inspector.services.async_workers import RSMFParseWorker, AutoExtractionWorker, ExportWorker, BatchExportWorker

class RSMFInspectorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RSMF Inspector - Relativity Short Message Format Analyzer")
        self.resize(1420, 880)
        
        self.current_payload = None
        self.parse_worker: RSMFParseWorker = None
        self.auto_extract_worker: AutoExtractionWorker = None
        self.export_worker = None  # ExportWorker or BatchExportWorker
        self.progress_dialog: QProgressDialog = None

        # Clean cache on launch
        TempCacheService.clear_cache()

        self._apply_global_theme()
        self._init_ui()

    def closeEvent(self, event: QCloseEvent):
        """Automatically purges all temporary extracted files and thumbnails upon exit."""
        if self.auto_extract_worker and self.auto_extract_worker.isRunning():
            self.auto_extract_worker.terminate()
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.terminate()
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.terminate()

        TempCacheService.clear_cache()
        event.accept()

    def _apply_global_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0f17;
            }
            QSplitter::handle {
                background-color: #1e293b;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #38bdf8;
            }
            QStatusBar {
                background-color: #0f172a;
                color: #94a3b8;
                border-top: 1px solid #1e293b;
                font-size: 11px;
            }
            QProgressDialog {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #334155;
            }
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                color: #f8fafc;
            }
            QProgressBar::chunk {
                background-color: #0284c7;
                border-radius: 4px;
            }
        """)

    def _init_ui(self):
        # Central Horizontal QSplitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        # Pane 1 (Far Left): File Containers List
        self.left_pane = FileListPane()
        self.left_pane.file_selected.connect(self._on_file_selected)
        self.splitter.addWidget(self.left_pane)

        # Pane 2 (Center): Workspace
        self.center_container = QWidget()
        center_layout = QVBoxLayout(self.center_container)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(10)


        # Header Banner with Branding Logo
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(12)

        # Brand Logo Label
        self.logo_label = QLabel()
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
        logo_path = os.path.join(assets_dir, "pageone-logo-white.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(assets_dir, "pageone-logo.png")

        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToHeight(28, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            header_layout.addWidget(self.logo_label)

        # App Title & Subtitle in Header
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("RSMF Inspector")
        app_title.setStyleSheet("color: #f8fafc; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        app_sub = QLabel("Relativity Short Message Format Analyzer & Extractor")
        app_sub.setStyleSheet("color: #64748b; font-size: 11px; border: none; background: transparent;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)
        header_layout.addLayout(title_box)

        header_layout.addStretch()
        center_layout.addWidget(header_widget)

        self.metric_cards_pane = TopMetricCardsPane()
        self.metric_cards_pane.participants_clicked.connect(self.open_participants_dialog)
        center_layout.addWidget(self.metric_cards_pane)


        self.tabbed_viewer = TabbedViewerPane()
        center_layout.addWidget(self.tabbed_viewer)

        self.splitter.addWidget(self.center_container)

        # Pane 3 (Far Right): Attachments Pane
        self.attachment_pane = AttachmentPane()
        self.attachment_pane.export_requested.connect(self.export_stripped_rsmf)
        self.splitter.addWidget(self.attachment_pane)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 6)
        self.splitter.setStretchFactor(2, 2)
        self.splitter.setSizes([240, 850, 260])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load a directory to inspect RSMF containers.")

    def _on_file_selected(self, display_name: str, file_path: str):
        """Phase 1: Instant manifest streaming & background worker launch."""
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "File Not Found", f"File path does not exist:\n{file_path}")
            return

        # 1. Purge previous container's temp cache
        if self.auto_extract_worker and self.auto_extract_worker.isRunning():
            self.auto_extract_worker.terminate()
        if self.parse_worker and self.parse_worker.isRunning():
            self.parse_worker.terminate()

        TempCacheService.clear_cache()

        self.status_bar.showMessage(f"⚡ Instant streaming metadata for '{display_name}' (Background QThread)...")

        # Spawn RSMFParseWorker QThread
        self.parse_worker = RSMFParseWorker(file_path, parent=self)
        self.parse_worker.finished.connect(self._on_payload_parsed)
        self.parse_worker.error.connect(self._on_parse_error)
        self.parse_worker.start()

    def _on_payload_parsed(self, payload):
        """Phase 1 Complete -> Trigger Phase 2: Autonomous Background Extraction."""
        self.current_payload = payload

        # 1. Update UI components instantly with placeholders
        self.metric_cards_pane.update_metrics(payload)
        self.tabbed_viewer.load_payload(payload)
        self.attachment_pane.load_payload(payload)

        file_size_mb = os.path.getsize(payload.file_path) / (1024 * 1024)
        self.status_bar.showMessage(
            f"⚡ Manifest loaded ({file_size_mb:.2f} MB) | "
            f"Starting background extraction of {payload.attachment_count} attachments..."
        )

        # 2. Trigger Phase 2: Launch Autonomous Background Extraction Worker
        if payload.attachments:
            self.auto_extract_worker = AutoExtractionWorker(
                zip_path=payload.file_path,
                attachments=payload.attachments,
                parent=self
            )
            self.auto_extract_worker.item_started.connect(self._on_auto_item_started)
            self.auto_extract_worker.item_skipped.connect(self._on_auto_item_skipped)
            self.auto_extract_worker.item_finished.connect(self._on_auto_item_finished)
            self.auto_extract_worker.all_finished.connect(self._on_auto_all_finished)
            self.auto_extract_worker.start()
        else:
            self.status_bar.showMessage(f"Loaded '{payload.file_name}' | No internal attachments.")

    def _on_auto_item_started(self, att_id: str, display_name: str, current_idx: int, total_count: int):
        """Phase 2: Updates live visual progress indicators as worker extracts each file."""
        self.attachment_pane.update_item_status(att_id, "⏳ Extracting...")
        self.attachment_pane.update_batch_progress(current_idx, total_count, display_name)
        self.status_bar.showMessage(
            f"⏳ Background extraction in progress ({current_idx}/{total_count}): Unpacking '{display_name}'..."
        )

    def _on_auto_item_skipped(self, att_id: str, display_name: str, size_bytes: int, reason: str):
        """Phase 2: Updates item status badge when a >50MB attachment skips auto-extraction."""
        self.attachment_pane.mark_item_skipped(att_id, reason)

    def _on_auto_item_finished(self, att_id: str, extracted_path: str, thumb_uri: str, orig_file_uri: str):
        """Phase 3: Autonomous Re-Render when item finishes extracting."""
        self.attachment_pane.mark_item_extracted(att_id, extracted_path)
        self._re_render_chat_view()

    def _on_auto_all_finished(self, total_extracted: int, total_skipped: int, total_failed: int):
        """Phase 3 Complete: Re-render final Chat View & update status bar."""
        self.attachment_pane.mark_all_extracted(total_extracted, total_skipped, total_failed)
        self._re_render_chat_view()
        
        if self.current_payload:
            if total_skipped > 0:
                self.status_bar.showMessage(
                    f"✅ Ready | '{self.current_payload.file_name}' — {total_extracted} extracted ({total_skipped} skipped >50MB limit)"
                )
            else:
                self.status_bar.showMessage(
                    f"✅ Ready | '{self.current_payload.file_name}' — All {total_extracted} attachments extracted & cached"
                )

    def _re_render_chat_view(self):
        """Performs targeted re-render of RSMF Chat View while preserving scroll position."""
        if not self.current_payload:
            return

        browser = self.tabbed_viewer.chat_tab.browser
        v_bar = browser.verticalScrollBar()
        scroll_pos = v_bar.value()

        updated_html = RSMFParserService.generate_html_chat(self.current_payload)
        browser.setHtml(updated_html)

        v_bar.setValue(scroll_pos)

    def _on_parse_error(self, error_msg: str):
        self.status_bar.showMessage(f"Parsing Error: {error_msg}")
        QMessageBox.critical(self, "RSMF Parsing Error", f"Failed to parse RSMF container:\n{error_msg}")

    def open_participants_dialog(self):
        """Opens a scrollable dialog displaying the list of participants in alphabetical order."""
        if not self.current_payload or not self.current_payload.participants:
            QMessageBox.information(self, "Participants", "No participants found in the currently loaded container.")
            return

        dialog = ParticipantsDialog(self.current_payload.participants, parent=self)
        dialog.exec()

    def export_stripped_rsmf(self):
        """Exports stripped RSMF container(s), companion attachments folders, manifest JSON, and attachment load file (CSV)."""
        loaded_files = self.left_pane.get_all_loaded_files()
        if not loaded_files:
            QMessageBox.information(self, "Separate RSMF Attachments", "No RSMF containers are currently loaded in the directory list.")
            return

        # Prompt single vs batch if multiple RSMF containers loaded
        is_batch = False
        target_rsmf_paths = []

        if len(loaded_files) > 1:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Separate RSMF Attachments Scope")
            msg_box.setText(f"You have {len(loaded_files)} RSMF containers loaded.")
            msg_box.setInformativeText("Would you like to separate attachments for the currently selected file or all loaded files?")
            
            btn_current = msg_box.addButton("Current File Only", QMessageBox.ActionRole)
            btn_all = msg_box.addButton(f"All Loaded Files ({len(loaded_files)})", QMessageBox.ActionRole)
            btn_cancel = msg_box.addButton(QMessageBox.Cancel)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()

            if clicked == btn_cancel or clicked is None:
                return
            elif clicked == btn_all:
                is_batch = True
                target_rsmf_paths = list(loaded_files.values())
            else:
                if not self.current_payload:
                    QMessageBox.information(self, "Separate RSMF Attachments", "Please select a specific RSMF container first.")
                    return
                target_rsmf_paths = [self.current_payload.file_path]
        else:
            if not self.current_payload:
                target_rsmf_paths = list(loaded_files.values())
            else:
                target_rsmf_paths = [self.current_payload.file_path]

        # Check for duplicate base file names across loaded RSMF files that would target the same export directory
        stem_counts = {}
        for rsmf_path in target_rsmf_paths:
            base_stem = os.path.splitext(os.path.basename(rsmf_path))[0]
            stem_counts.setdefault(base_stem, []).append(rsmf_path)

        duplicate_stems = {stem: paths for stem, paths in stem_counts.items() if len(paths) > 1}

        if duplicate_stems:
            dup_file_msg = []
            for stem, paths in duplicate_stems.items():
                dup_file_msg.append(f"• Container Name: '{stem}' ({len(paths)} files):")
                for p in paths[:3]:
                    dup_file_msg.append(f"   - {p}")
                if len(paths) > 3:
                    dup_file_msg.append(f"   - ... and {len(paths) - 3} more")

            msg_str = "\n".join(dup_file_msg)

            dup_batch_box = QMessageBox(self)
            dup_batch_box.setIcon(QMessageBox.Warning)
            dup_batch_box.setWindowTitle("⚠️ Duplicate Container File Names Loaded")
            dup_batch_box.setText("The loaded batch contains RSMF files with identical file names in different subfolders:")
            dup_batch_box.setInformativeText(
                f"{msg_str}\n\n"
                "Because exports are saved into folders named '<Filename>_Export', these files will target the same export folder and overwrite each other.\n\n"
                "Do you want to proceed anyway?"
            )
            btn_proceed_dup_name = dup_batch_box.addButton("Proceed & Overwrite", QMessageBox.AcceptRole)
            btn_cancel_dup_name = dup_batch_box.addButton(QMessageBox.Cancel)
            
            dup_batch_box.exec()
            if dup_batch_box.clickedButton() != btn_proceed_dup_name:
                return

        target_dir = QFileDialog.getExistingDirectory(self, "Select Export Destination Directory")
        if not target_dir:
            return


        # Check for duplicate output export folders before processing
        existing_export_dirs = []
        for rsmf_path in target_rsmf_paths:
            base_stem = os.path.splitext(os.path.basename(rsmf_path))[0]
            export_folder_path = os.path.join(target_dir, f"{base_stem}_Export")
            if os.path.exists(export_folder_path):
                existing_export_dirs.append(f"{base_stem}_Export")

        if existing_export_dirs:
            dup_box = QMessageBox(self)
            dup_box.setIcon(QMessageBox.Warning)
            dup_box.setWindowTitle("⚠️ Duplicate Export Folders Detected")
            dup_box.setText(f"Found {len(existing_export_dirs)} existing export folder(s) in destination:")
            dir_list_str = "\n".join([f" • {d}" for d in existing_export_dirs[:5]])
            if len(existing_export_dirs) > 5:
                dir_list_str += f"\n ... and {len(existing_export_dirs) - 5} more"
            
            dup_box.setInformativeText(f"{dir_list_str}\n\nExisting files inside these folders will be overwritten. Do you want to proceed?")
            btn_proceed = dup_box.addButton("Overwrite & Proceed", QMessageBox.AcceptRole)
            btn_cancel_dup = dup_box.addButton(QMessageBox.Cancel)
            
            dup_box.exec()
            if dup_box.clickedButton() != btn_proceed:
                return

        # Check for existing attachment_load_file.csv in target directory
        csv_path = os.path.join(target_dir, "attachment_load_file.csv")

        append_csv = False
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
            csv_box = QMessageBox(self)
            csv_box.setIcon(QMessageBox.Question)
            csv_box.setWindowTitle("Attachment Load File Detected")
            csv_box.setText("An existing 'attachment_load_file.csv' was found in the target directory.")
            csv_box.setInformativeText("Do you want to append new records to the existing load file, or overwrite it?")
            
            btn_append = csv_box.addButton("Append Records", QMessageBox.AcceptRole)
            btn_overwrite = csv_box.addButton("Overwrite Load File", QMessageBox.DestructiveRole)
            btn_cancel = csv_box.addButton(QMessageBox.Cancel)
            
            csv_box.exec()
            clicked_csv = csv_box.clickedButton()

            if clicked_csv == btn_cancel or clicked_csv is None:
                return
            elif clicked_csv == btn_append:
                append_csv = True
            else:
                append_csv = False

        # Non-Blocking QProgressDialog
        self.progress_dialog = QProgressDialog(
            "Separating attachments and exporting files...",
            "Cancel",
            0,
            100,
            self
        )
        self.progress_dialog.setWindowTitle("🛠️ Separating RSMF Attachments...")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)

        if is_batch or len(target_rsmf_paths) > 1:
            self.export_worker = BatchExportWorker(target_rsmf_paths, target_dir, append_csv=append_csv, parent=self)
            self.export_worker.progress.connect(self._on_batch_export_progress)
            self.export_worker.finished.connect(self._on_batch_export_finished)
            self.export_worker.failed.connect(self._on_export_failed)
        else:
            self.export_worker = ExportWorker(target_rsmf_paths[0], target_dir, append_csv=append_csv, parent=self)
            self.export_worker.progress.connect(self._on_export_progress)
            self.export_worker.finished.connect(self._on_single_export_finished)
            self.export_worker.failed.connect(self._on_export_failed)

        self.progress_dialog.canceled.connect(self._on_export_canceled)
        self.export_worker.start()

    def _on_export_progress(self, current_idx: int, total_count: int, filename: str):
        """Updates QProgressDialog progress bar percentage and label text for single export."""
        if self.progress_dialog and not self.progress_dialog.wasCanceled():
            self.progress_dialog.setMaximum(total_count)
            self.progress_dialog.setValue(current_idx)
            self.progress_dialog.setLabelText(f"Extracting file {current_idx} of {total_count}:\n{filename}")

    def _on_batch_export_progress(self, file_idx: int, total_files: int, status_msg: str):
        """Updates QProgressDialog progress bar percentage and label text for batch export."""
        if self.progress_dialog and not self.progress_dialog.wasCanceled():
            self.progress_dialog.setMaximum(total_files)
            self.progress_dialog.setValue(file_idx)
            self.progress_dialog.setLabelText(status_msg)

    def _on_single_export_finished(self, root_export: str, stripped_rsmf: str, att_count: int, csv_path: str):
        """Closes progress dialog and displays success alert for single file export."""
        if self.progress_dialog:
            self.progress_dialog.close()

        self.status_bar.showMessage(f"Export completed: {os.path.basename(root_export)}")

        msg = (
            f"<b>✅ Separate RSMF Attachments Completed Successfully!</b><br><br>"
            f"<b>Target Export Directory:</b><br><code>{root_export}</code><br><br>"
            f"<b>Modified RSMF (RSMF/):</b><br><code>{os.path.basename(stripped_rsmf)}</code><br><br>"
            f"<b>Manifest JSON (JSON/):</b><br><code>{os.path.basename(stripped_rsmf).replace('_stripped.rsmf', '_rsmf_manifest.json').replace('_stripped.zip', '_rsmf_manifest.json')}</code><br><br>"
            f"<b>Attachments Directory (Attachments/):</b><br><code>{att_count} original files renamed by Attachment ID</code><br><br>"
            f"<b>Attachment Load File (CSV):</b><br><code>{os.path.basename(csv_path)}</code>"
        )
        
        QMessageBox.information(self, "Separate RSMF Attachments Successful", msg)

    def _on_batch_export_finished(self, total_files: int, total_att_count: int, csv_path: str):
        """Closes progress dialog and displays success alert for batch export."""
        if self.progress_dialog:
            self.progress_dialog.close()

        self.status_bar.showMessage(f"Batch Export completed: {total_files} containers processed")

        msg = (
            f"<b>✅ Batch Separate RSMF Attachments Completed Successfully!</b><br><br>"
            f"<b>Processed RSMF Containers:</b> {total_files}<br>"
            f"<b>Total Attachments Extracted:</b> {total_att_count}<br><br>"
            f"<b>Attachment Load File (CSV):</b><br><code>{csv_path}</code>"
        )
        
        QMessageBox.information(self, "Batch Separate RSMF Attachments Successful", msg)

    def _on_export_failed(self, error_msg: str):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.status_bar.showMessage(f"Export Error: {error_msg}")
        QMessageBox.critical(self, "Export Error", f"Failed to separate RSMF attachments:\n{error_msg}")

    def _on_export_canceled(self):
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.terminate()
        self.status_bar.showMessage("Export operation canceled by user.")

