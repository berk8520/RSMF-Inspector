import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtGui import QFont, QTextOption, QTextDocument, QPalette, QColor, QTextCursor
from PySide6.QtCore import Qt
from rsmf_inspector.models.rsmf_payload import RSMFPayload
from rsmf_inspector.ui.json_highlighter import JSONHighlighter

class JSONViewTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header Info Bar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 4, 4, 4)
        
        self.lbl_info = QLabel("📄 Streamed manifest payload")
        self.lbl_info.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 12px;")
        header_layout.addWidget(self.lbl_info)
        
        header_layout.addStretch()
        
        self.btn_copy = QPushButton("📋 Copy JSON")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        header_layout.addWidget(self.btn_copy)
        
        layout.addLayout(header_layout)

        # Editor View
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setWordWrapMode(QTextOption.NoWrap)
        
        # Configure bright yellow search hit selection palette
        palette = self.text_edit.palette()
        palette.setColor(QPalette.Highlight, QColor("#ffff00"))      # Bright Yellow
        palette.setColor(QPalette.HighlightedText, QColor("#000000")) # Black Text
        self.text_edit.setPalette(palette)

        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.text_edit.setFont(font)
        
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #090d16;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #ffff00;
                selection-color: #000000;
            }
        """)
        
        self.highlighter = JSONHighlighter(self.text_edit.document())
        layout.addWidget(self.text_edit)
        self.set_placeholder()

    def set_placeholder(self):
        self.lbl_info.setText("📄 Raw manifest payload")
        self.text_edit.setPlainText("// Select an RSMF container from the left pane to inspect formatted manifest.json")

    def load_payload(self, payload: RSMFPayload):
        if not payload or not payload.raw_json_str:
            self.set_placeholder()
            return

        manifest_label = payload.manifest_name or "rsmf_manifest.json"
        self.lbl_info.setText(f"📄 Streamed Payload: {manifest_label} ({len(payload.raw_json_str)} bytes)")
        
        try:
            parsed = json.loads(payload.raw_json_str)
            formatted_json = json.dumps(parsed, indent=2)
            self.text_edit.setPlainText(formatted_json)
        except Exception:
            self.text_edit.setPlainText(payload.raw_json_str)

    def search_text(self, query: str, backward: bool = False) -> bool:
        """Finds search hit, highlights in bright yellow with black text, and scrolls to line."""
        if not query:
            self.text_edit.setExtraSelections([])
            return False
            
        flags = QTextDocument.FindFlags()
        if backward:
            flags |= QTextDocument.FindBackward

        found = self.text_edit.find(query, flags)
        if not found:
            # Wrap around
            cursor = self.text_edit.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.End)
            else:
                cursor.movePosition(QTextCursor.Start)
            self.text_edit.setTextCursor(cursor)
            found = self.text_edit.find(query, flags)

        if found:
            self.text_edit.ensureCursorVisible()
            
            # Apply bright yellow extra selection highlight
            cursor = self.text_edit.textCursor()
            extra = QTextEdit.ExtraSelection()
            extra.cursor = cursor
            extra.format.setBackground(QColor("#ffff00")) # Yellow
            extra.format.setForeground(QColor("#000000")) # Black
            self.text_edit.setExtraSelections([extra])

        return found

    def _copy_to_clipboard(self):
        clipboard = self.text_edit.QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
