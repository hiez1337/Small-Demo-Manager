import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def run_app(demo_file_on_startup: str = ""):
    app = QApplication(sys.argv)
    app.setOrganizationName("Small-Demo-Manager")
    app.setApplicationName("Small Demo Manager")

    app.setStyle("Fusion")

    window = MainWindow(app, demo_file_on_startup)
    window.show()

    return app.exec()
