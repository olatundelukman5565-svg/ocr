"""Excel (.xlsx) export via openpyxl: one sheet of per-word data, one
summary sheet with per-page confidence/text.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from app.core.models import OCRDocument


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    wb = Workbook()

    summary = wb.active
    summary.title = "Summary"
    summary.append(["Page", "Mean Confidence (%)", "Text"])
    for cell in summary[1]:
        cell.font = Font(bold=True)
    for page in document.pages:
        summary.append([page.page_number, round(page.mean_confidence, 1), page.text])
    summary.column_dimensions["C"].width = 80

    words_sheet = wb.create_sheet("Words")
    words_sheet.append(["Page", "Text", "Confidence (%)", "X", "Y", "Width", "Height", "Line"])
    for cell in words_sheet[1]:
        cell.font = Font(bold=True)
    for page in document.pages:
        for word in page.words:
            x, y, w, h = word.bbox
            words_sheet.append([page.page_number, word.text, round(word.confidence, 1), x, y, w, h, word.line_number])

    wb.save(str(path))
    return path
