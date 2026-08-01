"""CSV export: one row per recognized word, with page, position and confidence."""
from __future__ import annotations

import csv
from pathlib import Path

from app.core.models import OCRDocument


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["page", "text", "confidence", "x", "y", "width", "height", "line_number"])
        for page in document.pages:
            if page.words:
                for word in page.words:
                    x, y, w, h = word.bbox
                    writer.writerow([page.page_number, word.text, f"{word.confidence:.1f}", x, y, w, h, word.line_number])
            else:
                writer.writerow([page.page_number, page.text, f"{page.mean_confidence:.1f}", "", "", "", "", ""])
    return path
