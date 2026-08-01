"""EasyOCR engine wrapper.

EasyOCR ships its own deep-learning detection + recognition models and
can run on GPU (CUDA) or CPU. The heavy ``easyocr`` package (and its
first-run model downloads) is imported lazily so the rest of the
application works even when it isn't installed.
"""
from __future__ import annotations

import logging
import threading

import numpy as np

from app.core.models import OCRPage, OCRWord
from app.ocr.base_engine import OCREngine, OCREngineUnavailableError

logger = logging.getLogger(__name__)

try:
    import easyocr

    _IMPORT_OK = True
except ImportError:  # pragma: no cover
    _IMPORT_OK = False


class EasyOCREngine(OCREngine):
    name = "easyocr"
    display_name = "EasyOCR"
    supports_gpu = True

    LANGUAGE_MAP = {
        "en": "en", "fr": "fr", "de": "de", "es": "es", "it": "it",
        "pt": "pt", "nl": "nl", "zh": "ch_sim", "ja": "ja", "ko": "ko",
        "ar": "ar", "hi": "hi", "tr": "tr", "ru": "ru", "th": "th", "vi": "vi",
    }

    def __init__(self) -> None:
        self._readers: dict[tuple[str, bool], "easyocr.Reader"] = {}
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return _IMPORT_OK

    def supported_languages(self) -> dict[str, str]:
        return dict(self.LANGUAGE_MAP)

    def _get_reader(self, lang_code: str, use_gpu: bool) -> "easyocr.Reader":
        key = (lang_code, use_gpu)
        with self._lock:
            if key not in self._readers:
                logger.info("Initializing EasyOCR reader for lang=%s gpu=%s", lang_code, use_gpu)
                self._readers[key] = easyocr.Reader([lang_code], gpu=use_gpu, verbose=False)
            return self._readers[key]

    def recognize(
        self,
        image: np.ndarray,
        language: str = "en",
        use_gpu: bool = False,
        page_number: int = 1,
        confidence_threshold: float = 0.0,
        **kwargs,
    ) -> OCRPage:
        self.ensure_available()
        lang_code = self.translate_language(language) or "en"

        try:
            reader = self._get_reader(lang_code, use_gpu)
            rgb_image = image if image.ndim == 2 else image[:, :, ::-1]
            detections = reader.readtext(rgb_image)
        except Exception as exc:  # noqa: BLE001
            raise OCREngineUnavailableError(f"EasyOCR failed: {exc}") from exc

        words: list[OCRWord] = []
        lines: list[str] = []
        confidences: list[float] = []
        for line_idx, (polygon, text, conf) in enumerate(detections):
            conf_pct = conf * 100
            if not text.strip() or conf_pct < confidence_threshold:
                continue
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            bbox = (int(min(xs)), int(min(ys)), int(max(xs) - min(xs)), int(max(ys) - min(ys)))
            words.append(OCRWord(text=text, confidence=conf_pct, bbox=bbox, line_number=line_idx))
            lines.append(text)
            confidences.append(conf_pct)

        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return OCRPage(
            page_number=page_number,
            text="\n".join(lines),
            words=words,
            mean_confidence=mean_conf,
            width=image.shape[1],
            height=image.shape[0],
        )
