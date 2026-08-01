from __future__ import annotations

import json

import pytest

from app.core.models import ExportFormat, OCRDocument, OCRPage, OCRWord
from app.exports.exporter import export_document, extension_for
from app.ocr.engine_manager import get_engine_manager

TESSERACT_AVAILABLE = get_engine_manager().get_engine("tesseract").is_available()


@pytest.fixture
def sample_document() -> OCRDocument:
    words = [
        OCRWord(text="Hello", confidence=95.0, bbox=(0, 0, 40, 20), line_number=0),
        OCRWord(text="World", confidence=88.0, bbox=(45, 0, 40, 20), line_number=0),
    ]
    page = OCRPage(page_number=1, text="Hello World", words=words, mean_confidence=91.5, width=200, height=100)
    return OCRDocument(source_path="test.png", pages=[page], engine="tesseract", language="en")


def test_extension_for_every_format():
    for fmt in ExportFormat:
        ext = extension_for(fmt)
        assert ext.startswith(".")


def test_export_txt(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.TXT, tmp_path / "out.txt")
    assert out.read_text(encoding="utf-8") == "Hello World"


def test_export_json_round_trips_words(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.JSON, tmp_path / "out.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pages"][0]["words"][0]["text"] == "Hello"
    assert payload["mean_confidence"] == pytest.approx(91.5)


def test_export_csv_has_header_and_word_rows(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.CSV, tmp_path / "out.csv")
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("page,text,confidence")
    assert len(lines) == 3  # header + 2 words


def test_export_html_contains_text(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.HTML, tmp_path / "out.html")
    content = out.read_text(encoding="utf-8")
    assert "Hello World" in content
    assert "<html" in content


def test_export_markdown_contains_text(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.MARKDOWN, tmp_path / "out.md")
    assert "Hello World" in out.read_text(encoding="utf-8")


def test_export_rtf_is_valid_rtf_header(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.RTF, tmp_path / "out.rtf")
    content = out.read_text(encoding="ascii")
    assert content.startswith(r"{\rtf1")
    assert "Hello World" in content


def test_export_docx_creates_file(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.DOCX, tmp_path / "out.docx")
    assert out.exists() and out.stat().st_size > 0


def test_export_xlsx_creates_file(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.XLSX, tmp_path / "out.xlsx")
    assert out.exists() and out.stat().st_size > 0


def test_export_pdf_creates_file(tmp_path, sample_document):
    out = export_document(sample_document, ExportFormat.PDF, tmp_path / "out.pdf")
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract binary not installed")
def test_export_searchable_pdf_text_is_extractable(tmp_path, sample_invoice_path):
    import fitz

    from app.core.document_processor import DocumentProcessor

    processor = DocumentProcessor()
    document = processor.process(sample_invoice_path, engine_name="tesseract", language="en", mode="fast")
    out = export_document(document, ExportFormat.SEARCHABLE_PDF, tmp_path / "out.pdf")
    with fitz.open(str(out)) as pdf:
        extracted = pdf[0].get_text()
    assert "INVOICE" in extracted.upper()
