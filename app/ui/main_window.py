"""Main application window: sidebar navigation, stacked dashboard pages,
status bar with progress reporting, and dark/light theme switching.
"""
from __future__ import annotations

import logging

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import APP_NAME, APP_VERSION
from app.config.settings import SettingsManager
from app.database.db_manager import DBManager
from app.ui.pages.batch_page import BatchPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.home_page import HomePage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.workspace_page import WorkspacePage
from app.ui.theme import stylesheet_for

logger = logging.getLogger(__name__)

_NAV_ITEMS = [
    ("home", "Home"),
    ("workspace", "OCR Workspace"),
    ("batch", "Batch Processing"),
    ("history", "History"),
    ("settings", "Settings"),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsManager()
        self.db = DBManager()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1440, 900)

        self._build_pages()
        self._build_layout()
        self._build_menu()
        self._build_status_bar()
        self.apply_theme(self.settings.get("theme", "dark"))
        self._navigate("home")

    # -- construction ------------------------------------------------------------------
    def _build_pages(self) -> None:
        self.home_page = HomePage(self.db)
        self.workspace_page = WorkspacePage(self.settings, self.db)
        self.batch_page = BatchPage(self.settings, self.db)
        self.history_page = HistoryPage(self.db)
        self.settings_page = SettingsPage(self.settings)

        self.home_page.navigate_requested.connect(self._navigate)
        self.home_page.open_files_requested.connect(self._open_files_in_workspace)
        self.settings_page.theme_changed.connect(self.apply_theme)

        for page in (self.workspace_page, self.batch_page):
            page.status_message.connect(self._show_status)

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        body = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        outer_layout.addWidget(body)

        # -- sidebar --------------------------------------------------------------------
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        from PySide6.QtWidgets import QLabel

        brand = QLabel(APP_NAME)
        brand.setObjectName("SectionTitle")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addSpacing(16)

        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label in _NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, k=key: self._navigate(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        sidebar_layout.addStretch(1)

        self.theme_toggle_btn = QPushButton("Toggle Theme")
        self.theme_toggle_btn.setObjectName("SecondaryButton")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        sidebar_layout.addWidget(self.theme_toggle_btn)

        body_layout.addWidget(sidebar)

        # -- page stack -------------------------------------------------------------------
        self.stack = QStackedWidget()
        self.page_index = {}
        for key, page in (
            ("home", self.home_page),
            ("workspace", self.workspace_page),
            ("batch", self.batch_page),
            ("history", self.history_page),
            ("settings", self.settings_page),
        ):
            index = self.stack.addWidget(page)
            self.page_index[key] = index
        self.stack.setContentsMargins(24, 24, 24, 24)
        body_layout.addWidget(self.stack, stretch=1)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("Open File…", self)
        open_action.setShortcut(QKeySequence(self.settings.get("hotkeys", {}).get("open_file", "Ctrl+O")))
        open_action.triggered.connect(self._open_file_dialog)
        file_menu.addAction(open_action)

        open_folder_action = QAction("Open Folder…", self)
        open_folder_action.setShortcut(
            QKeySequence(self.settings.get("hotkeys", {}).get("open_folder", "Ctrl+Shift+O"))
        )
        open_folder_action.triggered.connect(self._open_folder_dialog)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")
        run_ocr_action = QAction("Run OCR", self)
        run_ocr_action.setShortcut(QKeySequence(self.settings.get("hotkeys", {}).get("run_ocr", "Ctrl+R")))
        run_ocr_action.triggered.connect(self.workspace_page.run_ocr)
        edit_menu.addAction(run_ocr_action)

        view_menu = menu_bar.addMenu("&View")
        for key, label in _NAV_ITEMS:
            action = QAction(label, self)
            action.triggered.connect(lambda _checked=False, k=key: self._navigate(k))
            view_menu.addAction(action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    # -- navigation --------------------------------------------------------------------
    def _navigate(self, key: str) -> None:
        self.stack.setCurrentIndex(self.page_index[key])
        for nav_key, btn in self.nav_buttons.items():
            btn.setChecked(nav_key == key)
        if key == "home":
            self.home_page.refresh()
        if key == "history":
            self.history_page.refresh()

    def _open_files_in_workspace(self, paths: list[str]) -> None:
        self.workspace_page.load_files(paths)
        self._navigate("workspace")

    def _open_file_dialog(self) -> None:
        from app.config.constants import SUPPORTED_INPUT_EXTENSIONS

        patterns = " ".join(f"*{ext}" for ext in SUPPORTED_INPUT_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(self, "Open file", "", f"Supported files ({patterns})")
        if files:
            self._open_files_in_workspace(files)

    def _open_folder_dialog(self) -> None:
        from app.utils.file_utils import iter_supported_files

        folder = QFileDialog.getExistingDirectory(self, "Open folder")
        if folder:
            files = [str(p) for p in iter_supported_files(folder)]
            if files:
                self._open_files_in_workspace(files)

    # -- theme -------------------------------------------------------------------------
    def apply_theme(self, theme: str) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.instance().setStyleSheet(stylesheet_for(theme))
        self.settings.set("theme", theme)

    def _toggle_theme(self) -> None:
        current = self.settings.get("theme", "dark")
        self.apply_theme("light" if current == "dark" else "dark")

    # -- misc ------------------------------------------------------------------------------
    def _show_status(self, message: str) -> None:
        self.status_bar.showMessage(message, 8000)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Offline, multi-engine OCR for images and scanned PDFs.\n"
            "All processing happens locally — nothing is uploaded.",
        )

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override
        self.settings.save()
        super().closeEvent(event)
