"""Registry/factory for OCR engines, allowing the UI and batch processor to
switch engines at runtime and to discover which ones are actually usable
on the current machine.
"""
from __future__ import annotations

import logging

from app.ocr.base_engine import OCREngine, OCREngineUnavailableError
from app.ocr.engines.easyocr_engine import EasyOCREngine
from app.ocr.engines.paddleocr_engine import PaddleOCREngine
from app.ocr.engines.tesseract_engine import TesseractEngine

logger = logging.getLogger(__name__)


class OCREngineManager:
    """Lazily-instantiated, process-wide registry of OCR engines."""

    def __init__(self) -> None:
        self._engines: dict[str, OCREngine] = {
            "tesseract": TesseractEngine(),
            "easyocr": EasyOCREngine(),
            "paddleocr": PaddleOCREngine(),
        }

    def get_engine(self, name: str) -> OCREngine:
        try:
            return self._engines[name]
        except KeyError as exc:
            raise ValueError(f"Unknown OCR engine '{name}'") from exc

    def list_engines(self) -> list[OCREngine]:
        return list(self._engines.values())

    def list_available_engines(self) -> list[OCREngine]:
        return [engine for engine in self._engines.values() if engine.is_available()]

    def resolve(self, preferred_name: str) -> OCREngine:
        """Return the requested engine if available, otherwise fall back to
        the first available engine and log a warning; raises if none of the
        registered engines are usable at all.
        """
        engine = self._engines.get(preferred_name)
        if engine is not None and engine.is_available():
            return engine

        available = self.list_available_engines()
        if not available:
            raise OCREngineUnavailableError(
                "No OCR engine is available. Install Tesseract (recommended default), "
                "or the easyocr / paddleocr Python packages."
            )
        fallback = available[0]
        logger.warning(
            "Requested OCR engine '%s' is unavailable; falling back to '%s'",
            preferred_name,
            fallback.name,
        )
        return fallback


_manager_instance: OCREngineManager | None = None


def get_engine_manager() -> OCREngineManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = OCREngineManager()
    return _manager_instance
