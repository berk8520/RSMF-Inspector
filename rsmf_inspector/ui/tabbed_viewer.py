from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Qt
from rsmf_inspector.models.rsmf_payload import RSMFPayload
from rsmf_inspector.ui.rsmf_chat_tab import RSMFChatTab
from rsmf_inspector.ui.json_view_tab import JSONViewTab

class TabbedViewerPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_payload: RSMFPayload = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # -------------------------------------------------------------
        # Top Search Bar for Active Viewing Tab (RSMF or JSON)
        # -------------------------------------------------------------
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 2)
        search_layout.setSpacing(6)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search in active tab (RSMF Chat or JSON)...")
        self.txt_search.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)
        self.txt_search.textChanged.connect(self._on_search_text_changed)
        self.txt_search.returnPressed.connect(self._find_next)
        search_layout.addWidget(self.txt_search)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(self._btn_style())
        self.btn_prev.clicked.connect(self._find_prev)
        search_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(self._btn_style())
        self.btn_next.clicked.connect(self._find_next)
        search_layout.addWidget(self.btn_next)

        self.lbl_search_info = QLabel("Target: 💬 RSMF View")
        self.lbl_search_info.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; padding: 0 4px;")
        search_layout.addWidget(self.lbl_search_info)

        main_layout.addLayout(search_layout)

        # -------------------------------------------------------------
        # Main Tab Widget (RSMF View & JSON View)
        # -------------------------------------------------------------
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #0f172a;
                border-radius: 8px;
                padding: 4px;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 16px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #334155;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #0f172a;
                color: #38bdf8;
                border-top: 2px solid #38bdf8;
            }
            QTabBar::tab:hover:!selected {
                background-color: #283548;
                color: #f1f5f9;
            }
        """)

        # Tab 1: RSMF Chat Thread View
        self.chat_tab = RSMFChatTab()
        self.tab_widget.addTab(self.chat_tab, "💬 RSMF View")
        
        # Tab 2: Raw manifest.json Stream View (Syntax Highlighted)
        self.json_tab = JSONViewTab()
        self.tab_widget.addTab(self.json_tab, "📄 JSON View")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)

    @staticmethod
    def _btn_style() -> str:
        return """
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                font-weight: 600;
                font-size: 11px;
                padding: 6px 12px;
                border-radius: 5px;
                border: 1px solid #475569;
            }
            QPushButton:hover {
                background-color: #475569;
                color: #38bdf8;
            }
        """

    def load_payload(self, payload: RSMFPayload):
        self.current_payload = payload
        self.chat_tab.load_payload(payload)
        self.json_tab.load_payload(payload)
        if self.txt_search.text():
            self._on_search_text_changed(self.txt_search.text())

    def _on_tab_changed(self, index: int):
        tab_name = "💬 RSMF View" if index == 0 else "📄 JSON View"
        self.lbl_search_info.setText(f"Target: {tab_name}")
        query = self.txt_search.text().strip()
        if query:
            self._do_search(query, backward=False)

    def _on_search_text_changed(self, text: str):
        query = text.strip()
        if not query:
            self._update_info_label(True)
            return
        self._do_search(query, backward=False)

    def _find_next(self):
        query = self.txt_search.text().strip()
        if query:
            self._do_search(query, backward=False)

    def _find_prev(self):
        query = self.txt_search.text().strip()
        if query:
            self._do_search(query, backward=True)

    def _do_search(self, query: str, backward: bool = False):
        active_widget = self.tab_widget.currentWidget()
        if hasattr(active_widget, 'search_text'):
            found = active_widget.search_text(query, backward=backward)
            self._update_info_label(found)

    def _update_info_label(self, found: bool):
        tab_name = "💬 RSMF View" if self.tab_widget.currentIndex() == 0 else "📄 JSON View"
        query = self.txt_search.text().strip()
        if not query:
            self.lbl_search_info.setText(f"Target: {tab_name}")
            self.lbl_search_info.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; padding: 0 4px;")
        elif found:
            self.lbl_search_info.setText(f"Target: {tab_name} (Match Found)")
            self.lbl_search_info.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: 600; padding: 0 4px;")
        else:
            self.lbl_search_info.setText(f"Target: {tab_name} (No Matches)")
            self.lbl_search_info.setStyleSheet("color: #f87171; font-size: 11px; font-weight: 600; padding: 0 4px;")
