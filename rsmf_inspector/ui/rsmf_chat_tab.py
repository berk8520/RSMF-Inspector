from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtGui import QTextDocument, QPalette, QColor, QTextCursor
from PySide6.QtCore import Qt, QUrl
from rsmf_inspector.models.rsmf_payload import RSMFPayload
from rsmf_inspector.services.rsmf_parser import RSMFParserService
from rsmf_inspector.ui.attachment_pane import AttachmentPane

class RSMFChatTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)  # Intercept anchor clicks to open in OS default application
        self.browser.anchorClicked.connect(self._on_anchor_clicked)
        
        palette = self.browser.palette()
        palette.setColor(QPalette.Highlight, QColor("#ffff00"))      # Bright Yellow
        palette.setColor(QPalette.HighlightedText, QColor("#000000")) # Black Text
        self.browser.setPalette(palette)

        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #e2e8f0;
                selection-background-color: #ffff00;
                selection-color: #000000;
            }
        """)
        layout.addWidget(self.browser)
        self.set_placeholder()

    def set_placeholder(self):
        placeholder_html = """
        <div style="text-align: center; color: #64748b; margin-top: 100px; font-family: sans-serif;">
            <h2>💬 RSMF Chat View</h2>
            <p>Select an RSMF container from the left pane to render the phone-style chat thread.</p>
        </div>
        """
        self.browser.setHtml(placeholder_html)

    def load_payload(self, payload: RSMFPayload):
        if not payload:
            self.set_placeholder()
            return
            
        html_content = RSMFParserService.generate_html_chat(payload)
        self.browser.setHtml(html_content)

    def _on_anchor_clicked(self, url: QUrl):
        """Launches hyperlinked attachment in OS default application."""
        file_path = url.toLocalFile()
        if file_path:
            try:
                AttachmentPane.open_file_with_default_app(file_path)
            except Exception as ex:
                pass

    def search_text(self, query: str, backward: bool = False) -> bool:
        """Finds text hit, highlights in bright yellow with black text, and scrolls directly to the line."""
        if not query:
            return False
            
        flags = QTextDocument.FindFlags()
        if backward:
            flags |= QTextDocument.FindBackward

        found = self.browser.find(query, flags)
        if not found:
            cursor = self.browser.textCursor()
            if backward:
                cursor.movePosition(QTextCursor.End)
            else:
                cursor.movePosition(QTextCursor.Start)
            self.browser.setTextCursor(cursor)
            found = self.browser.find(query, flags)

        if found:
            self.browser.ensureCursorVisible()

        return found
