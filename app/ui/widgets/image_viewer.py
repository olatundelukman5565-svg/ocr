"""Zoomable, rotatable, region-selectable image preview widget used by the
OCR Workspace, built on QGraphicsView/QGraphicsScene for smooth pan/zoom.
"""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
)


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    if image.ndim == 2:
        h, w = image.shape
        qimage = QImage(image.data, w, h, w, QImage.Format.Format_Grayscale8)
    else:
        h, w, _ = image.shape
        rgb = np.ascontiguousarray(image[:, :, ::-1])
        qimage = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())


class ImageViewer(QGraphicsView):
    """Displays one image with mouse-wheel zoom, click-drag pan, 90-degree
    rotation, and a rubber-band region selector for Region OCR / cropping.
    """

    region_selected = Signal(QRectF)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._rotation_degrees = 0
        self._selection_mode = False
        self._selection_item: QGraphicsRectItem | None = None
        self._selection_origin = None

    # -- loading -------------------------------------------------------------------
    def load_array(self, image: np.ndarray) -> None:
        pixmap = numpy_to_qpixmap(image)
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        self._rotation_degrees = 0
        self.resetTransform()
        self.fit_to_view()

    def fit_to_view(self) -> None:
        if self._pixmap_item is not None:
            self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    # -- zoom -------------------------------------------------------------------------
    def zoom_in(self, factor: float = 1.25) -> None:
        self.scale(factor, factor)

    def zoom_out(self, factor: float = 0.8) -> None:
        self.scale(factor, factor)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 - Qt override
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # -- rotation ---------------------------------------------------------------------
    def rotate_view(self, degrees: int) -> None:
        self._rotation_degrees = (self._rotation_degrees + degrees) % 360
        self.rotate(degrees)

    # -- region selection (crop / region OCR) ------------------------------------------
    def set_selection_mode(self, enabled: bool) -> None:
        self._selection_mode = enabled
        self.setDragMode(
            QGraphicsView.DragMode.NoDrag if enabled else QGraphicsView.DragMode.ScrollHandDrag
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._selection_mode and self._pixmap_item is not None:
            self._selection_origin = self.mapToScene(event.pos())
            if self._selection_item is not None:
                self._scene.removeItem(self._selection_item)
            self._selection_item = QGraphicsRectItem()
            pen = QPen(Qt.GlobalColor.red)
            pen.setWidth(2)
            self._selection_item.setPen(pen)
            self._scene.addItem(self._selection_item)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._selection_mode and self._selection_item is not None and self._selection_origin is not None:
            current = self.mapToScene(event.pos())
            rect = QRectF(self._selection_origin, current).normalized()
            self._selection_item.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt override
        if self._selection_mode and self._selection_item is not None:
            self.region_selected.emit(self._selection_item.rect())
        super().mouseReleaseEvent(event)

    def current_selection_rect(self) -> QRectF | None:
        return self._selection_item.rect() if self._selection_item is not None else None

    def clear_selection(self) -> None:
        if self._selection_item is not None:
            self._scene.removeItem(self._selection_item)
            self._selection_item = None
