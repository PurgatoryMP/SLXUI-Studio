import os
import sys
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QIcon
from main_window import MainWindow
from config import CONFIG
from textures import TextureManager

try:
    myappid = 'mycompany.xui_designer.editor.1'  # Arbitrary unique string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except AttributeError:
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(root_dir, "icon.ico")

    if not os.path.exists(icon_path):
        print(f"[Warning] Icon file not found at: {icon_path}")
    else:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(CONFIG["ui_colors"]["window_bg"]))
    palette.setColor(QPalette.WindowText, QColor(CONFIG["ui_colors"]["window_text"]))
    palette.setColor(QPalette.Base, QColor(CONFIG["ui_colors"]["tree_bg"]))
    palette.setColor(QPalette.AlternateBase, QColor(CONFIG["ui_colors"]["window_bg"]))
    palette.setColor(QPalette.Text, QColor(CONFIG["ui_colors"]["window_text"]))
    palette.setColor(QPalette.Button, QColor(CONFIG["ui_colors"]["window_bg"]))
    palette.setColor(QPalette.ButtonText, QColor(CONFIG["ui_colors"]["window_text"]))

    # --- Highlight & Inactive Highlight Colors ---
    highlight_color = QColor(CONFIG["ui_colors"]["highlight"])
    highlighted_text = QColor("#FFFFFF")

    palette.setColor(QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.HighlightedText, highlighted_text)

    # Force Qt to show the colored highlight box even when the Tree Widget is out of focus
    palette.setColor(QPalette.Inactive, QPalette.Highlight, highlight_color)
    palette.setColor(QPalette.Inactive, QPalette.HighlightedText, highlighted_text)

    app.setPalette(palette)
    TextureManager()
    window = MainWindow()

    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.show()
    sys.exit(app.exec())