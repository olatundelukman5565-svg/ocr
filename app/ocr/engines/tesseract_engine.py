"""Tesseract OCR engine wrapper (via pytesseract).

Tesseract is the most reliably-installable fully-offline OCR engine, and
is used as the application's default. It runs entirely on CPU.
"""
from __future__ import annotations

import logging
import os
import shutil

import numpy as np

from app.core.models import OCRPage, OCRWord
from app.ocr.base_engine import OCREngine, OCREngineUnavailableError

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image

    _IMPORT_OK = True
except ImportError:  # pragma: no cover
    _IMPORT_OK = False

# Common install locations for platforms/installers that don't reliably put
# `tesseract` on PATH for an already-open shell (notably the UB-Mannheim
# Windows installer, whose PATH update often only takes effect in *new*
# shells/processes started after install). Checked as a fallback so the app
# works immediately after installation without requiring a reboot.
_FALLBACK_BINARY_PATHS = [
    os.path.expandvars(r"%ProgramFiles%\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%LocalAppData%\Programs\Tesseract-OCR\tesseract.exe"),
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
    "/usr/bin/tesseract",
]


def _locate_tesseract_binary() -> str | None:
    """Return a usable tesseract binary path: PATH first, then well-known
    install locations. Also honours a TESSERACT_CMD env var override.
    """
    if override := os.environ.get("TESSERACT_CMD"):
        if os.path.isfile(override):
            return override
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in _FALLBACK_BINARY_PATHS:
        if os.path.isfile(candidate):
            return candidate
    return None


if _IMPORT_OK:
    _binary_path = _locate_tesseract_binary()
    if _binary_path and shutil.which("tesseract") is None:
        # Only PATH-based `tesseract` calls are visible to shutil.which();
        # point pytesseract directly at the binary we found instead.
        pytesseract.pytesseract.tesseract_cmd = _binary_path
        logger.info("Located Tesseract binary outside PATH: %s", _binary_path)


class TesseractEngine(OCREngine):
    name = "tesseract"
    display_name = "Tesseract OCR"
    supports_gpu = False

    # Generic language code (app.config.constants.SUPPORTED_LANGUAGES) -> tesseract 3-letter code
    LANGUAGE_MAP = {
        "en": "eng", "fr": "fra", "de": "deu", "es": "spa", "it": "ita",
        "pt": "por", "nl": "nld", "zh": "chi_sim", "ja": "jpn", "ko": "kor",
        "ar": "ara", "hi": "hin", "tr": "tur", "ru": "rus", "th": "tha", "vi": "vie",
    }

    def is_available(self) -> bool:
        if not _IMPORT_OK:
            return False
        if _locate_tesseract_binary() is None:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:  # noqa: BLE001
            return False

    def supported_languages(self) -> dict[str, str]:
        return dict(self.LANGUAGE_MAP)

    def recognize(
        self,
        image: np.ndarray,
        language: str = "en",
        use_gpu: bool = False,
        page_number: int = 1,
        confidence_threshold: float = 0.0,
        psm: int = 3,
        **kwargs,
    ) -> OCRPage:
        self.ensure_available()

        tesseract_lang = self.translate_language(language) or "eng"
        pil_image = Image.fromarray(image) if image.ndim == 2 else Image.fromarray(image[:, :, ::-1])

        config = f"--oem 3 --psm {psm}"
        try:
            data = pytesseract.image_to_data(
                pil_image, lang=tesseract_lang, config=config, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractError as exc:
            raise OCREngineUnavailableError(str(exc)) from exc

        words: list[OCRWord] = []
        lines: dict[tuple[int, int, int], list[str]] = {}
        confidences: list[float] = []

        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            conf_raw = data["conf"][i]
            try:
                conf = float(conf_raw)
            except (TypeError, ValueError):
                conf = -1.0
            if not text or conf < 0:
                continue
            if conf < confidence_threshold:
                continue
            bbox = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            words.append(
                OCRWord(
                    text=text,
                    confidence=conf,
                    bbox=bbox,
                    line_number=data["line_num"][i],
                    paragraph_number=data["par_num"][i],
                )
            )
            lines.setdefault(key, []).append(text)
            confidences.append(conf)

        full_text = "\n".join(" ".join(tokens) for tokens in lines.values())
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return OCRPage(
            page_number=page_number,
            text=full_text,
            words=words,
            mean_confidence=mean_conf,
            width=image.shape[1],
            height=image.shape[0],
        )
