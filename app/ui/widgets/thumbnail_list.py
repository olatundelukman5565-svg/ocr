"""Sidebar list of loaded pages/images with small preview thumbnails,
used by the Workspace page for multi-image/multi-page navigation.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.ui.widgets.image_viewer import numpy_to_qpixmap


class ThumbnailList(QListWidget):
    """Emits ``page_selected(int)`` with the index of the clicked thumbnail."""

    page_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setIconSize(QSize(96, 96))
        self.setSpacing(4)
        self.currentRowChanged.connect(self.page_selected.emit)

    def clear_pages(self) -> None:
        self.clear()

    def add_page(self, label: str, image: np.ndarray | None = None) -> None:
        item = QListWidgetItem(label)
        if image is not None:
            pixmap = numpy_to_qpixmap(image).scaled(
                96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            item.setIcon(QIcon(pixmap))
        self.addItem(item)

    def set_pages(self, labels_and_images: list[tuple[str, np.ndarray | None]]) -> None:
        self.clear_pages()
        for label, image in labels_and_images:
            self.add_page(label, image)
        if labels_and_images:
            self.setCurrentRow(0)
