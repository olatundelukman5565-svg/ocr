"""Shared pytest fixtures: synthetic OpenCV images and sample file paths."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

SAMPLE_DIR = Path(__file__).parent.parent / "sample_images"


@pytest.fixture
def white_image() -> np.ndarray:
    return np.full((200, 300, 3), 255, dtype=np.uint8)


@pytest.fixture
def noisy_gray_image() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 255, size=(150, 150), dtype=np.uint8)


@pytest.fixture
def sample_invoice_path() -> Path:
    return SAMPLE_DIR / "sample_invoice.png"


@pytest.fixture
def sample_multipage_pdf_path() -> Path:
    return SAMPLE_DIR / "sample_multipage.pdf"


@pytest.fixture
def sample_skewed_path() -> Path:
    return SAMPLE_DIR / "sample_receipt_skewed.png"
