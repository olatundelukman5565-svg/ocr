"""Rich Text Format export. RTF's control-word syntax is simple enough to
emit directly without a third-party dependency.
"""
from __future__ import annotations

from pathlib import Path

from app.core.models import OCRDocument


def _escape_rtf(text: str) -> str:
    text = text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
    escaped_lines = [line.encode("ascii", "xmlcharrefreplace").decode("ascii") for line in text.split("\n")]
    return r"\line ".join(escaped_lines)


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    parts = [r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Calibri;}}", r"\f0\fs22"]
    for page in document.pages:
        if document.page_count > 1:
            parts.append(rf"\b Page {page.page_number}\b0\line ")
        for paragraph in page.text.split("\n\n"):
            if paragraph.strip():
                parts.append(_escape_rtf(paragraph.strip()))
                parts.append(r"\par ")
    parts.append("}")
    path.write_text("\n".join(parts), encoding="ascii", errors="xmlcharrefreplace")
    return path
