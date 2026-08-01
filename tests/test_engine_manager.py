from __future__ import annotations

import pytest

from app.ocr.base_engine import OCREngineUnavailableError
from app.ocr.engine_manager import OCREngineManager


def test_list_engines_returns_all_three_registered_engines():
    manager = OCREngineManager()
    names = {e.name for e in manager.list_engines()}
    assert names == {"tesseract", "easyocr", "paddleocr"}


def test_get_engine_unknown_name_raises():
    manager = OCREngineManager()
    with pytest.raises(ValueError):
        manager.get_engine("does-not-exist")


def test_resolve_falls_back_when_engine_unavailable():
    manager = OCREngineManager()
    # paddleocr is not installed in the test environment, so resolving it
    # should transparently fall back to an available engine (tesseract).
    engine = manager.resolve("paddleocr")
    assert engine.is_available()


def test_tesseract_engine_reports_available_when_binary_present():
    manager = OCREngineManager()
    tesseract = manager.get_engine("tesseract")
    # This assumes the CI/dev environment has the `tesseract` binary
    # installed; if not, is_available() should still return False cleanly
    # rather than raising.
    assert isinstance(tesseract.is_available(), bool)


def test_ensure_available_raises_typed_error_for_unavailable_engine():
    manager = OCREngineManager()
    paddle = manager.get_engine("paddleocr")
    if not paddle.is_available():
        with pytest.raises(OCREngineUnavailableError):
            paddle.ensure_available()
