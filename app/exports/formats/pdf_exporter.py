"""PDF export in two flavours:

* :func:`export` -- a plain, reflowed-text PDF (via reportlab) suitable
  when only the extracted text matters.
* :func:`export_searchable` -- a "searchable PDF" that looks exactly like
  the original scan but has an invisible, selectable OCR text layer
  positioned over every recognized word (via PyMuPDF).
"""
from __future__ import annotations

import logging
from pathlib import Path

import cv2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.core.document_processor import DocumentProcessor
from app.core.models import OCRDocument
from app.utils.pdf_utils import create_searchable_pdf

logger = logging.getLogger(__name__)


def export(document: OCRDocument, path: str | Path) -> Path:
    """Plain text-only PDF: readable, but not a facsimile of the source scan."""
    path = Path(path)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    margin = 2 * cm
    usable_width = width - 2 * margin
    line_height = 14

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, Path(document.source_path).name)
    c.setFont("Helvetica", 10)
    y = height - margin - 2 * line_height

    for page in document.pages:
        for paragraph in page.text.split("\n\n"):
            if not paragraph.strip():
                continue
            for wrapped_line in _wrap_text(c, paragraph.strip(), usable_width, "Helvetica", 10):
                if y < margin:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - margin
                c.drawString(margin, y, wrapped_line)
                y -= line_height
            y -= line_height * 0.5

    c.save()
    return path


def _wrap_text(c: canvas.Canvas, text: str, max_width: float, font: str, size: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if c.stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def export_searchable(document: OCRDocument, path: str | Path, source_path: str | None = None) -> Path:
    """Rebuild page images from the original source file (resized to match
    each :class:`OCRPage`'s dimensions, so word bounding boxes line up
    exactly) and lay the OCR text underneath as an invisible layer.
    """
    path = Path(path)
    src = source_path or document.source_path
    raw_pages = DocumentProcessor.load_pages(src)

    aligned_images = []
    for raw_image, page in zip(raw_pages, document.pages):
        if page.width and page.height and (raw_image.shape[1], raw_image.shape[0]) != (page.width, page.height):
            raw_image = cv2.resize(raw_image, (page.width, page.height), interpolation=cv2.INTER_CUBIC)
        aligned_images.append(raw_image)

    words_per_page = [page.words for page in document.pages]
    create_searchable_pdf(aligned_images, words_per_page, path)
    return path
