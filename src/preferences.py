from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from config import CONFIG, save_config


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XUI Designer Preferences")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.inputs = {}

        # Syntax Colors
        for key, val in CONFIG["syntax_colors"].items():
            line_edit = QLineEdit(val)
            self.inputs[f"syntax_{key}"] = line_edit
            form_layout.addRow(f"Syntax - {key.capitalize()}:", line_edit)

        # UI Colors
        for key, val in CONFIG["ui_colors"].items():
            line_edit = QLineEdit(val)
            self.inputs[f"ui_{key}"] = line_edit
            form_layout.addRow(f"UI - {key.replace('_', ' ').capitalize()}:", line_edit)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save && Restart")
        save_btn.clicked.connect(self.save_and_close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save_and_close(self):
        for key, val in CONFIG["syntax_colors"].items():
            CONFIG["syntax_colors"][key] = self.inputs[f"syntax_{key}"].text()
        for key, val in CONFIG["ui_colors"].items():
            CONFIG["ui_colors"][key] = self.inputs[f"ui_{key}"].text()

        save_config(CONFIG)
        QMessageBox.information(self, "Saved", "Preferences saved. Please restart the application to apply UI changes.")
        self.accept()