"""Batch Processing: queue hundreds of files, run in the background with
pause/resume/cancel, and auto-export + log each result to history.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.constants import AUTO_DETECT_LANGUAGE, OCR_MODES, SUPPORTED_LANGUAGES
from app.config.settings import SettingsManager
from app.core.batch_manager import BatchManager
from app.core.models import ExportFormat, HistoryRecord, JobStatus
from app.database.db_manager import DBManager
from app.exports.exporter import export_document, extension_for
from app.ocr.engine_manager import get_engine_manager
from app.ui.widgets.drop_area import DropArea
from app.utils.file_utils import unique_output_path

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    JobStatus.QUEUED: "Queued",
    JobStatus.PROCESSING: "Processing…",
    JobStatus.DONE: "Done",
    JobStatus.FAILED: "Failed",
    JobStatus.CANCELLED: "Cancelled",
    JobStatus.PAUSED: "Paused",
}

_COLUMNS = ["File", "Status", "Progress", "Confidence", "Time (s)"]


class BatchPage(QWidget):
    status_message = Signal(str)

    def __init__(self, settings: SettingsManager, db: DBManager, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.db = db
        self.engine_manager = get_engine_manager()
        self.batch_manager = BatchManager()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("Batch Processing")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        self.drop_area = DropArea("Drag & drop hundreds of files or a whole folder here")
        self.drop_area.setMaximumHeight(110)
        self.drop_area.files_dropped.connect(self._add_files)
        root.addWidget(self.drop_area)

        controls = QHBoxLayout()
        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setObjectName("SecondaryButton")
        add_folder_btn.clicked.connect(self._add_folder)
        controls.addWidget(add_folder_btn)

        controls.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        for engine in self.engine_manager.list_engines():
            suffix = "" if engine.is_available() else " (not installed)"
            self.engine_combo.addItem(f"{engine.display_name}{suffix}", engine.name)
        controls.addWidget(self.engine_combo)

        controls.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("Auto-detect", AUTO_DETECT_LANGUAGE)
        for name, code in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(name, code)
        controls.addWidget(self.language_combo)

        controls.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        for mode in OCR_MODES:
            self.mode_combo.addItem(mode.replace("_", " ").title(), mode)
        controls.addWidget(self.mode_combo)

        controls.addWidget(QLabel("Export as:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([f.value for f in ExportFormat])
        controls.addWidget(self.export_format_combo)
        controls.addStretch(1)
        root.addLayout(controls)

        buttons = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_batch)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("SecondaryButton")
        self.pause_btn.clicked.connect(self._pause_or_resume)
        self.pause_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DangerButton")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        clear_btn = QPushButton("Clear Queue")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self._clear_queue)
        for b in (self.start_btn, self.pause_btn, self.cancel_btn, clear_btn):
            buttons.addWidget(b)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.overall_progress = QProgressBar()
        self.eta_label = QLabel("")
        self.eta_label.setObjectName("Muted")
        root.addWidget(self.overall_progress)
        root.addWidget(self.eta_label)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.table, stretch=1)

        self._is_paused = False

    # -- queue management ----------------------------------------------------------------
    def _add_files(self, paths: list[str]) -> None:
        self.batch_manager.add_files(paths)
        self._refresh_table()
        self.status_message.emit(f"Added {len(paths)} file(s) to the batch queue.")

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if folder:
            from app.utils.file_utils import iter_supported_files

            files = [str(p) for p in iter_supported_files(folder)]
            self._add_files(files)

    def _clear_queue(self) -> None:
        self.batch_manager.clear()
        self._refresh_table()

    def _refresh_table(self) -> None:
        self.table.setRowCount(len(self.batch_manager.items))
        for row, item in enumerate(self.batch_manager.items):
            self.table.setItem(row, 0, QTableWidgetItem(Path(item.path).name))
            self.table.setItem(row, 1, QTableWidgetItem(_STATUS_LABELS.get(item.status, item.status.value)))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item.progress}%"))
            conf = f"{item.result.mean_confidence:.1f}%" if item.result else ""
            self.table.setItem(row, 3, QTableWidgetItem(conf))
            duration = f"{(item.finished_at - item.started_at):.2f}" if item.started_at and item.finished_at else ""
            self.table.setItem(row, 4, QTableWidgetItem(duration))

    # -- running --------------------------------------------------------------------------
    def start_batch(self) -> None:
        if not self.batch_manager.items:
            self.status_message.emit("Queue is empty — add files first.")
            return

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self._is_paused = False
        self.pause_btn.setText("Pause")

        worker = self.batch_manager.start(
            engine_name=self.engine_combo.currentData(),
            language=self.language_combo.currentData(),
            mode=self.mode_combo.currentData(),
            use_gpu=bool(self.settings.get("use_gpu", False)),
            confidence_threshold=float(self.settings.get("confidence_threshold", 0)),
        )
        worker.item_started.connect(self._on_item_started)
        worker.item_progress.connect(self._on_item_progress)
        worker.item_finished.connect(self._on_item_finished)
        worker.item_failed.connect(self._on_item_failed)
        worker.batch_progress.connect(self._on_batch_progress)
        worker.batch_finished.connect(self._on_batch_finished)

    def _pause_or_resume(self) -> None:
        if self._is_paused:
            self.batch_manager.resume()
            self.pause_btn.setText("Pause")
        else:
            self.batch_manager.pause()
            self.pause_btn.setText("Resume")
        self._is_paused = not self._is_paused

    def _cancel(self) -> None:
        self.batch_manager.cancel()
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)

    def _on_item_started(self, index: int, path: str) -> None:
        self._refresh_table()
        self.status_message.emit(f"Processing {Path(path).name}…")

    def _on_item_progress(self, index: int, current_page: int, total_pages: int) -> None:
        item = self.batch_manager.items[index]
        item.progress = int((current_page / total_pages) * 100) if total_pages else 0
        self._refresh_table()

    def _on_item_finished(self, index: int, document) -> None:
        item = self.batch_manager.items[index]
        item.progress = 100
        output_path = ""
        try:
            fmt = ExportFormat(self.export_format_combo.currentText())
            default_dir = self.settings.get("default_export_folder")
            base_name = Path(item.path).stem
            out_path = unique_output_path(default_dir, base_name, extension_for(fmt))
            export_document(document, fmt, out_path)
            output_path = str(out_path)
        except Exception:  # noqa: BLE001 - export failures shouldn't stop the batch
            logger.exception("Auto-export failed for %s", item.path)

        self.db.insert_record(
            HistoryRecord(
                id=None,
                file_name=Path(document.source_path).name,
                file_path=document.source_path,
                date=DBManager.now_str(),
                engine=document.engine,
                language=document.detected_language or document.language,
                confidence=document.mean_confidence,
                processing_time=document.processing_time_seconds,
                output_path=output_path,
                status="done",
                page_count=document.page_count,
            ),
            extracted_text=document.full_text,
        )
        self._refresh_table()

    def _on_item_failed(self, index: int, message: str) -> None:
        self._refresh_table()
        self.status_message.emit(f"Item {index + 1} failed: {message}")

    def _on_batch_progress(self, completed: int, total: int, eta_seconds: float) -> None:
        self.overall_progress.setMaximum(total)
        self.overall_progress.setValue(completed)
        minutes, seconds = divmod(int(eta_seconds), 60)
        self.eta_label.setText(f"{completed}/{total} complete — ETA {minutes}m {seconds}s")

    def _on_batch_finished(self) -> None:
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.status_message.emit("Batch processing complete.")
