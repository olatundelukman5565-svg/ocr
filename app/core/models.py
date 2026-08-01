"""Shared data models passed between the OCR engines, core processing
pipeline, database layer, export layer, and UI.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OCRMode(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH_ACCURACY = "high_accuracy"
    AI_ENHANCED = "ai_enhanced"
    BATCH = "batch"
    REGION = "region"
    TABLE = "table"
    HANDWRITING = "handwriting"


class ExportFormat(str, Enum):
    TXT = "TXT"
    DOCX = "DOCX"
    PDF = "PDF"
    SEARCHABLE_PDF = "SEARCHABLE_PDF"
    CSV = "CSV"
    XLSX = "XLSX"
    JSON = "JSON"
    HTML = "HTML"
    MARKDOWN = "MARKDOWN"
    RTF = "RTF"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class OCRWord:
    """A single recognized word/token with its pixel-space bounding box."""

    text: str
    confidence: float  # 0-100
    bbox: tuple[int, int, int, int]  # x, y, width, height (pixels)
    line_number: int = 0
    paragraph_number: int = 0


@dataclass
class OCRPage:
    """OCR output for a single image / PDF page."""

    page_number: int
    text: str
    words: list[OCRWord] = field(default_factory=list)
    mean_confidence: float = 0.0
    width: int = 0
    height: int = 0
    image_path: Optional[str] = None  # preprocessed image used for OCR, if cached to disk


@dataclass
class OCRDocument:
    """Aggregate OCR result for one source file (possibly multi-page)."""

    source_path: str
    pages: list[OCRPage] = field(default_factory=list)
    engine: str = ""
    language: str = ""
    mode: str = OCRMode.BALANCED.value
    processing_time_seconds: float = 0.0
    detected_language: Optional[str] = None
    document_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text for page in self.pages)

    @property
    def mean_confidence(self) -> float:
        confidences = [p.mean_confidence for p in self.pages if p.mean_confidence]
        return sum(confidences) / len(confidences) if confidences else 0.0

    @property
    def page_count(self) -> int:
        return len(self.pages)


@dataclass
class HistoryRecord:
    """Row shape persisted to / loaded from the SQLite history table."""

    id: Optional[int]
    file_name: str
    file_path: str
    date: str
    engine: str
    language: str
    confidence: float
    processing_time: float
    output_path: str
    status: str
    page_count: int = 1


@dataclass
class BatchItem:
    """One queued file within a :class:`~app.core.batch_manager.BatchManager` run."""

    path: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    result: Optional[OCRDocument] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
