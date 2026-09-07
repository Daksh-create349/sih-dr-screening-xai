"""Automated tests for classifier input preprocessing."""

from pathlib import Path
import numpy as np
import pytest

from classifier.preprocessing import (
    crop_retinal_borders,
    preprocess_classifier_image,
    prepare_input_tensor,
    prepare_batch_tensors,
    TARGET_IMAGE_SIZE,
)

SAMPLE_REAL_IMAGE: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "real_retinal_images"
    / "confirmed_grade4_proliferative.jpg"
)


def test_crop_retinal_borders_numeric_fixture():
    """Verify border cropping removes black margin from numeric fixture."""
    # Create 100x100 black image with 40x40 bright square at [30:70, 30:70]
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[30:70, 30:70] = 150

    cropped = crop_retinal_borders(img, tol=10)
    assert cropped.shape == (40, 40, 3)
    assert np.all(cropped == 150)


def test_crop_retinal_borders_no_crop_when_full():
    """Verify image without black borders remains unchanged."""
    img = np.full((100, 100, 3), 120, dtype=np.uint8)
    cropped = crop_retinal_borders(img, tol=10)
    assert cropped.shape == (100, 100, 3)


def test_preprocess_classifier_image_real_retinal_image():
    """Verify preprocessing of real retinal image produces exact shape, dtype, and range."""
    assert SAMPLE_REAL_IMAGE.exists(), f"Missing real image at {SAMPLE_REAL_IMAGE}"

    processed = preprocess_classifier_image(SAMPLE_REAL_IMAGE)

    # Resolution: (384, 384, 3)
    assert processed.shape == (384, 384, 3)
    # Datatype: float32
    assert processed.dtype == np.float32
    # Intensity range: within [0.0, 255.0]
    assert np.min(processed) >= 0.0
    assert np.max(processed) <= 255.0
    # Must NOT be divided by 255.0 (EfficientNet has internal normalization)
    assert np.max(processed) > 1.0, "Input was incorrectly normalized to [0, 1]; model expects [0, 255]"


def test_prepare_input_tensor():
    """Verify single-image tensor preparation expands batch dimension to (1, 384, 384, 3)."""
    tensor = prepare_input_tensor(SAMPLE_REAL_IMAGE)
    assert tensor.shape == (1, 384, 384, 3)
    assert tensor.dtype == np.float32


def test_prepare_batch_tensors():
    """Verify batch tensor preparation stacks multiple inputs into (N, 384, 384, 3)."""
    items = [SAMPLE_REAL_IMAGE, SAMPLE_REAL_IMAGE]
    batch = prepare_batch_tensors(items)
    assert batch.shape == (2, 384, 384, 3)
    assert batch.dtype == np.float32


def test_prepare_batch_tensors_empty_raises():
    """Verify empty batch list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot prepare batch tensor from empty list"):
        prepare_batch_tensors([])


def test_preprocess_invalid_channels_raises():
    """Verify single-channel or 4-channel arrays raise ValueError."""
    gray = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
        preprocess_classifier_image(gray)

    rgba = np.zeros((100, 100, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
        preprocess_classifier_image(rgba)


def test_preprocess_invalid_type_raises():
    """Verify non-path non-array input raises TypeError."""
    with pytest.raises(TypeError, match="Expected file path or np.ndarray"):
        preprocess_classifier_image(12345)
