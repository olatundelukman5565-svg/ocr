"""OpenCV-based image preprocessing pipeline for maximizing OCR accuracy.

Each transform is a small, independently testable static method on
:class:`ImagePreprocessor`. :meth:`ImagePreprocessor.preprocess_pipeline`
composes them according to an options dict (as produced by the OCR
Settings panel) or an :class:`~app.core.models.OCRMode` preset.

All methods accept and return ``numpy.ndarray`` images in BGR (OpenCV's
native order) or single-channel grayscale, so the pipeline can be used
identically from the UI, the batch processor, and unit tests.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingOptions:
    """Flags controlling which stages :meth:`preprocess_pipeline` runs."""

    grayscale: bool = True
    remove_shadows: bool = False
    denoise: bool = False
    deskew: bool = False
    perspective_correction: bool = False
    clahe_contrast: bool = False
    sharpen: bool = False
    adaptive_threshold: bool = False
    upscale: bool = False
    upscale_factor: float = 2.0

    @classmethod
    def for_mode(cls, mode: str) -> "PreprocessingOptions":
        """Return a sensible preset for a named OCR mode."""
        presets = {
            "fast": cls(grayscale=True),
            "balanced": cls(grayscale=True, denoise=True, deskew=True, clahe_contrast=True),
            "high_accuracy": cls(
                grayscale=True,
                remove_shadows=True,
                denoise=True,
                deskew=True,
                clahe_contrast=True,
                sharpen=True,
                adaptive_threshold=True,
            ),
            "ai_enhanced": cls(
                grayscale=True,
                remove_shadows=True,
                denoise=True,
                deskew=True,
                perspective_correction=True,
                clahe_contrast=True,
                sharpen=True,
                adaptive_threshold=True,
                upscale=True,
            ),
        }
        return presets.get(mode, cls())


@dataclass
class PreprocessingResult:
    image: np.ndarray
    skew_angle_corrected: float = 0.0
    perspective_corrected: bool = False
    stages_applied: list = field(default_factory=list)


class ImagePreprocessor:
    """Stateless collection of OpenCV image-enhancement operations."""

    # -- basic conversions ---------------------------------------------------
    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def to_bgr(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    # -- denoising -------------------------------------------------------------
    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    # -- shadow / background removal --------------------------------------------
    @staticmethod
    def remove_shadows(image: np.ndarray) -> np.ndarray:
        """Estimate and divide out uneven illumination using morphological dilation."""
        is_gray = image.ndim == 2
        channels = [image] if is_gray else cv2.split(image)
        result_channels = []
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        for channel in channels:
            dilated = cv2.dilate(channel, kernel)
            bg = cv2.medianBlur(dilated, 21)
            diff = 255 - cv2.absdiff(channel, bg)
            norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
            result_channels.append(norm)
        return result_channels[0] if is_gray else cv2.merge(result_channels)

    # -- contrast ----------------------------------------------------------------
    @staticmethod
    def enhance_contrast_clahe(image: np.ndarray, clip_limit: float = 2.5, tile_grid_size: int = 8) -> np.ndarray:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
        if image.ndim == 2:
            return clahe.apply(image)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_channel = clahe.apply(l_channel)
        merged = cv2.merge((l_channel, a_channel, b_channel))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    # -- sharpening ------------------------------------------------------------
    @staticmethod
    def sharpen(image: np.ndarray, amount: float = 1.0) -> np.ndarray:
        """Unsharp mask: sharpened = original + amount * (original - blurred)."""
        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
        return cv2.addWeighted(image, 1 + amount, blurred, -amount, 0)

    # -- thresholding / binarization ----------------------------------------------
    @staticmethod
    def adaptive_threshold(image: np.ndarray, block_size: int = 31, c: int = 15) -> np.ndarray:
        gray = ImagePreprocessor.to_grayscale(image)
        if block_size % 2 == 0:
            block_size += 1
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
        )

    @staticmethod
    def otsu_binarize(image: np.ndarray) -> np.ndarray:
        gray = ImagePreprocessor.to_grayscale(image)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    # -- geometric correction -----------------------------------------------------
    @staticmethod
    def detect_skew_angle(image: np.ndarray) -> float:
        """Estimate the dominant text skew angle in degrees via minAreaRect."""
        gray = ImagePreprocessor.to_grayscale(image)
        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if coords.shape[0] < 20:
            return 0.0
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        # Guard against nonsensical corrections on near-blank/noisy images.
        if abs(angle) > 45:
            return 0.0
        return float(angle)

    @staticmethod
    def rotate(image: np.ndarray, angle: float) -> np.ndarray:
        if abs(angle) < 0.05:
            return image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        border_value = 255 if image.ndim == 2 else (255, 255, 255)
        return cv2.warpAffine(
            image, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=border_value
        )

    @staticmethod
    def deskew(image: np.ndarray) -> tuple[np.ndarray, float]:
        angle = ImagePreprocessor.detect_skew_angle(image)
        return ImagePreprocessor.rotate(image, angle), angle

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    @staticmethod
    def detect_document_contour(image: np.ndarray) -> Optional[np.ndarray]:
        """Find the largest quadrilateral contour, assumed to be the document edge."""
        gray = ImagePreprocessor.to_grayscale(image)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        edges = cv2.dilate(edges, None, iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        image_area = image.shape[0] * image.shape[1]
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(approx) > 0.2 * image_area:
                return approx.reshape(4, 2)
        return None

    @staticmethod
    def correct_perspective(image: np.ndarray) -> tuple[np.ndarray, bool]:
        """Warp a photographed document to a top-down view if a quad boundary is found."""
        quad = ImagePreprocessor.detect_document_contour(image)
        if quad is None:
            return image, False
        rect = ImagePreprocessor._order_points(quad.astype("float32"))
        (tl, tr, br, bl) = rect
        width_a = np.linalg.norm(br - bl)
        width_b = np.linalg.norm(tr - tl)
        max_width = max(int(width_a), int(width_b))
        height_a = np.linalg.norm(tr - br)
        height_b = np.linalg.norm(tl - bl)
        max_height = max(int(height_a), int(height_b))
        if max_width < 10 or max_height < 10:
            return image, False
        dst = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]], dtype="float32"
        )
        matrix = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
        return warped, True

    @staticmethod
    def upscale(image: np.ndarray, factor: float = 2.0) -> np.ndarray:
        h, w = image.shape[:2]
        return cv2.resize(image, (int(w * factor), int(h * factor)), interpolation=cv2.INTER_CUBIC)

    # -- pipeline composer ---------------------------------------------------------
    @staticmethod
    def preprocess_pipeline(image: np.ndarray, options: PreprocessingOptions) -> PreprocessingResult:
        """Run the requested stages in an accuracy-optimized order.

        Order matters: geometric correction happens before binarization so
        threshold decisions are made on a properly aligned image, and
        contrast/denoise happen before sharpening to avoid amplifying noise.
        """
        result = PreprocessingResult(image=image.copy())
        stages = result.stages_applied

        if options.perspective_correction:
            result.image, corrected = ImagePreprocessor.correct_perspective(result.image)
            result.perspective_corrected = corrected
            if corrected:
                stages.append("perspective_correction")

        if options.remove_shadows:
            result.image = ImagePreprocessor.remove_shadows(result.image)
            stages.append("remove_shadows")

        if options.deskew:
            result.image, angle = ImagePreprocessor.deskew(result.image)
            result.skew_angle_corrected = angle
            stages.append(f"deskew({angle:.2f} deg)")

        if options.grayscale:
            result.image = ImagePreprocessor.to_grayscale(result.image)
            stages.append("grayscale")

        if options.denoise:
            result.image = ImagePreprocessor.denoise(result.image)
            stages.append("denoise")

        if options.clahe_contrast:
            result.image = ImagePreprocessor.enhance_contrast_clahe(result.image)
            stages.append("clahe_contrast")

        if options.upscale:
            result.image = ImagePreprocessor.upscale(result.image, options.upscale_factor)
            stages.append(f"upscale(x{options.upscale_factor})")

        if options.sharpen:
            result.image = ImagePreprocessor.sharpen(result.image)
            stages.append("sharpen")

        if options.adaptive_threshold:
            result.image = ImagePreprocessor.adaptive_threshold(result.image)
            stages.append("adaptive_threshold")

        logger.debug("Preprocessing pipeline applied: %s", stages)
        return result
