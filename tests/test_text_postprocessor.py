from __future__ import annotations

from app.core.models import OCRWord
from app.core.text_postprocessor import detect_language, group_words_into_paragraphs


def test_group_words_into_paragraphs_splits_on_large_gaps():
    words = [
        OCRWord(text="First", confidence=90, bbox=(0, 0, 40, 20), line_number=0),
        OCRWord(text="line", confidence=90, bbox=(45, 0, 40, 20), line_number=0),
        OCRWord(text="Second", confidence=90, bbox=(0, 25, 40, 20), line_number=1),
        OCRWord(text="line", confidence=90, bbox=(45, 25, 40, 20), line_number=1),
        # Large vertical gap -> new paragraph
        OCRWord(text="New", confidence=90, bbox=(0, 200, 40, 20), line_number=2),
        OCRWord(text="paragraph", confidence=90, bbox=(45, 200, 60, 20), line_number=2),
    ]
    result = group_words_into_paragraphs(words)
    paragraphs = result.split("\n\n")
    assert len(paragraphs) == 2
    assert paragraphs[0] == "First line Second line"
    assert paragraphs[1] == "New paragraph"


def test_group_words_into_paragraphs_empty_input():
    assert group_words_into_paragraphs([]) == ""


def test_detect_language_english():
    detected = detect_language("This is a reasonably long sentence written in English for detection.")
    assert detected in (None, "en")  # None only if langdetect isn't installed
