"""Plain text export."""
from __future__ import annotations

from pathlib import Path

from app.core.models import OCRDocument


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    path.write_text(document.full_text, encoding="utf-8")
    return path
