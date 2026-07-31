from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from rsmf_inspector.models.rsmf_payload import RSMFPayload

class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, initial_value: str, icon_str: str, accent_color: str, is_clickable: bool = False, is_compact_text: bool = False, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.is_clickable = is_clickable
        self.is_compact_text = is_compact_text
        
        self.setFixedHeight(72)
        
        if is_clickable:
            self.setCursor(Qt.PointingHandCursor)
            
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        
        # Header Row (Icon + Title)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel(icon_str)
        self.icon_label.setStyleSheet(f"font-size: 14px; color: {accent_color};")
        header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 700; text-transform: uppercase;")
        header_layout.addWidget(self.title_label)
        
        if is_clickable:
            click_hint = QLabel("🔍")
            click_hint.setStyleSheet("font-size: 10px; color: #64748b;")
            click_hint.setToolTip("Click to view list")
            header_layout.addWidget(click_hint)

        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value Label
        font_size = "12px" if is_compact_text else "18px"
        self.value_label = QLabel(initial_value)
        self.value_label.setStyleSheet(f"color: #f8fafc; font-size: {font_size}; font-weight: 700; font-family: 'Segoe UI', sans-serif;")
        self.value_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.value_label.setWordWrap(True)
        layout.addWidget(self.value_label)

    def _update_style(self):
        hover_style = f"border: 1px solid {self.accent_color}; background-color: #243347;" if self.is_clickable else "border: 1px solid #475569;"
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }}
            MetricCard:hover {{
                {hover_style}
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_clickable:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_value(self, text: str):
        self.value_label.setText(text)


class TopMetricCardsPane(QWidget):
    participants_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 4)
        main_layout.setSpacing(10)
        
        # Card 1: Participants Count (Clickable!)
        self.card_participants = MetricCard("Participants", "0", "👥", "#38bdf8", is_clickable=True)
        self.card_participants.clicked.connect(self.participants_clicked.emit)
        self.card_participants.setToolTip("Click to view full participants list in alphabetical order")
        main_layout.addWidget(self.card_participants, stretch=1)
        
        # Card 2: Message Event Count
        self.card_events = MetricCard("Message Events", "0", "💬", "#34d399")
        main_layout.addWidget(self.card_events, stretch=1)
        
        # Card 3: Attachment Count
        self.card_attachments = MetricCard("Attachments", "0", "📎", "#a78bfa")
        main_layout.addWidget(self.card_attachments, stretch=1)
        
        # Card 4: Date Range (Compact Text)
        self.card_daterange = MetricCard("Date Range", "N/A", "📅", "#fbbf24", is_compact_text=True)
        main_layout.addWidget(self.card_daterange, stretch=2)

    def update_metrics(self, payload: RSMFPayload):
        """Updates metric cards with stats parsed from RSMF payload."""
        if not payload:
            self.clear_metrics()
            return
            
        self.card_participants.set_value(str(payload.participant_count))
        self.card_events.set_value(str(payload.event_count))
        self.card_attachments.set_value(str(payload.attachment_count))
        self.card_daterange.set_value(payload.date_range_str)

    def clear_metrics(self):
        self.card_participants.set_value("0")
        self.card_events.set_value("0")
        self.card_attachments.set_value("0")
        self.card_daterange.set_value("N/A")
