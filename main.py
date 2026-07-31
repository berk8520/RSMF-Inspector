import sys
import os

# Ensure project root is in python sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from rsmf_inspector.ui.main_window import RSMFInspectorWindow

from PySide6.QtGui import QIcon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RSMF Inspector")
    app.setOrganizationName("Page One Legal")
    
    # Load application icon from assets
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    icon_path = os.path.join(assets_dir, "app_icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(assets_dir, "icon.png")
    
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = RSMFInspectorWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    
    # If a directory argument was provided via CLI, load it automatically
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        window.left_pane.load_directory(sys.argv[1])
        
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
