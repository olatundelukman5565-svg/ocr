"""Single entry point for exporting an :class:`OCRDocument` to any
supported output format. The UI's Export Center and the batch/CLI paths
both call :func:`export_document` so format support only needs to live
in one place.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.models import ExportFormat, OCRDocument
from app.exports.formats import (
    csv_exporter,
    docx_exporter,
    html_exporter,
    json_exporter,
    markdown_exporter,
    pdf_exporter,
    rtf_exporter,
    txt_exporter,
    xlsx_exporter,
)

logger = logging.getLogger(__name__)

_EXTENSION_BY_FORMAT = {
    ExportFormat.TXT: ".txt",
    ExportFormat.DOCX: ".docx",
    ExportFormat.PDF: ".pdf",
    ExportFormat.SEARCHABLE_PDF: ".pdf",
    ExportFormat.CSV: ".csv",
    ExportFormat.XLSX: ".xlsx",
    ExportFormat.JSON: ".json",
    ExportFormat.HTML: ".html",
    ExportFormat.MARKDOWN: ".md",
    ExportFormat.RTF: ".rtf",
}


def extension_for(fmt: str | ExportFormat) -> str:
    return _EXTENSION_BY_FORMAT[ExportFormat(fmt)]


def export_document(document: OCRDocument, fmt: str | ExportFormat, output_path: str | Path) -> Path:
    """Write ``document`` to ``output_path`` in the requested format."""
    fmt = ExportFormat(fmt)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dispatch = {
        ExportFormat.TXT: txt_exporter.export,
        ExportFormat.DOCX: docx_exporter.export,
        ExportFormat.PDF: pdf_exporter.export,
        ExportFormat.SEARCHABLE_PDF: pdf_exporter.export_searchable,
        ExportFormat.CSV: csv_exporter.export,
        ExportFormat.XLSX: xlsx_exporter.export,
        ExportFormat.JSON: json_exporter.export,
        ExportFormat.HTML: html_exporter.export,
        ExportFormat.MARKDOWN: markdown_exporter.export,
        ExportFormat.RTF: rtf_exporter.export,
    }

    handler = dispatch[fmt]
    logger.info("Exporting '%s' as %s -> %s", document.source_path, fmt.value, output_path)
    return handler(document, output_path)


def copy_text_to_clipboard(document: OCRDocument) -> str:
    """Return the plain text payload the UI should place on the clipboard."""
    return document.full_text
