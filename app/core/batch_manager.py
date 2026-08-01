"""Background batch OCR queue with pause/resume/cancel and ETA estimation.

Runs on a dedicated :class:`QThread` so the UI never blocks while
processing hundreds of queued files.
"""
from __future__ import annotations

import logging
import threading
import time

from PySide6.QtCore import QThread, Signal

from app.core.document_processor import DocumentProcessor
from app.core.models import BatchItem, JobStatus, OCRDocument

logger = logging.getLogger(__name__)


class BatchWorker(QThread):
    """Processes a list of files sequentially, emitting Qt signals the UI
    can bind directly to a progress bar / queue table.
    """

    item_started = Signal(int, str)  # index, path
    item_progress = Signal(int, int, int)  # index, current_page, total_pages
    item_finished = Signal(int, object)  # index, OCRDocument
    item_failed = Signal(int, str)  # index, error message
    batch_progress = Signal(int, int, float)  # completed, total, eta_seconds
    batch_finished = Signal()

    def __init__(
        self,
        items: list[BatchItem],
        engine_name: str,
        language: str,
        mode: str,
        use_gpu: bool = False,
        confidence_threshold: float = 0.0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.items = items
        self.engine_name = engine_name
        self.language = language
        self.mode = mode
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold

        self._processor = DocumentProcessor()
        self._pause_event = threading.Event()
        self._pause_event.set()  # set == running
        self._cancelled = False

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def cancel(self) -> None:
        self._cancelled = True
        self._pause_event.set()  # unblock a paused wait so cancellation is immediate

    def run(self) -> None:  # noqa: D102 - QThread entry point
        durations: list[float] = []
        total = len(self.items)

        for index, item in enumerate(self.items):
            if self._cancelled:
                item.status = JobStatus.CANCELLED
                continue

            self._pause_event.wait()
            if self._cancelled:
                item.status = JobStatus.CANCELLED
                continue

            item.status = JobStatus.PROCESSING
            item.started_at = time.time()
            self.item_started.emit(index, item.path)

            def on_progress(current_page: int, total_pages: int, idx=index) -> None:
                self.item_progress.emit(idx, current_page, total_pages)

            try:
                document: OCRDocument = self._processor.process(
                    item.path,
                    engine_name=self.engine_name,
                    language=self.language,
                    mode=self.mode,
                    use_gpu=self.use_gpu,
                    confidence_threshold=self.confidence_threshold,
                    progress_callback=on_progress,
                )
                item.result = document
                item.status = JobStatus.DONE
                item.finished_at = time.time()
                durations.append(item.finished_at - item.started_at)
                self.item_finished.emit(index, document)
            except Exception as exc:  # noqa: BLE001 - one bad file must not kill the batch
                logger.exception("Batch item failed: %s", item.path)
                item.status = JobStatus.FAILED
                item.error = str(exc)
                item.finished_at = time.time()
                self.item_failed.emit(index, str(exc))

            completed = index + 1
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            remaining = max(total - completed, 0)
            eta = avg_duration * remaining
            self.batch_progress.emit(completed, total, eta)

        self.batch_finished.emit()


class BatchManager:
    """Thin façade the UI constructs once per batch run; owns the worker
    thread's lifecycle and exposes plain-Python queue state.
    """

    def __init__(self) -> None:
        self.items: list[BatchItem] = []
        self.worker: BatchWorker | None = None

    def add_files(self, paths: list[str]) -> None:
        self.items.extend(BatchItem(path=p) for p in paths)

    def clear(self) -> None:
        self.items.clear()
        self.worker = None

    def start(
        self,
        engine_name: str,
        language: str,
        mode: str,
        use_gpu: bool = False,
        confidence_threshold: float = 0.0,
    ) -> BatchWorker:
        self.worker = BatchWorker(
            self.items, engine_name, language, mode, use_gpu, confidence_threshold
        )
        self.worker.start()
        return self.worker

    def pause(self) -> None:
        if self.worker:
            self.worker.pause()

    def resume(self) -> None:
        if self.worker:
            self.worker.resume()

    def cancel(self) -> None:
        if self.worker:
            self.worker.cancel()
