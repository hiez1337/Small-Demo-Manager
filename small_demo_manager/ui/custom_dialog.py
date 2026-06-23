from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QPushButton, QLabel
)
from PyQt6.QtCore import Qt


class RenameDialog(QDialog):
    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Demo File")
        self.setMinimumWidth(450)
        self.setModal(True)

        self.result_text = ""
        self.result_combo_index = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info_label = QLabel(f"Current name: {current_name}")
        info_label.setObjectName("infoLabel")
        layout.addWidget(info_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter new file name (without extension)")
        layout.addWidget(self.name_input)

        self.combo_box = QComboBox()
        self.combo_box.addItems([
            "Expand original name (prefix)",
            "Completely new name",
            "Keep original name",
        ])
        layout.addWidget(self.combo_box)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self._on_accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _on_accept(self):
        self.result_text = self.name_input.text()
        self.result_combo_index = self.combo_box.currentIndex()
        self.accept()
