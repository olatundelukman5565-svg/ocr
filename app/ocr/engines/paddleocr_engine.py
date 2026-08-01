"""PaddleOCR engine wrapper.

PaddleOCR provides strong multilingual detection/recognition, including
solid CJK support, and can run on GPU or CPU. The ``paddleocr`` /
``paddlepaddle`` packages are imported lazily since they are large,
optional dependencies.
"""
from __future__ import annotations

import logging
import threading

import numpy as np

from app.core.models import OCRPage, OCRWord
from app.ocr.base_engine import OCREngine, OCREngineUnavailableError

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR

    _IMPORT_OK = True
except ImportError:  # pragma: no cover
    _IMPORT_OK = False


class PaddleOCREngine(OCREngine):
    name = "paddleocr"
    display_name = "PaddleOCR"
    supports_gpu = True

    LANGUAGE_MAP = {
        "en": "en", "fr": "fr", "de": "german", "es": "es", "it": "it",
        "pt": "pt", "nl": "nl", "zh": "ch", "ja": "japan", "ko": "korean",
        "ar": "ar", "hi": "hi", "tr": "tr", "ru": "ru", "th": "th", "vi": "vi",
    }

    def __init__(self) -> None:
        self._instances: dict[tuple[str, bool], "PaddleOCR"] = {}
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return _IMPORT_OK

    def supported_languages(self) -> dict[str, str]:
        return dict(self.LANGUAGE_MAP)

    def _get_instance(self, lang_code: str, use_gpu: bool) -> "PaddleOCR":
        key = (lang_code, use_gpu)
        with self._lock:
            if key not in self._instances:
                logger.info("Initializing PaddleOCR for lang=%s gpu=%s", lang_code, use_gpu)
                self._instances[key] = PaddleOCR(use_angle_cls=True, lang=lang_code, use_gpu=use_gpu, show_log=False)
            return self._instances[key]

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
            engine = self._get_instance(lang_code, use_gpu)
            bgr_image = image if image.ndim == 2 else image
            raw_result = engine.ocr(bgr_image, cls=True)
        except Exception as exc:  # noqa: BLE001
            raise OCREngineUnavailableError(f"PaddleOCR failed: {exc}") from exc

        words: list[OCRWord] = []
        lines: list[str] = []
        confidences: list[float] = []
        detections = raw_result[0] if raw_result and raw_result[0] else []
        for line_idx, detection in enumerate(detections):
            polygon, (text, conf) = detection
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
