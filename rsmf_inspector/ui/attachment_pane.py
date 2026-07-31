import os
import sys
import subprocess
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, 
    QMessageBox, QLineEdit, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt, Signal
from rsmf_inspector.models.rsmf_payload import RSMFPayload, AttachmentItem
from rsmf_inspector.services.rsmf_parser import RSMFParserService, AUTO_EXTRACT_MAX_BYTES

class AttachmentPane(QWidget):
    export_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_payload: RSMFPayload = None
        self.all_attachments = []
        self.extracted_files: Dict[str, str] = {}  # att_id -> extracted_file_path
        self.skipped_files: Dict[str, str] = {}    # att_id -> reason
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(8)

        # Header Group Box
        self.group_box = QGroupBox("📎 Container Attachments")
        self.group_box.setStyleSheet("""
            QGroupBox {
                color: #a78bfa;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)

        gb_layout = QVBoxLayout(self.group_box)
        gb_layout.setContentsMargins(8, 12, 8, 8)
        gb_layout.setSpacing(8)

        # Filter Input
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Filter attachments...")
        self.txt_filter.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #a78bfa;
            }
        """)
        self.txt_filter.textChanged.connect(self._filter_list)
        gb_layout.addWidget(self.txt_filter)

        # QListWidget for Attachments with Visual Status Indicators
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #1e293b;
            }
            QListWidget::item:hover {
                background-color: #1e293b;
                color: #a78bfa;
            }
            QListWidget::item:selected {
                background-color: #4c1d95;
                color: #ffffff;
                border-radius: 4px;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_attachment_double_clicked)
        gb_layout.addWidget(self.list_widget)

        # Status Label / Batch Progress Indicator
        self.lbl_status = QLabel("Double-click file to open in OS")
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 11px;")
        gb_layout.addWidget(self.lbl_status)

        layout.addWidget(self.group_box)

        # Full-width Separate Attachments Button
        self.btn_export = QPushButton("🛠️ Separate RSMF Attachments...")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #475569;
                color: #f8fafc;
                font-weight: 600;
                font-size: 12px;
                padding: 10px 12px;
                border-radius: 6px;
                border: 1px solid #64748b;
            }
            QPushButton:hover {
                background-color: #64748b;
                color: #38bdf8;
                border: 1px solid #38bdf8;
            }
            QPushButton:pressed {
                background-color: #334155;
            }
        """)
        self.btn_export.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.btn_export)

        self.set_placeholder()

    def set_placeholder(self):
        self.current_payload = None
        self.all_attachments = []
        self.extracted_files.clear()
        self.skipped_files.clear()
        self.list_widget.clear()
        self.lbl_status.setText("No container loaded")
        item = QListWidgetItem("No container selected.")
        item.setFlags(Qt.NoItemFlags)
        self.list_widget.addItem(item)

    def load_payload(self, payload: RSMFPayload):
        self.extracted_files.clear()
        self.skipped_files.clear()
        self.current_payload = payload
        self.all_attachments = payload.attachments if payload else []
        self._populate_list(self.all_attachments)

        if not payload or not payload.attachments:
            self.lbl_status.setText("0 attachments found")
        else:
            count = len(payload.attachments)
            self.lbl_status.setText(f"⚡ Instant manifest load complete. Starting background extraction...")

    def update_item_status(self, att_id: str, status_text: str):
        """Updates per-item visual badge."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            att: AttachmentItem = item.data(Qt.UserRole)
            if att and att.id == att_id:
                size_str = self._format_size(att.size)
                item.setText(f"📄 {att.display_name}\n    [{size_str}] — {status_text}")
                break

    def mark_item_extracted(self, att_id: str, extracted_path: str):
        self.extracted_files[att_id] = extracted_path
        self.update_item_status(att_id, "✅ Ready 📎")

    def mark_item_skipped(self, att_id: str, reason: str):
        self.skipped_files[att_id] = reason
        self.update_item_status(att_id, "📦 >50MB (Click to Extract)")

    def update_batch_progress(self, current_idx: int, total_count: int, att_display: str):
        self.lbl_status.setText(f"⏳ Extracting {current_idx}/{total_count}: {att_display}")

    def mark_all_extracted(self, total_extracted: int, total_skipped: int, total_failed: int):
        if total_skipped > 0:
            self.lbl_status.setText(f"✅ {total_extracted} extracted ({total_skipped} skipped >50MB)")
        elif total_failed == 0:
            self.lbl_status.setText(f"✅ All {total_extracted} attachments extracted & cached")
        else:
            self.lbl_status.setText(f"✅ {total_extracted} extracted ({total_failed} failed)")

    def _populate_list(self, att_list):
        self.list_widget.clear()
        if not att_list:
            if self.current_payload:
                item = QListWidgetItem("No internal attachments.")
                item.setFlags(Qt.NoItemFlags)
                self.list_widget.addItem(item)
            return

        for att in att_list:
            size_str = self._format_size(att.size)
            if att.id in self.extracted_files:
                status_icon = "✅ Ready 📎"
            elif att.size > AUTO_EXTRACT_MAX_BYTES:
                status_icon = "📦 >50MB (Click to Extract)"
            else:
                status_icon = "⏳ Pending extraction..."

            display_text = f"📄 {att.display_name}\n    [{size_str}] — {status_icon}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, att)
            self.list_widget.addItem(item)

    def _filter_list(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_list(self.all_attachments)
            return

        filtered = [
            att for att in self.all_attachments
            if query in att.display_name.lower() or query in att.archive_path.lower()
        ]
        self._populate_list(filtered)

    def _on_attachment_double_clicked(self, item: QListWidgetItem):
        att: AttachmentItem = item.data(Qt.UserRole)
        if not att or not self.current_payload:
            return

        if att.id in self.extracted_files and os.path.exists(self.extracted_files[att.id]):
            try:
                self.open_file_with_default_app(self.extracted_files[att.id])
            except Exception as ex:
                QMessageBox.critical(self, "Launch Error", f"Failed to launch file:\n{str(ex)}")
        else:
            # On-demand extraction for >50MB or unextracted attachments
            try:
                self.lbl_status.setText(f"⏳ On-demand extracting '{att.display_name}'...")
                extracted_path = RSMFParserService.extract_attachment_to_temp(
                    self.current_payload.file_path,
                    att.archive_path or att.display_name
                )
                self.mark_item_extracted(att.id, extracted_path)
                self.open_file_with_default_app(extracted_path)
            except Exception as ex:
                QMessageBox.critical(self, "Extraction Error", f"Failed to extract attachment:\n{str(ex)}")

    @staticmethod
    def open_file_with_default_app(file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Extracted file missing: {file_path}")

        if sys.platform.startswith('win'):
            os.startfile(file_path)
        elif sys.platform.startswith('darwin'):
            subprocess.run(['open', file_path], check=True)
        else:
            subprocess.run(['xdg-open', file_path], check=True)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes <= 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
