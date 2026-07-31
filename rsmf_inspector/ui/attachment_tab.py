import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, 
    QMessageBox, QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt
from rsmf_inspector.models.rsmf_payload import RSMFPayload, AttachmentItem
from rsmf_inspector.services.rsmf_parser import RSMFParserService

class AttachmentTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_payload: RSMFPayload = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header Info Bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 4, 4, 4)
        
        self.lbl_info = QLabel("📎 Internal Archive Attachments")
        self.lbl_info.setStyleSheet("color: #a78bfa; font-weight: 600; font-size: 12px;")
        header_layout.addWidget(self.lbl_info)
        
        header_layout.addStretch()
        
        self.lbl_tip = QLabel("💡 Double-click any file to extract and open with OS default application")
        self.lbl_tip.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        header_layout.addWidget(self.lbl_tip)
        
        layout.addLayout(header_layout)
        
        # QListWidget for Attachments
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 10px 14px;
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
        layout.addWidget(self.list_widget)
        
        self.set_placeholder()

    def set_placeholder(self):
        self.current_payload = None
        self.list_widget.clear()
        self.lbl_info.setText("📎 Internal Archive Attachments")
        item = QListWidgetItem("No RSMF container currently loaded.")
        item.setFlags(Qt.NoItemFlags)
        self.list_widget.addItem(item)

    def load_payload(self, payload: RSMFPayload):
        self.current_payload = payload
        self.list_widget.clear()
        
        if not payload or not payload.attachments:
            self.lbl_info.setText("📎 Internal Archive Attachments (0 files)")
            item = QListWidgetItem("No internal attachments found in this container.")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return

        self.lbl_info.setText(f"📎 Internal Archive Attachments ({payload.attachment_count} files)")

        for att in payload.attachments:
            size_str = self._format_size(att.size)
            display_text = f"📄 {att.display_name}  —  [{size_str}]"
            if att.mime_type:
                display_text += f"  ({att.mime_type})"
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, att)
            self.list_widget.addItem(item)

    def _on_attachment_double_clicked(self, item: QListWidgetItem):
        att: AttachmentItem = item.data(Qt.UserRole)
        if not att or not self.current_payload:
            return

        try:
            # Stream file to secure temp directory
            extracted_path = RSMFParserService.extract_attachment_to_temp(
                self.current_payload.file_path, 
                att.archive_path or att.display_name
            )
            
            # Launch via OS default handler
            self.open_file_with_default_app(extracted_path)
            
        except Exception as ex:
            QMessageBox.critical(
                self, 
                "Attachment Extraction Error", 
                f"Failed to extract and open attachment:\n{str(ex)}"
            )

    @staticmethod
    def open_file_with_default_app(file_path: str):
        """Cross-platform default OS file handler caller."""
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
