"""Post-OCR text intelligence: language detection, paragraph grouping and
spell checking. All optional dependencies degrade gracefully offline.
"""
from __future__ import annotations

import logging

from app.core.models import OCRPage, OCRWord

logger = logging.getLogger(__name__)

try:
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
    _LANGDETECT_OK = True
except ImportError:  # pragma: no cover
    _LANGDETECT_OK = False

try:
    from spellchecker import SpellChecker

    _SPELLCHECKER_OK = True
except ImportError:  # pragma: no cover
    _SPELLCHECKER_OK = False


def detect_language(text: str) -> str | None:
    """Best-effort natural-language detection of OCR output (auto-detect mode)."""
    if not _LANGDETECT_OK or not text or len(text.strip()) < 3:
        return None
    try:
        return detect(text)
    except Exception:  # noqa: BLE001 - langdetect raises on unclassifiable text
        return None


def group_words_into_paragraphs(words: list[OCRWord], line_gap_factor: float = 1.6) -> str:
    """Reconstruct paragraph breaks from word bounding boxes using vertical
    gaps between lines, rather than relying solely on the engine's own
    line/paragraph numbering (useful for engines that don't report it).
    """
    if not words:
        return ""

    lines: dict[int, list[OCRWord]] = {}
    for word in words:
        lines.setdefault(word.line_number, []).append(word)

    ordered_line_numbers = sorted(lines.keys())
    line_entries = []
    for line_no in ordered_line_numbers:
        line_words = sorted(lines[line_no], key=lambda w: w.bbox[0])
        top = min(w.bbox[1] for w in line_words)
        height = max(w.bbox[3] for w in line_words)
        text = " ".join(w.text for w in line_words)
        line_entries.append((top, height, text))

    if not line_entries:
        return ""

    paragraphs: list[list[str]] = [[line_entries[0][2]]]
    avg_height = sum(e[1] for e in line_entries) / len(line_entries) or 1
    for i in range(1, len(line_entries)):
        prev_top, prev_height, _ = line_entries[i - 1]
        top, height, text = line_entries[i]
        gap = top - (prev_top + prev_height)
        if gap > avg_height * line_gap_factor:
            paragraphs.append([text])
        else:
            paragraphs[-1].append(text)

    return "\n\n".join(" ".join(lines_) for lines_ in paragraphs)


def spellcheck_text(text: str, language: str = "en") -> list[str]:
    """Return the list of words in ``text`` that are likely misspelled.

    Only a handful of languages are supported by pyspellchecker; anything
    else (or a missing dependency) returns an empty list rather than raising.
    """
    if not _SPELLCHECKER_OK or not text:
        return []
    try:
        checker = SpellChecker(language=language)
    except Exception:  # noqa: BLE001 - unsupported language dictionary
        return []
    words = [w.strip(".,!?;:\"'()[]") for w in text.split()]
    words = [w for w in words if w.isalpha()]
    return sorted(checker.unknown(words))


def apply_confidence_filter(page: OCRPage, threshold: float) -> OCRPage:
    """Return a copy of ``page`` keeping only words at/above ``threshold``."""
    kept = [w for w in page.words if w.confidence >= threshold]
    text = group_words_into_paragraphs(kept) if kept else page.text
    mean_conf = sum(w.confidence for w in kept) / len(kept) if kept else 0.0
    return OCRPage(
        page_number=page.page_number,
        text=text,
        words=kept,
        mean_confidence=mean_conf,
        width=page.width,
        height=page.height,
        image_path=page.image_path,
    )
