"""Automated test suite for Focus and Blur Assessment on real retinal fundus images."""

from pathlib import Path
import pytest
import numpy as np

from image_quality.focus import (
    assess_focus,
    normalize_focus_score,
    classify_focus,
    compute_foreground_mask,
    extract_analysis_channel,
    ENGINEERING_BLURRY_THRESHOLD,
    ENGINEERING_SHARP_THRESHOLD,
)
from image_quality.io import load_raw_image

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "real_retinal_images"


def get_real_image_paths():
    """Retrieve all real retinal fundus images in data directory."""
    valid_exts = {".png", ".jpg", ".jpeg"}
    images = sorted([p for p in DATA_DIR.iterdir() if p.suffix.lower() in valid_exts])
    assert len(images) > 0, "No real retinal images found"
    return images


def test_real_dataset_count():
    """Verify test cohort contains all 9 real retinal images."""
    images = get_real_image_paths()
    assert len(images) == 9, f"Expected 9 real retinal images, found {len(images)}"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_assess_focus_returns_expected_structure(image_path: Path):
    """Verify assess_focus returns complete structured dictionary on all real images."""
    result = assess_focus(image_path)

    expected_keys = {
        "image_path",
        "raw_metric",
        "tenengrad_energy",
        "normalized_score",
        "decision",
        "diagnostics",
        "thresholds",
    }
    assert expected_keys.issubset(result.keys())

    # Check diagnostics sub-keys
    diag = result["diagnostics"]
    assert "channel_used" in diag
    assert "resolution_evaluated" in diag
    assert "foreground_pixels" in diag
    assert "total_pixels" in diag
    assert "foreground_fraction" in diag

    # Check thresholds metadata
    thresh = result["thresholds"]
    assert thresh["clinical_validation"] is False
    assert "engineering" in thresh["status"]


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_focus_metrics_numeric_validity(image_path: Path):
    """Verify all returned metrics are finite, non-negative, and not NaN/Inf."""
    result = assess_focus(image_path)

    raw_lap = result["raw_metric"]
    tenengrad = result["tenengrad_energy"]
    score = result["normalized_score"]

    assert isinstance(raw_lap, (int, float)) and np.isfinite(raw_lap)
    assert raw_lap > 0.0, f"Laplacian variance must be positive: {raw_lap}"

    assert isinstance(tenengrad, (int, float)) and np.isfinite(tenengrad)
    assert tenengrad > 0.0, f"Tenengrad energy must be positive: {tenengrad}"

    assert isinstance(score, (int, float)) and np.isfinite(score)
    assert 0.0 <= score <= 100.0, f"Normalized score {score} outside [0, 100]"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_focus_decision_consistency(image_path: Path):
    """Verify decision strictly aligns with normalized score against thresholds."""
    result = assess_focus(image_path)
    score = result["normalized_score"]
    decision = result["decision"]

    assert decision in {"Sharp", "Borderline", "Blurry"}

    if score >= ENGINEERING_SHARP_THRESHOLD:
        assert decision == "Sharp", f"Score {score} should be Sharp, got {decision}"
    elif score >= ENGINEERING_BLURRY_THRESHOLD:
        assert decision == "Borderline", f"Score {score} should be Borderline, got {decision}"
    else:
        assert decision == "Blurry", f"Score {score} should be Blurry, got {decision}"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_channel_support(image_path: Path):
    """Verify analysis works across green and gray channels."""
    res_green = assess_focus(image_path, channel="green")
    res_gray = assess_focus(image_path, channel="gray")

    assert res_green["diagnostics"]["channel_used"] == "green"
    assert res_gray["diagnostics"]["channel_used"] == "gray"
    assert res_green["raw_metric"] > 0
    assert res_gray["raw_metric"] > 0


def test_in_memory_numpy_array_input():
    """Verify assess_focus accepts in-memory NumPy RGB arrays."""
    sample_path = get_real_image_paths()[0]
    raw_arr = load_raw_image(sample_path)

    result = assess_focus(raw_arr)
    assert result["image_path"] == "in_memory_array"
    assert 0.0 <= result["normalized_score"] <= 100.0
    assert result["decision"] in {"Sharp", "Borderline", "Blurry"}


def test_normalization_bounds_and_monotonicity():
    """Verify normalization mapping properties across full theoretical spectrum."""
    assert normalize_focus_score(0.0) == 0.0
    assert normalize_focus_score(-10.0) == 0.0
    assert normalize_focus_score(100.0) == 50.0  # Default midpoint

    # Monotonicity check
    test_vals = [1.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 5000.0]
    scores = [normalize_focus_score(v) for v in test_vals]
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], f"Normalization not monotonic: {scores[i]} > {scores[i+1]}"


def test_classification_boundary_logic():
    """Verify classify_focus boundary conditions."""
    assert classify_focus(100.0) == "Sharp"
    assert classify_focus(50.0) == "Sharp"
    assert classify_focus(49.99) == "Borderline"
    assert classify_focus(25.0) == "Borderline"
    assert classify_focus(24.99) == "Blurry"
    assert classify_focus(0.0) == "Blurry"


def test_missing_image_file_raises():
    """Verify FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        assess_focus(DATA_DIR / "non_existent_retina_image_99999.png")


def test_invalid_channel_raises():
    """Verify ValueError on unsupported color channel."""
    sample_path = get_real_image_paths()[0]
    with pytest.raises(ValueError, match="Unsupported channel"):
        assess_focus(sample_path, channel="invalid_channel")


def test_invalid_image_shape_raises():
    """Verify ValueError on malformed array input."""
    invalid_2d = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
        assess_focus(invalid_2d)


def test_deterministic_reproducibility():
    """Verify repeated runs on the same real image yield identical bit-exact results."""
    sample_path = get_real_image_paths()[0]
    run1 = assess_focus(sample_path)
    run2 = assess_focus(sample_path)

    assert run1["raw_metric"] == run2["raw_metric"]
    assert run1["tenengrad_energy"] == run2["tenengrad_energy"]
    assert run1["normalized_score"] == run2["normalized_score"]
    assert run1["decision"] == run2["decision"]
