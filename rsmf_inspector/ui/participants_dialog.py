from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from rsmf_inspector.models.rsmf_payload import Participant

class ParticipantsDialog(QDialog):
    def __init__(self, participants: List[Participant], parent=None):
        super().__init__(parent)
        self.setWindowTitle("👥 Participants List")
        self.resize(520, 600)
        
        # Sort participants in alphabetical order by display name (or id)
        self.participants = sorted(
            participants, 
            key=lambda p: (p.display or p.id or "").strip().lower()
        )

        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QLabel {
                color: #f8fafc;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title & Count Banner
        header = QHBoxLayout()
        title_lbl = QLabel(f"👥 Participants ({len(self.participants)})")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # Search Filter Bar
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Search participants by name or email...")
        self.txt_filter.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)
        self.txt_filter.textChanged.connect(self._filter_list)
        layout.addWidget(self.txt_filter)

        # Scrollable List Widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-bottom: 1px solid #334155;
            }
            QListWidget::item:hover {
                background-color: #243347;
                color: #38bdf8;
            }
            QListWidget::item:selected {
                background-color: #1e3a8a;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.list_widget)

        self._populate_list(self.participants)

        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                font-weight: 600;
                padding: 6px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _populate_list(self, part_list: List[Participant]):
        self.list_widget.clear()
        if not part_list:
            item = QListWidgetItem("No participants match query.")
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return

        for p in part_list:
            display_name = p.display or p.id
            email_info = f" • {p.email}" if p.email else ""
            account_info = f" • Account ID: {p.account_id}" if p.account_id else ""
            id_badge = f" [ID: {p.id}]" if p.id and p.id != display_name else ""
            
            line_1 = f"👤 {display_name}{id_badge}"
            line_2 = f"{email_info}{account_info}".strip(" •")
            
            if line_2:
                full_text = f"{line_1}\n    {line_2}"
            else:
                full_text = line_1

            item = QListWidgetItem(full_text)
            self.list_widget.addItem(item)

    def _filter_list(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_list(self.participants)
            return

        filtered = [
            p for p in self.participants
            if query in (p.display or "").lower() 
            or query in (p.email or "").lower() 
            or query in (p.id or "").lower()
            or query in (p.account_id or "").lower()
        ]
        self._populate_list(filtered)
