"""Abstract base class every OCR engine wrapper must implement.

The rest of the application (document processor, UI settings panel,
batch manager) only ever talks to this interface, which is what lets the
user switch between Tesseract, EasyOCR and PaddleOCR at runtime without
any other code changing.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from app.core.models import OCRPage


class OCREngineUnavailableError(RuntimeError):
    """Raised when an engine is selected but its dependency isn't installed
    or its runtime (e.g. the Tesseract binary) can't be found."""


class OCREngine(ABC):
    """Common interface implemented by every OCR backend."""

    #: short machine name, e.g. "tesseract"
    name: str = "base"
    #: human-readable label for the UI
    display_name: str = "Base Engine"
    #: whether this engine can make use of a GPU
    supports_gpu: bool = False

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine's dependencies/binaries are usable."""

    @abstractmethod
    def recognize(
        self,
        image: np.ndarray,
        language: str = "en",
        use_gpu: bool = False,
        page_number: int = 1,
        **kwargs,
    ) -> OCRPage:
        """Run OCR on a single preprocessed image and return structured results."""

    @abstractmethod
    def supported_languages(self) -> dict[str, str]:
        """Return {display name: engine-specific language code} for this engine."""

    def ensure_available(self) -> None:
        if not self.is_available():
            raise OCREngineUnavailableError(
                f"OCR engine '{self.display_name}' is not available. "
                "Verify its dependency/binary is installed."
            )

    def translate_language(self, generic_code: str) -> Optional[str]:
        """Map a generic ISO-ish code (from app.config.constants) to this
        engine's own language code, if supported."""
        return self.LANGUAGE_MAP.get(generic_code)  # type: ignore[attr-defined]
