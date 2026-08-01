"""Drag & drop target used on the Home, Workspace and Batch pages."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.utils.file_utils import is_supported_file


class DropArea(QWidget):
    """Emits ``files_dropped(list[str])`` for any supported images/PDFs
    dropped onto it (folders are expanded to their supported contents).
    """

    files_dropped = Signal(list)

    def __init__(self, hint_text: str = "Drag & drop images or PDFs here, or click to browse", parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("Card")
        self.setMinimumHeight(160)

        layout = QVBoxLayout(self)
        self.label = QLabel(hint_text)
        self.label.setObjectName("Muted")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        from app.utils.file_utils import iter_supported_files

        paths: list[str] = []
        for url in event.mimeData().urls():
            local = Path(url.toLocalFile())
            if not local.exists():
                continue
            if local.is_dir():
                paths.extend(str(p) for p in iter_supported_files(local))
            elif is_supported_file(local):
                paths.append(str(local))
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        from PySide6.QtWidgets import QFileDialog

        from app.config.constants import SUPPORTED_INPUT_EXTENSIONS

        patterns = " ".join(f"*{ext}" for ext in SUPPORTED_INPUT_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(self, "Select files", "", f"Supported files ({patterns})")
        if files:
            self.files_dropped.emit(files)
        super().mousePressEvent(event)
