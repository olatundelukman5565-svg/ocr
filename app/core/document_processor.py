"""Orchestrates the full pipeline for a single file: load -> preprocess ->
OCR -> postprocess -> :class:`~app.core.models.OCRDocument`.

This is the single entry point used identically by the interactive
Workspace page and by the headless :class:`~app.core.batch_manager.BatchManager`.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import cv2
import numpy as np

from app.config.constants import AUTO_DETECT_LANGUAGE
from app.core.models import OCRDocument, OCRMode
from app.core.text_postprocessor import detect_language
from app.ocr.base_engine import OCREngine
from app.ocr.engine_manager import get_engine_manager
from app.utils.file_utils import is_supported_pdf
from app.utils.image_preprocessing import ImagePreprocessor, PreprocessingOptions
from app.utils.pdf_utils import pdf_to_images

logger = logging.getLogger(__name__)


class DocumentProcessingError(RuntimeError):
    """Raised for unreadable/corrupted files or unrecoverable OCR failures."""


class DocumentProcessor:
    """Stateless orchestrator; all configuration is passed per call so a
    single instance is safely reusable across threads/batch workers.
    """

    def __init__(self, engine_manager=None) -> None:
        self.engine_manager = engine_manager or get_engine_manager()

    # -- loading -----------------------------------------------------------------
    @staticmethod
    def load_pages(path: str | Path) -> list[np.ndarray]:
        """Return a list of BGR numpy images: one per PDF page, or a
        single-element list for a plain image file.
        """
        path = Path(path)
        if not path.exists():
            raise DocumentProcessingError(f"File not found: {path}")

        if is_supported_pdf(path):
            try:
                return pdf_to_images(path)
            except Exception as exc:  # noqa: BLE001
                raise DocumentProcessingError(f"Could not read PDF '{path.name}': {exc}") from exc

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise DocumentProcessingError(f"Could not decode image (unsupported/corrupted): {path.name}")
        return [image]

    # -- main entry point -----------------------------------------------------------
    def process(
        self,
        path: str | Path,
        engine_name: str = "tesseract",
        language: str = AUTO_DETECT_LANGUAGE,
        mode: str = OCRMode.BALANCED.value,
        use_gpu: bool = False,
        confidence_threshold: float = 0.0,
        preprocessing_overrides: dict | None = None,
        progress_callback=None,
    ) -> OCRDocument:
        """Run the complete pipeline on ``path`` and return an :class:`OCRDocument`.

        ``progress_callback(current_page, total_pages)`` is invoked after
        each page, letting the UI/batch queue report fine-grained progress.
        """
        start_time = time.perf_counter()
        path = Path(path)

        engine: OCREngine = self.engine_manager.resolve(engine_name)

        options = PreprocessingOptions.for_mode(mode)
        if preprocessing_overrides:
            for key, value in preprocessing_overrides.items():
                if hasattr(options, key):
                    setattr(options, key, value)

        pages_images = self.load_pages(path)
        ocr_language = "en" if language == AUTO_DETECT_LANGUAGE else language

        document = OCRDocument(
            source_path=str(path), engine=engine.name, language=language, mode=mode
        )

        total = len(pages_images)
        for index, raw_image in enumerate(pages_images, start=1):
            preprocessed = ImagePreprocessor.preprocess_pipeline(raw_image, options)
            page = engine.recognize(
                preprocessed.image,
                language=ocr_language,
                use_gpu=use_gpu,
                page_number=index,
                confidence_threshold=confidence_threshold,
            )
            document.pages.append(page)
            if progress_callback:
                progress_callback(index, total)

        if language == AUTO_DETECT_LANGUAGE:
            document.detected_language = detect_language(document.full_text)

        document.processing_time_seconds = time.perf_counter() - start_time
        logger.info(
            "Processed '%s' with %s in %.2fs (%d page(s), mean confidence %.1f%%)",
            path.name,
            engine.name,
            document.processing_time_seconds,
            document.page_count,
            document.mean_confidence,
        )
        return document
