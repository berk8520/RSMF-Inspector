import os
from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QLineEdit, QLabel, QFileDialog, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal, Qt

class FileListPane(QWidget):
    # Signal emitted when a file is selected: (filename, full_path)
    file_selected = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files_dict: Dict[str, str] = {}  # filename -> full_path dictionary
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Header / Group Box
        group_box = QGroupBox("📁 RSMF Containers")
        group_box.setStyleSheet("""
            QGroupBox {
                color: #38bdf8;
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
        
        gb_layout = QVBoxLayout(group_box)
        gb_layout.setContentsMargins(8, 12, 8, 8)
        gb_layout.setSpacing(8)
        
        # Directory Selection Button
        self.btn_select_dir = QPushButton("📂 Open Directory...")
        self.btn_select_dir.setCursor(Qt.PointingHandCursor)
        self.btn_select_dir.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
            }
        """)
        self.btn_select_dir.clicked.connect(self.select_directory)
        gb_layout.addWidget(self.btn_select_dir)

        # Search Filter Input
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("🔍 Filter files...")
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
                border: 1px solid #38bdf8;
            }
        """)
        self.txt_filter.textChanged.connect(self._filter_list)
        gb_layout.addWidget(self.txt_filter)
        
        # QListWidget for File Display
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
                color: #38bdf8;
            }
            QListWidget::item:selected {
                background-color: #1e3a8a;
                color: #ffffff;
                border-radius: 4px;
            }
        """)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        gb_layout.addWidget(self.list_widget)
        
        # Status Count Label
        self.lbl_status = QLabel("No directory loaded")
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 11px;")
        gb_layout.addWidget(self.lbl_status)
        
        layout.addWidget(group_box)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select RSMF Container Directory")
        if dir_path:
            self.load_directory(dir_path)

    def load_directory(self, dir_path: str):
        self.files_dict.clear()
        self.list_widget.clear()
        
        if not os.path.exists(dir_path):
            QMessageBox.warning(self, "Directory Warning", f"Selected directory does not exist:\n{dir_path}")
            return

        rsmf_extensions = ('.rsmf', '.zip')
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(rsmf_extensions):
                    full_path = os.path.join(root, file)
                    display_name = file
                    if display_name in self.files_dict and self.files_dict[display_name] != full_path:
                        display_name = f"{file} ({os.path.basename(root)})"
                    self.files_dict[display_name] = full_path

        self._populate_list(self.files_dict)
        count = len(self.files_dict)
        self.lbl_status.setText(f"Found {count} RSMF container{'s' if count != 1 else ''}")

    def _populate_list(self, files_map: Dict[str, str]):
        self.list_widget.clear()
        for filename in sorted(files_map.keys()):
            item = QListWidgetItem(f"📦 {filename}")
            item.setData(Qt.UserRole, files_map[filename])
            self.list_widget.addItem(item)

    def _filter_list(self, text: str):
        query = text.strip().lower()
        if not query:
            self._populate_list(self.files_dict)
            return
            
        filtered = {
            fname: fpath for fname, fpath in self.files_dict.items()
            if query in fname.lower()
        }
        self._populate_list(filtered)

    def get_all_loaded_files(self) -> Dict[str, str]:
        """Returns dictionary of display_name -> full_path for all currently loaded RSMF containers."""
        return dict(self.files_dict)

    def _on_selection_changed(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            full_path = item.data(Qt.UserRole)
            display_name = item.text().replace("📦 ", "")
            self.file_selected.emit(display_name, full_path)

