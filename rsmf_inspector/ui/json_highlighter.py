import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import Qt

class JSONHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # Key format (e.g., "key":)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#38bdf8"))  # Cyan / Light Blue
        key_format.setFontWeight(QFont.Bold)
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"\s*:'), key_format))

        # String value format (e.g., "value")
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#4ade80"))  # Soft Green
        self.rules.append((re.compile(r':\s*("[^"\\]*(\\.[^"\\]*)*")'), string_format))

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#fbbf24"))  # Amber / Gold
        self.rules.append((re.compile(r'\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b'), number_format))

        # Keywords (true, false, null)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#c084fc"))  # Purple
        keyword_format.setFontWeight(QFont.Bold)
        self.rules.append((re.compile(r'\b(true|false|null)\b'), keyword_format))

        # Punctuation ({ } [ ] ,)
        punct_format = QTextCharFormat()
        punct_format.setForeground(QColor("#94a3b8"))  # Slate Gray
        self.rules.append((re.compile(r'[\{\}\[\],]'), punct_format))

    def highlightBlock(self, text: str):
        # Apply string values first, then keys, numbers, keywords
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                # If key format, highlight key part without trailing colon
                if fmt.foreground().color().name() == "#38bdf8":
                    colon_idx = text.find(':', start)
                    if colon_idx != -1 and colon_idx < match.end():
                        length = colon_idx - start
                # If string value format, only highlight the string part
                elif match.lastindex and match.lastindex >= 1:
                    start = match.start(1)
                    length = match.end(1) - start
                
                self.setFormat(start, length, fmt)
