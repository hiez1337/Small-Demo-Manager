import os
import re
import hashlib
import shutil
import webbrowser
import urllib.request
import json
import threading
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QProgressBar, QFileDialog, QMessageBox, QMenu, QSizePolicy,
    QFrame, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QBrush, QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect

from qt_material import apply_stylesheet

from models import PlayerSnapshot, MatchResult, AudioEntry
from demo_parser import CS2DemoParser
from audio_extractor import extract_voice
import audio_player
import audio_file_manager as afm
from config import read, write, key_exists
from translate import tr, get_translator
from ui.widgets import Card, IconButton, SectionHeader, ClickableLabel
from tokens import TOKENS


GITHUB_REPO = "https://api.github.com/repos/pythaeusone/Faceit-Demo-Voice-Calculator/releases"
PATCH_NOTES_URL = "https://raw.githubusercontent.com/hiez1337/Small-Demo-Manager/main/PATCH_NOTES.md"
CURRENT_VERSION = "1.0.8"
if getattr(sys, "frozen", False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = str(Path(__file__).resolve().parent.parent)
_RES_DIR = os.path.join(_BASE_DIR, "resources")
_TAB_ICONS = {
    "home": os.path.join(_RES_DIR, "homeNew.png"),
    "calc": os.path.join(_RES_DIR, "calculatorNew.png"),
    "match": os.path.join(_RES_DIR, "matchDetailsTrashStar.png"),
    "audio": os.path.join(_RES_DIR, "audioNew.png"),
    "settings": os.path.join(_RES_DIR, "settingsNew.png"),
    "about": os.path.join(_RES_DIR, "aboutNew.png"),
    "howto": os.path.join(_RES_DIR, "howTo2New.png"),
}


class ParseWorker(QThread):
    finished = pyqtSignal(list, object, bool)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            parser = CS2DemoParser(self.file_path)
            snapshots, match_result = parser.parse()
            self.finished.emit(snapshots, match_result, parser.is_sourcetv)
        except Exception as e:
            self.error.emit(str(e))


class AudioExtractWorker(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, demo_path: str, output_dir: str):
        super().__init__()
        self.demo_path = demo_path
        self.output_dir = output_dir

    def run(self):
        try:
            result = extract_voice(
                self.demo_path, self.output_dir,
                progress_callback=self.progress.emit
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    patch_notes_fetched = pyqtSignal(str)
    update_available = pyqtSignal(str)

    def __init__(self, app_ref, demo_file_on_startup: str = ""):
        super().__init__()
        self._app_ref = app_ref
        self._is_dark = read("IsDarkMode", False)
        self._demo_on_startup = demo_file_on_startup
        self.snapshots: list[PlayerSnapshot] = []
        self.match_result: Optional[MatchResult] = None
        self.audio_entries: dict[str, list[AudioEntry]] = {}
        self.demo_path = ""
        self.demo_name = ""
        self._current_player_audio: list[AudioEntry] = []
        self._selected_player_name: str = ""
        self._parse_worker: Optional[ParseWorker] = None
        self._audio_worker: Optional[AudioExtractWorker] = None
        self._tab_anim: Optional[QPropertyAnimation] = None
        self.patch_notes_fetched.connect(self._on_patch_notes_fetched)
        self.update_available.connect(lambda msg: self._snackbar(msg))
        self._tr = get_translator()
        saved_lang = read("Language", "en")
        self._tr.load(saved_lang)
        self._tr.language_changed.connect(self._retranslate)

        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(1100, 620)
        self.setAcceptDrops(True)

        self._init_ui()
        self.apply_theme()
        self._check_for_updates()

        if self._demo_on_startup and os.path.isfile(self._demo_on_startup):
            QTimer.singleShot(200, lambda: self._load_demo(self._demo_on_startup))

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.currentChanged.connect(self._animate_tab_fade)
        main_layout.addWidget(self.tabs)

        self.tab_home = self._create_home_tab()
        self.tab_bitfield = self._create_bitfield_tab()
        self.tab_match = self._create_match_tab()
        self.tab_audio = self._create_audio_tab()
        self.tab_settings = self._create_settings_tab()
        self.tab_about = self._create_about_tab()
        self.tab_howto = self._create_howto_tab()

        icon_keys = ["home", "calc", "match", "audio", "settings", "about", "howto"]
        tab_keys = ["tab.home", "tab.bitfield", "tab.match", "tab.audio", "tab.settings", "tab.about", "tab.howto"]
        tabs = [self.tab_home, self.tab_bitfield, self.tab_match, self.tab_audio, self.tab_settings, self.tab_about, self.tab_howto]
        for i, tab in enumerate(tabs):
            icon_path = _TAB_ICONS[icon_keys[i]]
            icon = QIcon(QPixmap(icon_path)) if os.path.isfile(icon_path) else QIcon()
            self.tabs.addTab(tab, icon, tr(tab_keys[i]))

    def apply_theme(self):
        theme = "dark_teal.xml" if self._is_dark else "light_teal.xml"
        apply_stylesheet(self._app_ref, theme=theme)
        ss = self._app_ref.styleSheet()

        c = TOKENS.light_colors if not self._is_dark else TOKENS.colors
        t = TOKENS.typography
        s = TOKENS.spacing
        b = TOKENS.borders

        btn_style = f"""
        QPushButton {{
            text-align: center; padding: {s.sm} {s.lg}; border-radius: {b.radius_md};
            font-size: {t.size_base}; font-family: {t.font_family};
            min-width: 90px;
        }}
        QPushButton#langBtn:checked {{
            background-color: {c.accent_button}; color: {c.text_on_accent};
            border: {b.width_default} solid {c.accent_button}; font-weight: {t.weight_bold};
        }}
        QPushButton#langBtn:!checked {{
            background-color: {c.surface_card}; color: {c.text_primary};
            border: {b.width_default} solid {c.border};
        }}
        QPushButton#langBtn:!checked:hover {{
            border: {b.width_default} solid {c.accent_light};
        }}
        QPushButton#primaryButton {{
            background-color: {c.accent_button}; color: {c.text_on_accent};
            border: {b.width_default} solid {c.accent_button}; font-weight: {t.weight_bold};
            padding: {s.sm} {s.xl};
        }}
        QPushButton#primaryButton:hover {{
            background-color: {c.accent_hover};
        }}
        """
        ss += btn_style
        ss += f"""
        QListWidget::item {{ padding: {s.xs} {s.sm}; }}
        QListWidget::item:checked {{ background-color: {c.selection_bg}; }}
        QListWidget::indicator {{
            width: 16px; height: 16px;
            border: {b.width_focus} solid {c.border};
            border-radius: {b.radius_sm}; background: {c.indicator_bg};
            margin-right: {s.sm};
        }}
        QListWidget::indicator:checked {{
            background: {c.accent_button}; border: {b.width_focus} solid {c.accent_button};
        }}
        QListWidget::indicator:hover {{
            border: {b.width_focus} solid {c.accent_light};
        }}
        QLineEdit#dropField, QLineEdit#commandField {{
            border: {b.width_default} solid {c.border}; border-radius: {b.radius_md};
            padding: {s.xs} {s.sm}; font-family: {t.font_family};
        }}
        QStatusBar {{
            font-size: {t.size_sm}; color: {c.text_secondary};
        }}
        """
        self._app_ref.setStyleSheet(ss)

    def toggle_theme(self):
        self._is_dark = not self._is_dark
        write("IsDarkMode", self._is_dark)
        self.apply_theme()

    def _snackbar(self, message: str, error: bool = False):
        self.statusBar().showMessage(message, 5000)

    # ─── Home Tab ───────────────────────────────────────────────

    def _create_home_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._home_header = SectionHeader(tr("home.header"))
        self._home_header.setObjectName("homeHeader")
        layout.addWidget(self._home_header)

        self._welcome_card = Card(tr("home.welcome.title"))
        self._welcome_lbl = QLabel(tr("home.welcome.text"))
        self._welcome_lbl.setWordWrap(True)
        self._welcome_card.add_widget(self._welcome_lbl)
        layout.addWidget(self._welcome_card)

        drop_layout = QHBoxLayout()
        self.home_file_path = QLineEdit()
        self.home_file_path.setReadOnly(True)
        self.home_file_path.setPlaceholderText(tr("home.drop.placeholder"))
        self.home_file_path.setObjectName("dropField")
        self.home_file_path.dragEnterEvent = self._drag_enter
        self.home_file_path.dragMoveEvent = self._drag_move
        self.home_file_path.dropEvent = self._drop
        drop_layout.addWidget(self.home_file_path)

        self._load_btn = QPushButton(tr("home.load.button"))
        self._load_btn.setObjectName("primaryButton")
        self._load_btn.clicked.connect(lambda: self._open_file_dialog())
        drop_layout.addWidget(self._load_btn)
        layout.addLayout(drop_layout)

        self._patch_card = Card(tr("home.notes.title"))
        self.patch_notes = QTextEdit()
        self.patch_notes.setReadOnly(True)
        self.patch_notes.setMaximumHeight(200)
        self.patch_notes.setObjectName("patchNotes")
        self.patch_notes.setPlainText(tr("home.notes.loading"))
        self._patch_card.add_widget(self.patch_notes)
        layout.addWidget(self._patch_card)
        layout.addStretch()
        QTimer.singleShot(100, self._fetch_patch_notes)

        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    # ─── Bitfield-Calc Tab ─────────────────────────────────────

    def _create_bitfield_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        drop_layout = QHBoxLayout()
        self.bf_file_path = QLineEdit()
        self.bf_file_path.setReadOnly(True)
        self.bf_file_path.setPlaceholderText(tr("bitfield.drop.placeholder"))
        self.bf_file_path.setObjectName("dropField")
        self.bf_file_path.dragEnterEvent = self._drag_enter
        self.bf_file_path.dragMoveEvent = self._drag_move
        self.bf_file_path.dropEvent = self._drop
        drop_layout.addWidget(self.bf_file_path)

        self.bf_move_btn = QPushButton(tr("bitfield.move.button"))
        self.bf_move_btn.clicked.connect(self._move_to_cs2)
        drop_layout.addWidget(self.bf_move_btn)
        layout.addLayout(drop_layout)

        info_layout = QHBoxLayout()
        self.lbl_map = QLabel(tr("bitfield.map") + " -")
        self.lbl_duration = QLabel(tr("bitfield.duration") + " -")
        self.lbl_vs = QLabel("VS")
        info_layout.addWidget(self.lbl_map)
        info_layout.addWidget(self.lbl_duration)
        info_layout.addStretch()
        self.lbl_team_a = QLabel(tr("bitfield.team_a"))
        self.lbl_team_b = QLabel(tr("bitfield.team_b"))
        info_layout.addWidget(self.lbl_team_a, alignment=Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.lbl_vs)
        info_layout.addWidget(self.lbl_team_b)
        layout.addLayout(info_layout)

        teams_layout = QHBoxLayout()
        self.team_a_list = QListWidget()
        self.team_a_list.setObjectName("teamList")
        self.team_a_list.itemClicked.connect(self._update_bitfield)
        self.team_b_list = QListWidget()
        self.team_b_list.setObjectName("teamList")
        self.team_b_list.itemClicked.connect(self._update_bitfield)
        teams_layout.addWidget(self.team_a_list)
        teams_layout.addWidget(self.team_b_list)
        layout.addLayout(teams_layout, stretch=1)

        cmd_layout = QHBoxLayout()
        self._cmd_label = QLabel(tr("bitfield.command.label"))
        cmd_layout.addWidget(self._cmd_label)
        self.tb_command = QLineEdit()
        self.tb_command.setReadOnly(True)
        self.tb_command.setObjectName("commandField")
        cmd_layout.addWidget(self.tb_command)

        self._copy_btn = QPushButton(tr("bitfield.copy.button"))
        self._copy_btn.setObjectName("primaryButton")
        self._copy_btn.clicked.connect(self._copy_command)
        cmd_layout.addWidget(self._copy_btn)
        layout.addLayout(cmd_layout)

        self.bf_progress = QProgressBar()
        self.bf_progress.setObjectName("loadProgress")
        self.bf_progress.setVisible(False)
        layout.addWidget(self.bf_progress)

        return tab

    # ─── Match-Results Tab ─────────────────────────────────────

    def _create_match_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.match_header_a = SectionHeader("Team A — 0")
        layout.addWidget(self.match_header_a)

        self.match_table_a = QTableWidget()
        self.match_table_a.setObjectName("matchTable")
        self._setup_match_table(self.match_table_a)
        layout.addWidget(self.match_table_a)

        self.match_header_b = SectionHeader("Team B — 0")
        layout.addWidget(self.match_header_b)

        self.match_table_b = QTableWidget()
        self.match_table_b.setObjectName("matchTable")
        self._setup_match_table(self.match_table_b)
        layout.addWidget(self.match_table_b)

        return tab

    def _setup_match_table(self, table: QTableWidget):
        cols = ["Player", "K", "D", "A", "K/D", "HS", "HS%", "MVP", "3K", "4K", "5K", "Damage"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

    # ─── Audio-Player Tab ──────────────────────────────────────

    def _create_audio_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        btn_layout = QHBoxLayout()
        self.extract_btn = QPushButton(tr("audio.extract.button"))
        self.extract_btn.setObjectName("primaryButton")
        self.extract_btn.clicked.connect(self._extract_audio)
        self.extract_btn.setEnabled(False)
        btn_layout.addWidget(self.extract_btn)
        self.save_all_btn = QPushButton(tr("audio.save_all.button"))
        self.save_all_btn.setEnabled(False)
        self.save_all_btn.clicked.connect(self._save_all_player_audio)
        btn_layout.addWidget(self.save_all_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.audio_progress = QProgressBar()
        self.audio_progress.setObjectName("audioProgress")
        self.audio_progress.setVisible(False)
        layout.addWidget(self.audio_progress)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(8)

        left_layout = QVBoxLayout()
        self._players_label = QLabel(tr("audio.players.label"))
        left_layout.addWidget(self._players_label)
        self.player_audio_list = QListWidget()
        self.player_audio_list.setObjectName("audioList")
        self.player_audio_list.currentRowChanged.connect(self._on_player_selected)
        self.player_audio_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.player_audio_list.customContextMenuRequested.connect(self._player_audio_context_menu)
        left_layout.addWidget(self.player_audio_list)
        lists_layout.addLayout(left_layout)

        mid_layout = QVBoxLayout()
        self._voices_label = QLabel(tr("audio.voices.label"))
        mid_layout.addWidget(self._voices_label)
        self.voice_list = QListWidget()
        self.voice_list.setObjectName("audioList")
        self.voice_list.itemDoubleClicked.connect(self._play_selected_audio)
        self.voice_list.customContextMenuRequested.connect(
            lambda pos: self._audio_context_menu(pos)
        )
        self.voice_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        mid_layout.addWidget(self.voice_list)
        lists_layout.addLayout(mid_layout)

        right_layout = QVBoxLayout()
        self._saved_label2 = QLabel(tr("audio.saved.label"))
        right_layout.addWidget(self._saved_label2)
        self.saved_voice_list = QListWidget()
        self.saved_voice_list.setObjectName("audioList")
        self.saved_voice_list.itemDoubleClicked.connect(self._play_saved_audio)
        right_layout.addWidget(self.saved_voice_list)
        lists_layout.addLayout(right_layout)

        layout.addLayout(lists_layout, stretch=1)

        return tab

    # ─── Settings Tab ──────────────────────────────────────────

    def _create_settings_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._theme_card = Card(tr("settings.theme.title"))
        theme_row = QHBoxLayout()
        self._theme_label = QLabel(tr("settings.theme.dark"))
        theme_row.addWidget(self._theme_label)
        self.theme_switch = QCheckBox()
        self.theme_switch.setChecked(self._is_dark)
        self.theme_switch.toggled.connect(lambda: self.toggle_theme())
        theme_row.addWidget(self.theme_switch)
        theme_row.addStretch()
        self._theme_card.add_layout(theme_row)
        layout.addWidget(self._theme_card)

        self._path_card = Card(tr("settings.paths.title"))
        cs2_row = QHBoxLayout()
        self._cs2_label = QLabel(tr("settings.paths.cs2"))
        cs2_row.addWidget(self._cs2_label)
        self.cs2_path_input = QLineEdit()
        self.cs2_path_input.setText(read("CS2DemoPath", ""))
        cs2_row.addWidget(self.cs2_path_input)
        self._cs2_browse = QPushButton(tr("settings.paths.browse"))
        self._cs2_browse.clicked.connect(lambda: self._browse_folder("cs2"))
        cs2_row.addWidget(self._cs2_browse)
        self._path_card.add_layout(cs2_row)

        saved_row = QHBoxLayout()
        self._saved_label = QLabel(tr("settings.paths.saved"))
        saved_row.addWidget(self._saved_label)
        self.saved_path_input = QLineEdit()
        self.saved_path_input.setText(read("SavedVoiceFilesPath", ""))
        saved_row.addWidget(self.saved_path_input)
        self._saved_browse = QPushButton(tr("settings.paths.browse"))
        self._saved_browse.clicked.connect(lambda: self._browse_folder("saved"))
        saved_row.addWidget(self._saved_browse)
        self._path_card.add_layout(saved_row)
        layout.addWidget(self._path_card)

        shell_card = Card(tr("settings.shell.title"))
        shell_row = QHBoxLayout()
        self.shell_checkbox = QCheckBox(tr("settings.shell.checkbox"))
        from shell_context import validate_shell_integration
        self.shell_checkbox.setChecked(validate_shell_integration())
        self.shell_checkbox.toggled.connect(self._toggle_shell)
        shell_row.addWidget(self.shell_checkbox)
        shell_row.addStretch()
        shell_card.add_layout(shell_row)
        layout.addWidget(shell_card)

        lang_card = Card(tr("settings.lang.title"))
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(tr("settings.lang.label")))
        self.lang_btns: dict[str, QPushButton] = {}
        from translate import get_translator
        langs = get_translator().supported_languages()
        current_lang = self._tr.current_language
        for code, name in langs.items():
            btn = QPushButton(name)
            btn.setObjectName("langBtn")
            btn.setCheckable(True)
            btn.setChecked(code == current_lang)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumWidth(90)
            btn.clicked.connect(lambda checked, c=code: self._on_lang_btn_clicked(c))
            self.lang_btns[code] = btn
            lang_row.addWidget(btn)
        lang_row.addStretch()
        lang_card.add_layout(lang_row)
        layout.addWidget(lang_card)
        layout.addStretch()

        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    # ─── About Tab ─────────────────────────────────────────────

    def _create_about_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        inner = QWidget()
        self._about_layout = QVBoxLayout(inner)
        self._about_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._about_layout.setContentsMargins(20, 20, 20, 20)
        self._about_layout.setSpacing(12)

        self._about_card = Card(tr("about.title"))
        self._about_lbl = QLabel(tr("about.description"))
        self._about_lbl.setWordWrap(True)
        self._about_card.add_widget(self._about_lbl)
        self._about_layout.addWidget(self._about_card)

        self._version_card = Card(tr("about.version.title"))
        self._version_lbl = QLabel(f"v{CURRENT_VERSION} (Python port)")
        self._version_card.add_widget(self._version_lbl)
        self._author_lbl = QLabel(tr("about.author"))
        self._version_card.add_widget(self._author_lbl)
        self._fork_lbl = QLabel(tr("about.fork"))
        self._version_card.add_widget(self._fork_lbl)
        self._about_layout.addWidget(self._version_card)

        self._support_card = Card(tr("about.support.title"))
        self.update_btn = QPushButton(tr("about.update.button"))
        self.update_btn.clicked.connect(self._manual_update_check)
        self._support_card.add_widget(self.update_btn)

        self._github_btn = QPushButton(tr("about.github.button"))
        self._github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/pythaeusone/Faceit-Demo-Voice-Calculator")
        )
        self._support_card.add_widget(self._github_btn)

        self._fork_btn = QPushButton(tr("about.fork.button"))
        self._fork_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/hiez1337/Small-Demo-Manager")
        )
        self._support_card.add_widget(self._fork_btn)
        self._about_layout.addWidget(self._support_card)
        self._about_layout.addStretch()

        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    # ─── HowTo Tab ─────────────────────────────────────────────

    def _create_howto_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("scrollArea")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._howto_sections = [
            (tr("howto.bitfield.title"), tr("howto.bitfield.text")),
            (tr("howto.match.title"), tr("howto.match.text")),
            (tr("howto.audio.title"), tr("howto.audio.text")),
            (tr("howto.settings.title"), tr("howto.settings.text")),
        ]

        for title, text in self._howto_sections:
            card = Card(title)
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            card.add_widget(lbl)
            layout.addWidget(card)

        layout.addStretch()
        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    # ─── Drag & Drop ───────────────────────────────────────────

    def _drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".dem"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def _drag_move(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".dem"):
                self._load_demo(path)
                return

    # ─── Demo Loading ──────────────────────────────────────────

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CS2 Demo", "", "CS2 Demo (*.dem)"
        )
        if path:
            self._load_demo(path)

    def _load_demo(self, file_path: str):
        if not os.path.isfile(file_path):
            self._snackbar("File not found", error=True)
            return

        self.demo_path = file_path
        self.demo_name = os.path.splitext(os.path.basename(file_path))[0]

        self.bf_file_path.setText(file_path)
        self.home_file_path.setText(file_path)

        self.bf_progress.setVisible(True)
        self.bf_progress.setValue(0)

        self.team_a_list.clear()
        self.team_b_list.clear()
        self.match_table_a.setRowCount(0)
        self.match_table_b.setRowCount(0)
        self._clear_audio_selection()

        self.extract_btn.setEnabled(False)

        self._parse_worker = ParseWorker(file_path)
        self._parse_worker.finished.connect(self._on_demo_parsed)
        self._parse_worker.error.connect(self._on_demo_error)
        self._parse_worker.start()

    def _on_demo_parsed(self, snapshots: list[PlayerSnapshot], match_result: MatchResult, is_sourcetv: bool = False):
        self.bf_progress.setVisible(False)
        self.snapshots = snapshots
        self.match_result = match_result
        self._load_bitfield()
        self._load_match_results()

        team_a = [s for s in snapshots if s.team_number == 3]
        team_b = [s for s in snapshots if s.team_number == 2]

        self.lbl_map.setText(f"Map: {snapshots[0].team_name if snapshots else '-'}")
        self.lbl_duration.setText(f"Duration: -")
        self.lbl_team_a.setText(match_result.team_a_name)
        self.lbl_team_b.setText(match_result.team_b_name)
        self.lbl_vs.setText(f"({match_result.team_a_score}:{match_result.team_b_score})")

        self.extract_btn.setEnabled(True)

        if is_sourcetv:
            self._snackbar("Demo loaded successfully!")
        else:
            self._snackbar("Demo loaded. Voice extraction may be limited (not SourceTV).")

    def _on_demo_error(self, error_msg: str):
        self.bf_progress.setVisible(False)
        self._snackbar(f"Error: {error_msg}", error=True)

    # ─── Bitfield ──────────────────────────────────────────────

    def _load_bitfield(self):
        self.team_a_list.clear()
        self.team_b_list.clear()

        for snap in sorted(self.snapshots, key=lambda s: s.spec_id):
            if snap.team_number == 3:
                item = QListWidgetItem(f"{snap.player_name} (sl:{snap.spec_id})")
                item.setData(Qt.ItemDataRole.UserRole, snap.steam_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, snap.spec_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.team_a_list.addItem(item)

        for snap in sorted(self.snapshots, key=lambda s: s.spec_id):
            if snap.team_number == 2:
                item = QListWidgetItem(f"{snap.player_name} (sl:{snap.spec_id})")
                item.setData(Qt.ItemDataRole.UserRole, snap.steam_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, snap.spec_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.team_b_list.addItem(item)

        self._setup_player_context_menu(self.team_a_list)
        self._setup_player_context_menu(self.team_b_list)

    def _update_bitfield(self):
        bitfield = 0
        for i in range(self.team_a_list.count()):
            item = self.team_a_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                sid = item.data(Qt.ItemDataRole.UserRole + 1)
                bitfield |= 1 << (sid - 1)
        for i in range(self.team_b_list.count()):
            item = self.team_b_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                sid = item.data(Qt.ItemDataRole.UserRole + 1)
                bitfield |= 1 << (sid - 1)
        self.tb_command.setText(
            f"tv_listen_voice_indices {bitfield}; tv_listen_voice_indices_h {bitfield}"
        )

    def _copy_command(self):
        cmd = self.tb_command.text()
        if cmd:
            try:
                import pyperclip
                pyperclip.copy(cmd)
                self._snackbar("Command copied to clipboard!")
            except ImportError:
                self._snackbar("pyperclip not installed", error=True)

    # ─── Player Context Menus ──────────────────────────────────

    def _setup_player_context_menu(self, list_widget: QListWidget):
        list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        list_widget.customContextMenuRequested.connect(
            lambda pos: self._show_player_menu(pos, list_widget)
        )

    def _show_player_menu(self, pos, list_widget: QListWidget):
        item = list_widget.itemAt(pos)
        if not item:
            return
        steam_id = item.data(Qt.ItemDataRole.UserRole)
        if not steam_id:
            return
        menu = QMenu(self)
        profile_url = f"https://steamcommunity.com/profiles/{steam_id}"

        copy_action = QAction("Copy SteamID64", self)
        copy_action.triggered.connect(lambda: self._copy_steamid(steam_id))
        menu.addAction(copy_action)

        menu.addAction("Steam Profile", lambda: webbrowser.open(profile_url))
        menu.addAction("cswatch.in", lambda: webbrowser.open(f"https://cswatch.in/player/{steam_id}"))
        menu.addAction("leetify.com", lambda: webbrowser.open(f"https://leetify.com/player/{steam_id}"))
        menu.addAction("csstats.gg", lambda: webbrowser.open(f"https://csstats.gg/player/{steam_id}"))

        menu.exec(list_widget.viewport().mapToGlobal(pos))

    def _copy_steamid(self, steam_id: int):
        try:
            import pyperclip
            pyperclip.copy(str(steam_id))
            self._snackbar("SteamID64 copied!")
        except ImportError:
            self._snackbar("pyperclip not installed", error=True)

    # ─── Match Results ─────────────────────────────────────────

    def _load_match_results(self):
        team_a = [s for s in self.snapshots if s.team_number == 3]
        team_b = [s for s in self.snapshots if s.team_number == 2]

        if self.match_result:
            self.match_header_a.setText(
                f"{self.match_result.team_a_name} — {self.match_result.team_a_score}"
            )
            self.match_header_b.setText(
                f"{self.match_result.team_b_name} — {self.match_result.team_b_score}"
            )

        self._populate_match_table(self.match_table_a, team_a)
        self._populate_match_table(self.match_table_b, team_b)

    def _populate_match_table(self, table: QTableWidget, players: list[PlayerSnapshot]):
        table.setRowCount(len(players))
        for row, p in enumerate(players):
            table.setItem(row, 0, QTableWidgetItem(p.player_name))
            table.setItem(row, 1, QTableWidgetItem(str(p.kills)))
            table.setItem(row, 2, QTableWidgetItem(str(p.deaths)))
            table.setItem(row, 3, QTableWidgetItem(str(p.assists)))
            table.setItem(row, 4, QTableWidgetItem(str(p.kd)))
            table.setItem(row, 5, QTableWidgetItem(str(p.headshot_kills)))
            table.setItem(row, 6, QTableWidgetItem(f"{p.headshot_percent}%"))
            table.setItem(row, 7, QTableWidgetItem(str(p.mvp)))
            table.setItem(row, 8, QTableWidgetItem(str(p.three_k)))
            table.setItem(row, 9, QTableWidgetItem(str(p.four_k)))
            table.setItem(row, 10, QTableWidgetItem(str(p.five_k)))
            table.setItem(row, 11, QTableWidgetItem(str(p.damage)))

    # ─── Audio Extraction & Playback ──────────────────────────

    def _clear_audio_selection(self):
        self.player_audio_list.clear()
        self.voice_list.clear()
        self.saved_voice_list.clear()
        self.audio_entries.clear()
        self._current_player_audio = []

    def _extract_audio(self):
        if not self.demo_path:
            self._snackbar("No demo loaded", error=True)
            return

        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        output_dir = os.path.join(appdata, "Small-Demo-Manager", "Audio", self.demo_name)
        os.makedirs(output_dir, exist_ok=True)

        self.audio_progress.setVisible(True)
        self.audio_progress.setValue(0)
        self.extract_btn.setEnabled(False)
        self.player_audio_list.clear()
        self.voice_list.clear()

        self._audio_worker = AudioExtractWorker(self.demo_path, output_dir)
        self._audio_worker.progress.connect(lambda v: self.audio_progress.setValue(int(v)))
        self._audio_worker.finished.connect(self._on_extraction_done)
        self._audio_worker.error.connect(self._on_extraction_error)
        self._audio_worker.start()

    def _on_extraction_done(self, entries: dict[str, list[AudioEntry]]):
        self.audio_entries = entries
        self.audio_progress.setVisible(False)
        self.extract_btn.setEnabled(True)

        self.player_audio_list.clear()
        for player_name in sorted(entries.keys()):
            count = len(entries[player_name])
            self.player_audio_list.addItem(f"{player_name} ({count} files)")

        if entries:
            self.player_audio_list.setCurrentRow(0)

        self._refresh_saved_audio()
        self._snackbar("Audio extraction complete!")

    def _on_extraction_error(self, error_msg: str):
        self.audio_progress.setVisible(False)
        self.extract_btn.setEnabled(True)
        self._snackbar(f"Extraction error: {error_msg}", error=True)

    def _player_audio_context_menu(self, pos):
        if not self._current_player_audio:
            return
        menu = QMenu(self)
        menu.addAction("Save All Player Audio", lambda: self._save_all_player_audio())
        menu.exec(self.player_audio_list.viewport().mapToGlobal(pos))

    def _on_player_selected(self, row: int):
        if row < 0:
            return
        player_names = sorted(self.audio_entries.keys())
        if row >= len(player_names):
            return
        self._selected_player_name = player_names[row]
        self._current_player_audio = self.audio_entries[self._selected_player_name]
        self.voice_list.clear()
        has_files = len(self._current_player_audio) > 0
        self.save_all_btn.setEnabled(has_files)
        for entry in self._current_player_audio:
            self.voice_list.addItem(
                f"Round {entry.round} | {entry.time:.0f}s | {entry.duration:.1f}s"
            )

    def _play_selected_audio(self, item: QListWidgetItem):
        idx = self.voice_list.row(item)
        if 0 <= idx < len(self._current_player_audio):
            file_path = self._current_player_audio[idx].file_path
            try:
                audio_player.play_wav(file_path)
            except Exception as e:
                self._snackbar(f"Playback error: {e}", error=True)

    def _play_saved_audio(self, item: QListWidgetItem):
        idx = self.saved_voice_list.row(item)
        if 0 <= idx < len(afm.saved_audio_files.files):
            file_path = afm.saved_audio_files.files[idx].full_path
            try:
                audio_player.play_wav(file_path)
            except Exception as e:
                self._snackbar(f"Playback error: {e}", error=True)

    def _check_saved_path(self) -> bool:
        saved_path = read("SavedVoiceFilesPath", "")
        if not saved_path or not os.path.isdir(saved_path):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, tr("audio.saved_path.title"),
                tr("audio.saved_path.msg")
            )
            return False
        return True

    def _audio_context_menu(self, pos):
        item = self.voice_list.itemAt(pos)
        if not item:
            return
        idx = self.voice_list.row(item)
        if 0 <= idx < len(self._current_player_audio):
            file_path = self._current_player_audio[idx].file_path
            menu = QMenu(self)
            menu.addAction(tr("audio.save_one"), lambda: self._save_voice_file(file_path))
            menu.addAction(tr("audio.save_all"), lambda: self._save_all_player_audio())
            menu.exec(self.voice_list.viewport().mapToGlobal(pos))

    def _save_voice_file(self, source_path: str):
        if not self._check_saved_path():
            return
        try:
            afm.copy_to_saved(source_path)
            self._refresh_saved_audio()
            self._snackbar(tr("audio.saved_ok"))
        except Exception as e:
            self._snackbar(f"Save error: {e}", error=True)

    def _save_all_player_audio(self):
        if not self._current_player_audio:
            return
        if not self._check_saved_path():
            return
        saved = 0
        for entry in self._current_player_audio:
            try:
                afm.copy_to_saved(entry.file_path)
                saved += 1
            except Exception:
                continue
        self._refresh_saved_audio()
        msg = tr("audio.saved_count").replace("{count}", str(saved)).replace("{player}", self._selected_player_name)
        self._snackbar(msg)

    def _refresh_saved_audio(self):
        afm.refresh_saved_files()
        self.saved_voice_list.clear()
        for info in afm.saved_audio_files.files:
            self.saved_voice_list.addItem(
                f"[{info.folder_name}] {info.file_name}"
            )

    # ─── Move & Rename ────────────────────────────────────────

    def _move_to_cs2(self):
        if not self.demo_path or not os.path.isfile(self.demo_path):
            self._snackbar("No demo loaded", error=True)
            return

        cs2_path = read("CS2DemoPath", "")
        if not cs2_path or not os.path.isdir(cs2_path):
            cs2_path = QFileDialog.getExistingDirectory(self, "Select CS2 Demo Folder")
            if not cs2_path:
                return
            write("CS2DemoPath", cs2_path)

        from ui.custom_dialog import RenameDialog
        dialog = RenameDialog(self.demo_name, self)
        if dialog.exec() != RenameDialog.DialogCode.Accepted:
            return

        new_name_text = dialog.result_text
        combo_idx = dialog.result_combo_index
        write("DemoNameOption", str(combo_idx))

        ext = os.path.splitext(self.demo_path)[1]
        if combo_idx == 0:
            new_name = f"{new_name_text}_{self.demo_name}{ext}"
        elif combo_idx == 1:
            new_name = f"{new_name_text}{ext}"
        else:
            new_name = f"{self.demo_name}{ext}"

        target = os.path.join(cs2_path, new_name)
        if os.path.exists(target):
            reply = QMessageBox.question(
                self, "File Exists",
                f"Target file exists. Overwrite?\n{target}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            sha256_src = hashlib.sha256()
            with open(self.demo_path, "rb") as f:
                while chunk := f.read(65536):
                    sha256_src.update(chunk)
            src_hash = sha256_src.hexdigest()

            shutil.copy2(self.demo_path, target)

            sha256_dst = hashlib.sha256()
            with open(target, "rb") as f:
                while chunk := f.read(65536):
                    sha256_dst.update(chunk)
            dst_hash = sha256_dst.hexdigest()

            if src_hash != dst_hash:
                os.remove(target)
                QMessageBox.critical(self, "Error", "SHA256 mismatch! File corrupted.")
                return

            self._snackbar(f"Copied to: {target}")
        except Exception as e:
            self._snackbar(f"Error: {e}", error=True)

    # ─── Settings ──────────────────────────────────────────────

    def _browse_folder(self, target: str):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            if target == "cs2":
                self.cs2_path_input.setText(path)
                write("CS2DemoPath", path)
            else:
                self.saved_path_input.setText(path)
                write("SavedVoiceFilesPath", path)
            self._snackbar("Path saved!")

    def _toggle_shell(self, checked: bool):
        from shell_context import add_shell_context, remove_shell_context
        if checked:
            ok = add_shell_context()
            if ok:
                self._snackbar("Shell context menu added!")
            else:
                self._snackbar("Failed to add shell context", error=True)
        else:
            remove_shell_context()
            self._snackbar("Shell context menu removed.")

    # ─── Update Check ──────────────────────────────────────────

    def _fetch_patch_notes(self):
        def fetch():
            for attempt in range(3):
                try:
                    req = Request(PATCH_NOTES_URL, headers={"User-Agent": "Small-Demo-Manager"})
                    with urlopen(req, timeout=10) as resp:
                        text = resp.read().decode("utf-8")
                        if text.strip():
                            self.patch_notes_fetched.emit(text.strip())
                            return
                except Exception:
                    continue
        threading.Thread(target=fetch, daemon=True).start()

    def _on_patch_notes_fetched(self, text: str):
        if text and text != self.patch_notes.toPlainText():
            self.patch_notes.setPlainText(text)

    def _on_lang_btn_clicked(self, code: str):
        if code == self._tr.current_language:
            return
        for c, btn in self.lang_btns.items():
            btn.setChecked(c == code)
        self._tr.load(code)
        write("Language", code)

    def _animate_tab_fade(self, index: int):
        widget = self.tabs.widget(index)
        if not widget:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        self._tab_anim = QPropertyAnimation(effect, b"opacity")
        self._tab_anim.setDuration(150)
        self._tab_anim.setStartValue(0.6)
        self._tab_anim.setEndValue(1.0)
        self._tab_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._tab_anim.start()

    def _retranslate(self):
        self.setWindowTitle(tr("app.title"))
        tab_keys = [
            "tab.home", "tab.bitfield", "tab.match", "tab.audio",
            "tab.settings", "tab.about", "tab.howto",
        ]
        for i, key in enumerate(tab_keys):
            self.tabs.setTabText(i, tr(key))
        self._home_header.setText(tr("home.header"))
        self._welcome_card.content_layout.itemAt(0).widget().setText(tr("home.welcome.text"))
        self._welcome_card.setTitle(tr("home.welcome.title"))
        self.home_file_path.setPlaceholderText(tr("home.drop.placeholder"))
        self._load_btn.setText(tr("home.load.button"))
        self._patch_card.setTitle(tr("home.notes.title"))
        self._about_card.setTitle(tr("about.title"))
        self._about_lbl.setText(tr("about.description"))
        self._version_card.setTitle(tr("about.version.title"))
        self._author_lbl.setText(tr("about.author"))
        self._fork_lbl.setText(tr("about.fork"))
        self._support_card.setTitle(tr("about.support.title"))
        self.update_btn.setText(tr("about.update.button"))
        self._github_btn.setText(tr("about.github.button"))
        self._fork_btn.setText(tr("about.fork.button"))
        self._theme_card.setTitle(tr("settings.theme.title"))
        self._theme_label.setText(tr("settings.theme.dark"))
        self._path_card.setTitle(tr("settings.paths.title"))
        self._cs2_label.setText(tr("settings.paths.cs2"))
        self._cs2_browse.setText(tr("settings.paths.browse"))
        self._saved_label.setText(tr("settings.paths.saved"))
        self._saved_browse.setText(tr("settings.paths.browse"))
        self.bf_move_btn.setText(tr("bitfield.move.button"))
        self.bf_file_path.setPlaceholderText(tr("bitfield.drop.placeholder"))
        self.lbl_map.setText(tr("bitfield.map") + " -")
        self.lbl_duration.setText(tr("bitfield.duration") + " -")
        self.lbl_team_a.setText(tr("bitfield.team_a"))
        self.lbl_team_b.setText(tr("bitfield.team_b"))
        self._cmd_label.setText(tr("bitfield.command.label"))
        self._copy_btn.setText(tr("bitfield.copy.button"))
        self.extract_btn.setText(tr("audio.extract.button"))
        self.save_all_btn.setText(tr("audio.save_all.button"))
        self._players_label.setText(tr("audio.players.label"))
        self._voices_label.setText(tr("audio.voices.label"))
        self._saved_label2.setText(tr("audio.saved.label"))

    def _check_for_updates(self):
        def check():
            try:
                req = urllib.request.Request(
                    GITHUB_REPO,
                    headers={"User-Agent": "Small-Demo-Manager"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    latest = data[0]["tag_name"] if isinstance(data, list) else data["tag_name"]
                    latest_ver = re.sub(r"[^\d.]", "", latest)
                    current_ver = CURRENT_VERSION
                    if self._compare_versions(latest_ver, current_ver) > 0:
                        self.update_available.emit(f"Update available: {latest}")
            except Exception:
                pass

        threading.Thread(target=check, daemon=True).start()

    def _manual_update_check(self):
        self._snackbar("Checking for updates...")
        self._check_for_updates()

    def _compare_versions(self, a: str, b: str) -> int:
        a_parts = [int(x) for x in a.split(".")]
        b_parts = [int(x) for x in b.split(".")]
        while len(a_parts) < len(b_parts):
            a_parts.append(0)
        while len(b_parts) < len(a_parts):
            b_parts.append(0)
        for i in range(len(a_parts)):
            if a_parts[i] > b_parts[i]:
                return 1
            elif a_parts[i] < b_parts[i]:
                return -1
        return 0

    # ─── Window Close ─────────────────────────────────────────

    def closeEvent(self, event):
        audio_player.stop()
        super().closeEvent(event)
