"""Structured JSON export: full OCRDocument dump including per-word bounding
boxes and confidence, for downstream automation/integration.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.models import OCRDocument


def export(document: OCRDocument, path: str | Path) -> Path:
    path = Path(path)
    payload = {
        "document_id": document.document_id,
        "source_path": document.source_path,
        "engine": document.engine,
        "language": document.language,
        "detected_language": document.detected_language,
        "mode": document.mode,
        "processing_time_seconds": document.processing_time_seconds,
        "mean_confidence": document.mean_confidence,
        "page_count": document.page_count,
        "pages": [
            {
                "page_number": page.page_number,
                "text": page.text,
                "mean_confidence": page.mean_confidence,
                "width": page.width,
                "height": page.height,
                "words": [
                    {
                        "text": w.text,
                        "confidence": w.confidence,
                        "bbox": w.bbox,
                        "line_number": w.line_number,
                        "paragraph_number": w.paragraph_number,
                    }
                    for w in page.words
                ],
            }
            for page in document.pages
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
