from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            title_font = title_label.font()
            title_font.setPointSize(11)
            title_font.setBold(True)
            title_label.setFont(title_font)
            layout.addWidget(title_label)

        self.content_layout = layout

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)


class IconButton(QPushButton):
    def __init__(self, text: str = "", icon_char: str = "", parent=None):
        super().__init__(parent)
        if icon_char:
            self.setText(f"{icon_char}  {text}" if text else icon_char)
        else:
            self.setText(text)
        self.setObjectName("iconButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("sectionHeader")
        font = self.font()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)


class ClickableLabel(QLabel):
    def __init__(self, text: str, url: str = "", parent=None):
        super().__init__(text, parent)
        self._url = url
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("clickableLabel")

    def mousePressEvent(self, event):
        if self._url:
            import webbrowser
            webbrowser.open(self._url)
        super().mousePressEvent(event)
