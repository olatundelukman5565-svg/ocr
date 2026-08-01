from __future__ import annotations

import cv2
import numpy as np

from app.utils.image_preprocessing import ImagePreprocessor, PreprocessingOptions


def test_to_grayscale_reduces_channels(white_image):
    gray = ImagePreprocessor.to_grayscale(white_image)
    assert gray.ndim == 2
    assert gray.shape == white_image.shape[:2]


def test_to_grayscale_is_idempotent(noisy_gray_image):
    result = ImagePreprocessor.to_grayscale(noisy_gray_image)
    assert np.array_equal(result, noisy_gray_image)


def test_clahe_contrast_preserves_shape(white_image):
    result = ImagePreprocessor.enhance_contrast_clahe(white_image)
    assert result.shape == white_image.shape


def test_adaptive_threshold_returns_binary_image(noisy_gray_image):
    result = ImagePreprocessor.adaptive_threshold(noisy_gray_image)
    unique_values = set(np.unique(result).tolist())
    assert unique_values <= {0, 255}


def test_otsu_binarize_returns_binary_image(noisy_gray_image):
    result = ImagePreprocessor.otsu_binarize(noisy_gray_image)
    unique_values = set(np.unique(result).tolist())
    assert unique_values <= {0, 255}


def test_rotate_zero_degrees_is_noop(white_image):
    result = ImagePreprocessor.rotate(white_image, 0.0)
    assert np.array_equal(result, white_image)


def test_deskew_detects_and_corrects_known_angle():
    canvas = np.full((400, 400), 255, dtype=np.uint8)
    cv2.putText(canvas, "HELLO WORLD SAMPLE TEXT", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, 0, 2)
    center = (200, 200)
    matrix = cv2.getRotationMatrix2D(center, 12, 1.0)
    rotated = cv2.warpAffine(canvas, matrix, (400, 400), borderValue=255)

    _, detected_angle = ImagePreprocessor.deskew(rotated)
    assert abs(detected_angle - 12) < 5 or abs(detected_angle + 12) < 5 or abs(detected_angle) < 5


def test_preprocessing_options_presets_differ():
    fast = PreprocessingOptions.for_mode("fast")
    high_accuracy = PreprocessingOptions.for_mode("high_accuracy")
    assert fast.denoise is False
    assert high_accuracy.denoise is True
    assert high_accuracy.adaptive_threshold is True


def test_preprocess_pipeline_runs_all_requested_stages(white_image):
    options = PreprocessingOptions(
        grayscale=True, denoise=True, clahe_contrast=True, sharpen=True, adaptive_threshold=True
    )
    result = ImagePreprocessor.preprocess_pipeline(white_image, options)
    assert result.image is not None
    assert "grayscale" in result.stages_applied
    assert "adaptive_threshold" in result.stages_applied


def test_upscale_increases_dimensions(white_image):
    upscaled = ImagePreprocessor.upscale(white_image, factor=2.0)
    assert upscaled.shape[0] == white_image.shape[0] * 2
    assert upscaled.shape[1] == white_image.shape[1] * 2
