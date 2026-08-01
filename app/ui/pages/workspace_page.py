"""OCR Workspace: image preview (zoom/rotate/crop/region-select), OCR
settings, run-OCR, editable results with find & replace / spell check,
and export.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from app.config.constants import AUTO_DETECT_LANGUAGE, EXPORT_FORMATS, OCR_MODES, SUPPORTED_LANGUAGES
from app.config.settings import SettingsManager
from app.core.document_processor import DocumentProcessor, DocumentProcessingError
from app.core.models import ExportFormat, HistoryRecord, OCRDocument
from app.core.text_postprocessor import spellcheck_text
from app.database.db_manager import DBManager
from app.exports.exporter import export_document, extension_for
from app.ocr.engine_manager import get_engine_manager
from app.ui.widgets.drop_area import DropArea
from app.ui.widgets.image_viewer import ImageViewer
from app.ui.widgets.thumbnail_list import ThumbnailList
from app.utils.file_utils import unique_output_path

logger = logging.getLogger(__name__)


class OCRRunThread(QThread):
    """Runs :class:`DocumentProcessor` for one file off the UI thread."""

    progress = Signal(int, int)
    finished_ok = Signal(object)  # OCRDocument
    failed = Signal(str)

    def __init__(self, path: str, engine: str, language: str, mode: str, use_gpu: bool, confidence: float, parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self.engine = engine
        self.language = language
        self.mode = mode
        self.use_gpu = use_gpu
        self.confidence = confidence
        self._processor = DocumentProcessor()

    def run(self) -> None:  # noqa: D102
        try:
            document = self._processor.process(
                self.path,
                engine_name=self.engine,
                language=self.language,
                mode=self.mode,
                use_gpu=self.use_gpu,
                confidence_threshold=self.confidence,
                progress_callback=lambda cur, total: self.progress.emit(cur, total),
            )
            self.finished_ok.emit(document)
        except DocumentProcessingError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, never crashes the UI
            logger.exception("OCR run failed")
            self.failed.emit(str(exc))


class WorkspacePage(QWidget):
    status_message = Signal(str)

    def __init__(self, settings: SettingsManager, db: DBManager, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.db = db
        self.engine_manager = get_engine_manager()

        self.loaded_pages: list = []
        self.current_document: OCRDocument | None = None
        self.current_path: str | None = None
        self._thread: OCRRunThread | None = None

        self._build_ui()

    # -- layout -------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("OCR Workspace")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, stretch=1)

        # -- left: thumbnails + drop area --------------------------------------------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.drop_area = DropArea("Drop images / PDFs")
        self.drop_area.setMaximumHeight(100)
        self.drop_area.files_dropped.connect(self.load_files)
        left_layout.addWidget(self.drop_area)
        self.thumbnails = ThumbnailList()
        self.thumbnails.page_selected.connect(self._on_page_selected)
        left_layout.addWidget(self.thumbnails, stretch=1)
        splitter.addWidget(left)

        # -- center: image viewer + toolbar -----------------------------------------
        center = QWidget()
        center_layout = QVBoxLayout(center)
        toolbar = QHBoxLayout()
        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        fit_btn = QPushButton("Fit")
        rotate_l_btn = QPushButton("Rotate ⟲")
        rotate_r_btn = QPushButton("Rotate ⟳")
        self.region_btn = QPushButton("Region Select")
        self.region_btn.setCheckable(True)
        for b in (zoom_in_btn, zoom_out_btn, fit_btn, rotate_l_btn, rotate_r_btn, self.region_btn):
            b.setObjectName("SecondaryButton")
            toolbar.addWidget(b)
        toolbar.addStretch(1)
        center_layout.addLayout(toolbar)

        self.viewer = ImageViewer()
        center_layout.addWidget(self.viewer, stretch=1)

        zoom_in_btn.clicked.connect(self.viewer.zoom_in)
        zoom_out_btn.clicked.connect(self.viewer.zoom_out)
        fit_btn.clicked.connect(self.viewer.fit_to_view)
        rotate_l_btn.clicked.connect(lambda: self.viewer.rotate_view(-90))
        rotate_r_btn.clicked.connect(lambda: self.viewer.rotate_view(90))
        self.region_btn.toggled.connect(self.viewer.set_selection_mode)

        splitter.addWidget(center)

        # -- right: settings + results ------------------------------------------------
        right = QWidget()
        right.setMaximumWidth(420)
        right_layout = QVBoxLayout(right)

        right_layout.addWidget(self._build_settings_panel())

        self.run_btn = QPushButton("Run OCR")
        self.run_btn.clicked.connect(self.run_ocr)
        right_layout.addWidget(self.run_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        results_label = QLabel("Extracted Text")
        results_label.setObjectName("SectionTitle")
        right_layout.addWidget(results_label)

        right_layout.addLayout(self._build_find_replace_bar())

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("OCR results will appear here — fully editable.")
        right_layout.addWidget(self.result_text, stretch=1)

        self.confidence_label = QLabel("")
        self.confidence_label.setObjectName("Muted")
        right_layout.addWidget(self.confidence_label)

        spellcheck_btn = QPushButton("Check Spelling")
        spellcheck_btn.setObjectName("SecondaryButton")
        spellcheck_btn.clicked.connect(self._run_spellcheck)
        right_layout.addWidget(spellcheck_btn)

        right_layout.addLayout(self._build_export_bar())

        splitter.addWidget(right)
        splitter.setSizes([220, 700, 420])

    def _build_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("Card")
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("OCR Settings"))

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        for engine in self.engine_manager.list_engines():
            suffix = "" if engine.is_available() else " (not installed)"
            self.engine_combo.addItem(f"{engine.display_name}{suffix}", engine.name)
        default_engine = self.settings.get("default_ocr_engine", "tesseract")
        self._select_combo_data(self.engine_combo, default_engine)
        row1.addWidget(self.engine_combo)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("Auto-detect", AUTO_DETECT_LANGUAGE)
        for name, code in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(name, code)
        row2.addWidget(self.language_combo)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        for mode in OCR_MODES:
            self.mode_combo.addItem(mode.replace("_", " ").title(), mode)
        self._select_combo_data(self.mode_combo, self.settings.get("default_mode", "balanced"))
        row3.addWidget(self.mode_combo)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Confidence threshold:"))
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(int(self.settings.get("confidence_threshold", 60)))
        self.confidence_value_label = QLabel(str(self.confidence_slider.value()))
        self.confidence_slider.valueChanged.connect(lambda v: self.confidence_value_label.setText(str(v)))
        row4.addWidget(self.confidence_slider)
        row4.addWidget(self.confidence_value_label)
        layout.addLayout(row4)

        self.gpu_checkbox = QCheckBox("Use GPU (EasyOCR / PaddleOCR)")
        self.gpu_checkbox.setChecked(bool(self.settings.get("use_gpu", False)))
        layout.addWidget(self.gpu_checkbox)

        return panel

    def _build_find_replace_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with")
        find_btn = QPushButton("Find")
        find_btn.setObjectName("SecondaryButton")
        find_btn.clicked.connect(self._find_next)
        replace_btn = QPushButton("Replace All")
        replace_btn.setObjectName("SecondaryButton")
        replace_btn.clicked.connect(self._replace_all)
        row.addWidget(self.find_input)
        row.addWidget(self.replace_input)
        row.addWidget(find_btn)
        row.addWidget(replace_btn)
        return row

    def _build_export_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(list(EXPORT_FORMATS))
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_result)
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("SecondaryButton")
        copy_btn.clicked.connect(self._copy_to_clipboard)
        row.addWidget(self.export_format_combo)
        row.addWidget(export_btn)
        row.addWidget(copy_btn)
        return row

    @staticmethod
    def _select_combo_data(combo: QComboBox, data_value: str) -> None:
        index = combo.findData(data_value)
        if index >= 0:
            combo.setCurrentIndex(index)

    # -- file loading -----------------------------------------------------------------
    def load_files(self, paths: list[str]) -> None:
        if not paths:
            return
        path = paths[0]
        try:
            self.loaded_pages = DocumentProcessor.load_pages(path)
        except DocumentProcessingError as exc:
            QMessageBox.warning(self, "Unable to load file", str(exc))
            return

        self.current_path = path
        self.current_document = None
        self.thumbnails.set_pages(
            [(f"Page {i + 1}", img) for i, img in enumerate(self.loaded_pages)]
        )
        self.viewer.load_array(self.loaded_pages[0])
        self.settings.add_recent_file(path)
        self.status_message.emit(f"Loaded {Path(path).name} ({len(self.loaded_pages)} page(s))")

    def _on_page_selected(self, index: int) -> None:
        if 0 <= index < len(self.loaded_pages):
            self.viewer.load_array(self.loaded_pages[index])

    # -- OCR ------------------------------------------------------------------------------
    def run_ocr(self) -> None:
        if not self.current_path:
            QMessageBox.information(self, "No file loaded", "Drag & drop or browse for a file first.")
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_message.emit("Running OCR…")

        self._thread = OCRRunThread(
            self.current_path,
            engine=self.engine_combo.currentData(),
            language=self.language_combo.currentData(),
            mode=self.mode_combo.currentData(),
            use_gpu=self.gpu_checkbox.isChecked(),
            confidence=float(self.confidence_slider.value()),
        )
        self._thread.progress.connect(self._on_progress)
        self._thread.finished_ok.connect(self._on_ocr_finished)
        self._thread.failed.connect(self._on_ocr_failed)
        self._thread.start()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_ocr_finished(self, document: OCRDocument) -> None:
        self.current_document = document
        self.result_text.setPlainText(document.full_text)
        self.confidence_label.setText(
            f"Engine: {document.engine} | Confidence: {document.mean_confidence:.1f}% | "
            f"Time: {document.processing_time_seconds:.2f}s"
            + (f" | Detected language: {document.detected_language}" if document.detected_language else "")
        )
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_message.emit("OCR complete.")

        if self.settings.get("autosave", True):
            self._record_history(document, output_path="")

    def _on_ocr_failed(self, message: str) -> None:
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_message.emit("OCR failed.")
        QMessageBox.critical(self, "OCR failed", message)

    def _record_history(self, document: OCRDocument, output_path: str) -> None:
        record = HistoryRecord(
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
        )
        self.db.insert_record(record, extracted_text=document.full_text)

    # -- find & replace --------------------------------------------------------------------
    def _find_next(self) -> None:
        query = self.find_input.text()
        if query:
            self.result_text.find(query)

    def _replace_all(self) -> None:
        query = self.find_input.text()
        replacement = self.replace_input.text()
        if not query:
            return
        text = self.result_text.toPlainText().replace(query, replacement)
        self.result_text.setPlainText(text)

    # -- spellcheck -----------------------------------------------------------------------
    def _run_spellcheck(self) -> None:
        text = self.result_text.toPlainText()
        lang = "en"
        if self.current_document and self.current_document.detected_language:
            lang = self.current_document.detected_language
        misspelled = spellcheck_text(text, language=lang)
        if not misspelled:
            QMessageBox.information(self, "Spell Check", "No issues found (or dictionary unavailable for this language).")
        else:
            preview = ", ".join(misspelled[:30])
            QMessageBox.information(self, "Spell Check", f"{len(misspelled)} possibly misspelled word(s):\n{preview}")

    # -- export / clipboard ------------------------------------------------------------------
    def _copy_to_clipboard(self) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(self.result_text.toPlainText())
        self.status_message.emit("Copied to clipboard.")

    def export_result(self) -> None:
        if self.current_document is None:
            QMessageBox.information(self, "Nothing to export", "Run OCR first.")
            return

        # Reflect any manual edits the user made in the text panel.
        edited_text = self.result_text.toPlainText()
        if self.current_document.pages:
            self.current_document.pages[0].text = edited_text

        fmt = ExportFormat(self.export_format_combo.currentText())
        default_dir = self.settings.get("default_export_folder")
        base_name = Path(self.current_path).stem
        suggested = unique_output_path(default_dir, base_name, extension_for(fmt))

        path_str, _ = QFileDialog.getSaveFileName(self, "Export As", str(suggested))
        if not path_str:
            return
        try:
            output_path = export_document(self.current_document, fmt, path_str)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        self.status_message.emit(f"Exported to {output_path}")
        self._record_history(self.current_document, output_path=str(output_path))
