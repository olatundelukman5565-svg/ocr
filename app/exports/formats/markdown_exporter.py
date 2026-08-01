"""Markdown export: one heading per page, paragraphs preserved."""
from __future__ import annotations

from pathlib import Path

from app.core.models import OCRDocument


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    lines = [f"# {Path(document.source_path).name}", ""]
    for page in document.pages:
        if document.page_count > 1:
            lines.append(f"## Page {page.page_number}")
            lines.append("")
        for paragraph in page.text.split("\n\n"):
            if paragraph.strip():
                lines.append(paragraph.strip())
                lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
