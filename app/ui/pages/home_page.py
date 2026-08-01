"""Home dashboard: OCR statistics, recent files, quick actions."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.db_manager import DBManager
from app.ui.widgets.drop_area import DropArea


def _stat_card(title: str, value: str) -> QFrame:
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    value_label = QLabel(value)
    value_label.setObjectName("StatValue")
    title_label = QLabel(title)
    title_label.setObjectName("Muted")
    layout.addWidget(value_label)
    layout.addWidget(title_label)
    return card


class HomePage(QWidget):
    """Dashboard landing page. Emits signals the MainWindow wires to
    navigation / file loading so this page stays decoupled from routing.
    """

    open_files_requested = Signal(list)
    navigate_requested = Signal(str)  # page key: "workspace" | "batch" | "settings" | "history"

    def __init__(self, db: DBManager, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("Welcome to ImageOCR Pro")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # -- quick actions -----------------------------------------------------
        actions_row = QHBoxLayout()
        new_ocr_btn = QPushButton("New OCR")
        new_ocr_btn.clicked.connect(lambda: self.navigate_requested.emit("workspace"))
        batch_btn = QPushButton("Batch Processing")
        batch_btn.setObjectName("SecondaryButton")
        batch_btn.clicked.connect(lambda: self.navigate_requested.emit("batch"))
        history_btn = QPushButton("View History")
        history_btn.setObjectName("SecondaryButton")
        history_btn.clicked.connect(lambda: self.navigate_requested.emit("history"))
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SecondaryButton")
        settings_btn.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        for btn in (new_ocr_btn, batch_btn, history_btn, settings_btn):
            actions_row.addWidget(btn)
        layout.addLayout(actions_row)

        # -- drop area -----------------------------------------------------------
        self.drop_area = DropArea("Drag & drop images or PDFs to start a new OCR job")
        self.drop_area.files_dropped.connect(self.open_files_requested.emit)
        layout.addWidget(self.drop_area)

        # -- stat cards ------------------------------------------------------------
        self.stats_row = QHBoxLayout()
        layout.addLayout(self.stats_row)

        # -- recent files -----------------------------------------------------------
        recent_label = QLabel("Recent Files")
        recent_label.setObjectName("SectionTitle")
        layout.addWidget(recent_label)
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        layout.addWidget(self.recent_list, stretch=1)

    def _on_recent_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_files_requested.emit([path])
            self.navigate_requested.emit("workspace")

    def refresh(self) -> None:
        # rebuild stat cards
        while self.stats_row.count():
            child = self.stats_row.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        stats = self.db.get_statistics()
        self.stats_row.addWidget(_stat_card("Files Processed", str(stats["total_processed"])))
        self.stats_row.addWidget(_stat_card("Avg. Confidence", f"{stats['average_confidence']}%"))
        self.stats_row.addWidget(_stat_card("Pages OCR'd", str(stats["total_pages"])))
        self.stats_row.addWidget(_stat_card("Avg. Time/File", f"{stats['average_processing_time']}s"))

        self.recent_list.clear()
        for record in self.db.get_recent(limit=15):
            item = QListWidgetItem(f"{record.file_name}  —  {record.date}  —  {record.engine} ({record.confidence:.0f}%)")
            item.setData(Qt.ItemDataRole.UserRole, record.file_path)
            self.recent_list.addItem(item)
