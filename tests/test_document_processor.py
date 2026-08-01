from __future__ import annotations

import pytest

from app.core.document_processor import DocumentProcessor, DocumentProcessingError
from app.ocr.engine_manager import get_engine_manager

TESSERACT_AVAILABLE = get_engine_manager().get_engine("tesseract").is_available()


def test_load_pages_missing_file_raises():
    with pytest.raises(DocumentProcessingError):
        DocumentProcessor.load_pages("does-not-exist.png")


def test_load_pages_single_image(sample_invoice_path):
    pages = DocumentProcessor.load_pages(sample_invoice_path)
    assert len(pages) == 1
    assert pages[0].ndim == 3


def test_load_pages_multipage_pdf(sample_multipage_pdf_path):
    pages = DocumentProcessor.load_pages(sample_multipage_pdf_path)
    assert len(pages) == 2


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract binary not installed")
def test_process_extracts_expected_text_from_invoice(sample_invoice_path):
    processor = DocumentProcessor()
    document = processor.process(sample_invoice_path, engine_name="tesseract", language="en", mode="balanced")
    assert document.page_count == 1
    assert "INVOICE" in document.full_text.upper()
    assert document.mean_confidence > 50


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract binary not installed")
def test_process_multipage_pdf_returns_one_page_per_pdf_page(sample_multipage_pdf_path):
    processor = DocumentProcessor()
    document = processor.process(sample_multipage_pdf_path, engine_name="tesseract", language="en", mode="fast")
    assert document.page_count == 2
    assert "Page 1" in document.full_text
    assert "Page 2" in document.full_text


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract binary not installed")
def test_process_reports_progress_callback(sample_multipage_pdf_path):
    processor = DocumentProcessor()
    calls = []
    processor.process(
        sample_multipage_pdf_path,
        engine_name="tesseract",
        language="en",
        mode="fast",
        progress_callback=lambda cur, total: calls.append((cur, total)),
    )
    assert calls == [(1, 2), (2, 2)]
