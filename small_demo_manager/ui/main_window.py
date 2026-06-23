import os
import re
import hashlib
import shutil
import webbrowser
import urllib.request
import json
import threading
from typing import Optional
from urllib.request import urlopen, Request

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QProgressBar, QFileDialog, QMessageBox, QMenu, QSizePolicy,
    QFrame, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QBrush, QDragEnterEvent, QDropEvent

from qt_material import apply_stylesheet

from models import PlayerSnapshot, MatchResult, AudioEntry
from demo_parser import CS2DemoParser
from audio_extractor import extract_voice
import audio_player
import audio_file_manager as afm
from config import read, write, key_exists
from ui.widgets import Card, IconButton, SectionHeader, ClickableLabel


GITHUB_REPO = "https://api.github.com/repos/pythaeusone/Faceit-Demo-Voice-Calculator/releases"
PATCH_NOTES_URL = "https://raw.githubusercontent.com/hiez1337/Small-Demo-Manager/main/PATCH_NOTES.md"
CURRENT_VERSION = "1.0.8"


class ParseWorker(QThread):
    finished = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            parser = CS2DemoParser(self.file_path)
            snapshots, match_result = parser.parse()
            self.finished.emit(snapshots, match_result)
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
        self._parse_worker: Optional[ParseWorker] = None
        self._audio_worker: Optional[AudioExtractWorker] = None

        self.setWindowTitle("Small Demo Manager")
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
        main_layout.addWidget(self.tabs)

        self.tab_home = self._create_home_tab()
        self.tab_bitfield = self._create_bitfield_tab()
        self.tab_match = self._create_match_tab()
        self.tab_audio = self._create_audio_tab()
        self.tab_settings = self._create_settings_tab()
        self.tab_about = self._create_about_tab()
        self.tab_howto = self._create_howto_tab()

        self.tabs.addTab(self.tab_home, "Home")
        self.tabs.addTab(self.tab_bitfield, "Bitfield-Calc")
        self.tabs.addTab(self.tab_match, "Match-Results")
        self.tabs.addTab(self.tab_audio, "Audio-Player")
        self.tabs.addTab(self.tab_settings, "Settings")
        self.tabs.addTab(self.tab_about, "About")
        self.tabs.addTab(self.tab_howto, "HowTo")

    def apply_theme(self):
        theme = "dark_teal.xml" if self._is_dark else "light_teal.xml"
        apply_stylesheet(self._app_ref, theme=theme)
        self._app_ref.setStyleSheet(self._app_ref.styleSheet())

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

        header = SectionHeader("Small Demo Manager")
        header.setObjectName("homeHeader")
        layout.addWidget(header)

        welcome_card = Card("Welcome")
        welcome_lbl = QLabel(
            "Analyze Counter-Strike 2 demo files (.dem) — extract match statistics, "
            "voice audio, calculate bitfield masks, and more.\n\n"
            "Drag & drop a .dem file onto the file path field below to get started."
        )
        welcome_lbl.setWordWrap(True)
        welcome_card.add_widget(welcome_lbl)
        layout.addWidget(welcome_card)

        drop_layout = QHBoxLayout()
        self.home_file_path = QLineEdit()
        self.home_file_path.setReadOnly(True)
        self.home_file_path.setPlaceholderText("Drop .dem file here...")
        self.home_file_path.setObjectName("dropField")
        self.home_file_path.dragEnterEvent = self._drag_enter
        self.home_file_path.dragMoveEvent = self._drag_move
        self.home_file_path.dropEvent = self._drop
        drop_layout.addWidget(self.home_file_path)

        load_btn = QPushButton("Load Demo")
        load_btn.setObjectName("primaryButton")
        load_btn.clicked.connect(lambda: self._open_file_dialog())
        drop_layout.addWidget(load_btn)
        layout.addLayout(drop_layout)

        patch_card = Card("Patch Notes")
        self.patch_notes = QTextEdit()
        self.patch_notes.setReadOnly(True)
        self.patch_notes.setMaximumHeight(200)
        self.patch_notes.setObjectName("patchNotes")
        self.patch_notes.setPlainText("Loading patch notes...")
        patch_card.add_widget(self.patch_notes)
        layout.addWidget(patch_card)
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
        self.bf_file_path.setPlaceholderText("Drop .dem file here...")
        self.bf_file_path.setObjectName("dropField")
        self.bf_file_path.dragEnterEvent = self._drag_enter
        self.bf_file_path.dragMoveEvent = self._drag_move
        self.bf_file_path.dropEvent = self._drop
        drop_layout.addWidget(self.bf_file_path)

        self.bf_move_btn = QPushButton("Move to CS2")
        self.bf_move_btn.clicked.connect(self._move_to_cs2)
        drop_layout.addWidget(self.bf_move_btn)
        layout.addLayout(drop_layout)

        info_layout = QHBoxLayout()
        self.lbl_map = QLabel("Map: -")
        self.lbl_duration = QLabel("Duration: -")
        self.lbl_vs = QLabel("VS")
        info_layout.addWidget(self.lbl_map)
        info_layout.addWidget(self.lbl_duration)
        info_layout.addStretch()
        self.lbl_team_a = QLabel("Team A")
        self.lbl_team_b = QLabel("Team B")
        info_layout.addWidget(self.lbl_team_a, alignment=Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.lbl_vs)
        info_layout.addWidget(self.lbl_team_b)
        layout.addLayout(info_layout)

        teams_layout = QHBoxLayout()
        self.team_a_list = QListWidget()
        self.team_a_list.setObjectName("teamList")
        self.team_b_list = QListWidget()
        self.team_b_list.setObjectName("teamList")
        teams_layout.addWidget(self.team_a_list)
        teams_layout.addWidget(self.team_b_list)
        layout.addLayout(teams_layout, stretch=1)

        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(QLabel("Command:"))
        self.tb_command = QLineEdit()
        self.tb_command.setReadOnly(True)
        self.tb_command.setObjectName("commandField")
        cmd_layout.addWidget(self.tb_command)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("primaryButton")
        copy_btn.clicked.connect(self._copy_command)
        cmd_layout.addWidget(copy_btn)
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
        self.extract_btn = QPushButton("Extract Audio")
        self.extract_btn.setObjectName("primaryButton")
        self.extract_btn.clicked.connect(self._extract_audio)
        self.extract_btn.setEnabled(False)
        btn_layout.addWidget(self.extract_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.audio_progress = QProgressBar()
        self.audio_progress.setObjectName("audioProgress")
        self.audio_progress.setVisible(False)
        layout.addWidget(self.audio_progress)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(8)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Players"))
        self.player_audio_list = QListWidget()
        self.player_audio_list.setObjectName("audioList")
        self.player_audio_list.currentRowChanged.connect(self._on_player_selected)
        left_layout.addWidget(self.player_audio_list)
        lists_layout.addLayout(left_layout)

        mid_layout = QVBoxLayout()
        mid_layout.addWidget(QLabel("Voice Files"))
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
        right_layout.addWidget(QLabel("Saved Voice Files"))
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

        theme_card = Card("Theme")
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Dark Mode"))
        self.theme_switch = QCheckBox()
        self.theme_switch.setChecked(self._is_dark)
        self.theme_switch.toggled.connect(lambda: self.toggle_theme())
        theme_row.addWidget(self.theme_switch)
        theme_row.addStretch()
        theme_card.add_layout(theme_row)
        layout.addWidget(theme_card)

        path_card = Card("Paths")
        cs2_row = QHBoxLayout()
        cs2_row.addWidget(QLabel("CS2 Demo Folder:"))
        self.cs2_path_input = QLineEdit()
        self.cs2_path_input.setText(read("CS2DemoPath", ""))
        cs2_row.addWidget(self.cs2_path_input)
        cs2_browse = QPushButton("Browse")
        cs2_browse.clicked.connect(lambda: self._browse_folder("cs2"))
        cs2_row.addWidget(cs2_browse)
        path_card.add_layout(cs2_row)

        saved_row = QHBoxLayout()
        saved_row.addWidget(QLabel("Saved Voice Folder:"))
        self.saved_path_input = QLineEdit()
        self.saved_path_input.setText(read("SavedVoiceFilesPath", ""))
        saved_row.addWidget(self.saved_path_input)
        saved_browse = QPushButton("Browse")
        saved_browse.clicked.connect(lambda: self._browse_folder("saved"))
        saved_row.addWidget(saved_browse)
        path_card.add_layout(saved_row)
        layout.addWidget(path_card)

        shell_card = Card("Shell Integration")
        shell_row = QHBoxLayout()
        self.shell_checkbox = QCheckBox("Add .dem context menu entry")
        from shell_context import validate_shell_integration
        self.shell_checkbox.setChecked(validate_shell_integration())
        self.shell_checkbox.toggled.connect(self._toggle_shell)
        shell_row.addWidget(self.shell_checkbox)
        shell_row.addStretch()
        shell_card.add_layout(shell_row)
        layout.addWidget(shell_card)

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
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        about_card = Card("About")
        about_lbl = QLabel(
            "Small Demo Manager — a tool for analyzing Counter-Strike 2 demo files.\n\n"
            "Originally developed for the CS2 community to simplify demo analysis,\n"
            "voice extraction, and spectator bitfield calculation."
        )
        about_lbl.setWordWrap(True)
        about_card.add_widget(about_lbl)
        layout.addWidget(about_card)

        version_card = Card("Version")
        version_lbl = QLabel(f"v{CURRENT_VERSION} (Python port)")
        version_card.add_widget(version_lbl)
        layout.addWidget(version_card)

        support_card = Card("Support")
        support_layout = QVBoxLayout()
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.clicked.connect(self._manual_update_check)
        support_card.add_widget(self.update_btn)

        github_btn = QPushButton("GitHub Repository")
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/pythaeusone/Faceit-Demo-Voice-Calculator")
        )
        support_card.add_widget(github_btn)
        layout.addWidget(support_card)

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

        sections = [
            ("Bitfield-Calc", "Drop a .dem file, select players from the lists, "
             "copy the generated console command, paste it in CS2 to hear selected players."),
            ("Match-Results", "After loading a demo, switch to this tab to see "
             "detailed match statistics for all players."),
            ("Audio-Player", "Click Extract Audio to extract voice data from the demo. "
             "Files are organized by player. Double-click to play. Right-click to save."),
            ("Settings", "Configure dark/light theme, set CS2 demo path, "
             "manage saved voice files location, and register shell context menu."),
        ]

        for title, text in sections:
            card = Card(title)
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            card.add_widget(lbl)
            layout.addWidget(card)

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

    def _on_demo_parsed(self, snapshots: list[PlayerSnapshot], match_result: MatchResult):
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

        src_server = os.path.basename(self.demo_path).lower().find("sourcetv")
        if src_server < 0:
            self._snackbar("Demo loaded. Voice extraction may be limited (not SourceTV).")
        else:
            self._snackbar("Demo loaded successfully!")

    def _on_demo_error(self, error_msg: str):
        self.bf_progress.setVisible(False)
        self._snackbar(f"Error: {error_msg}", error=True)

    # ─── Bitfield ──────────────────────────────────────────────

    def _load_bitfield(self):
        self.team_a_list.clear()
        self.team_b_list.clear()

        spec_id = 1
        for snap in self.snapshots:
            if snap.team_number == 3:
                item = QListWidgetItem(f"{snap.player_name} (ID: {spec_id})")
                item.setData(Qt.ItemDataRole.UserRole, snap.steam_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, spec_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.team_a_list.addItem(item)
                spec_id += 1

        for snap in self.snapshots:
            if snap.team_number == 2:
                item = QListWidgetItem(f"{snap.player_name} (ID: {spec_id})")
                item.setData(Qt.ItemDataRole.UserRole, snap.steam_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, spec_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.team_b_list.addItem(item)
                spec_id += 1

        self.team_a_list.itemChanged.connect(self._update_bitfield)
        self.team_b_list.itemChanged.connect(self._update_bitfield)

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
        self._audio_worker.progress.connect(self.audio_progress.setValue)
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

    def _on_player_selected(self, row: int):
        if row < 0:
            return
        player_names = sorted(self.audio_entries.keys())
        if row >= len(player_names):
            return
        name = player_names[row]
        self._current_player_audio = self.audio_entries[name]
        self.voice_list.clear()
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

    def _audio_context_menu(self, pos):
        item = self.voice_list.itemAt(pos)
        if not item:
            return
        idx = self.voice_list.row(item)
        if 0 <= idx < len(self._current_player_audio):
            file_path = self._current_player_audio[idx].file_path
            menu = QMenu(self)
            menu.addAction("Save to Voice Files", lambda: self._save_voice_file(file_path))
            menu.exec(self.voice_list.viewport().mapToGlobal(pos))

    def _save_voice_file(self, source_path: str):
        try:
            afm.copy_to_saved(source_path)
            self._refresh_saved_audio()
            self._snackbar("Saved!")
        except Exception as e:
            self._snackbar(f"Save error: {e}", error=True)

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
            try:
                req = Request(PATCH_NOTES_URL, headers={"User-Agent": "Small-Demo-Manager"})
                with urlopen(req, timeout=10) as resp:
                    text = resp.read().decode("utf-8")
                    self.patch_notes.setPlainText(text.strip())
            except Exception:
                self.patch_notes.setPlainText("v1.0.8\n- Initial Python port\n- Full Material Design 3 UI\n- CS2 demo parsing with demoparser2\n- Opus voice extraction\n- Audio playback\n- Bitfield calculator\n- Match results")
        threading.Thread(target=fetch, daemon=True).start()

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
                        self._snackbar(f"Update available: {latest}")
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
