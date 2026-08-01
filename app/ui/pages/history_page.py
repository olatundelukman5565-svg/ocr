"""OCR History: search (text / regex / case-sensitive / whole-word) over
every past run, filter by engine, and open past outputs.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import OCR_ENGINES
from app.database.db_manager import DBManager

logger = logging.getLogger(__name__)

_COLUMNS = ["File", "Date", "Engine", "Language", "Confidence", "Time (s)", "Output"]


class HistoryPage(QWidget):
    def __init__(self, db: DBManager, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self._records = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("OCR History")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search extracted text or file name…")
        self.search_input.returnPressed.connect(self.refresh)
        search_row.addWidget(self.search_input, stretch=1)

        self.regex_checkbox = QCheckBox("Regex")
        self.case_checkbox = QCheckBox("Case sensitive")
        self.whole_word_checkbox = QCheckBox("Whole word")
        search_row.addWidget(self.regex_checkbox)
        search_row.addWidget(self.case_checkbox)
        search_row.addWidget(self.whole_word_checkbox)

        self.engine_filter = QComboBox()
        self.engine_filter.addItem("All engines", None)
        for engine in OCR_ENGINES:
            self.engine_filter.addItem(engine, engine)
        search_row.addWidget(self.engine_filter)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.refresh)
        search_row.addWidget(search_btn)
        root.addLayout(search_row)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._open_output)
        root.addWidget(self.table, stretch=1)

        bottom_row = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(self._delete_selected)
        bottom_row.addWidget(delete_btn)
        bottom_row.addStretch(1)
        root.addLayout(bottom_row)

    def refresh(self) -> None:
        self._records = self.db.search(
            query=self.search_input.text().strip(),
            use_regex=self.regex_checkbox.isChecked(),
            case_sensitive=self.case_checkbox.isChecked(),
            whole_word=self.whole_word_checkbox.isChecked(),
            engine=self.engine_filter.currentData(),
        )
        self.table.setRowCount(len(self._records))
        for row, record in enumerate(self._records):
            self.table.setItem(row, 0, QTableWidgetItem(record.file_name))
            self.table.setItem(row, 1, QTableWidgetItem(record.date))
            self.table.setItem(row, 2, QTableWidgetItem(record.engine))
            self.table.setItem(row, 3, QTableWidgetItem(record.language or ""))
            self.table.setItem(row, 4, QTableWidgetItem(f"{record.confidence:.1f}%"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.processing_time:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(record.output_path or "(not exported)"))

    def _open_output(self, row: int, _column: int) -> None:
        record = self._records[row]
        if not record.output_path or not Path(record.output_path).exists():
            QMessageBox.information(self, "No output", "This record has no exported output file.")
            return
        path = record.output_path
        try:
            if sys.platform.startswith("darwin"):
                subprocess.run(["open", path], check=False)
            elif sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.run(["xdg-open", path], check=False)
        except OSError:
            logger.exception("Could not open output file %s", path)

    def _delete_selected(self) -> None:
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            record = self._records[row]
            if record.id is not None:
                self.db.delete_record(record.id)
        self.refresh()
