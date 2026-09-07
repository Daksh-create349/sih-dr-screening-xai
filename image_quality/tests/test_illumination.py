"""Automated test suite for Illumination and Exposure Assessment on real retinal fundus images."""

from pathlib import Path
import pytest
import numpy as np

from image_quality.illumination import (
    assess_illumination,
    compute_brightness_statistics,
    compute_regional_illumination,
    compute_exposure_score,
    compute_uniformity_score,
    classify_illumination,
    ENGINEERING_POOR_THRESHOLD,
    ENGINEERING_WELL_THRESHOLD,
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
def test_assess_illumination_returns_expected_structure(image_path: Path):
    """Verify assess_illumination returns complete structured dictionary on all real images."""
    result = assess_illumination(image_path)

    expected_keys = {
        "image_path",
        "exposure_score",
        "uniformity_score",
        "overall_illumination_score",
        "dark_pixel_pct",
        "bright_pixel_pct",
        "mean_brightness",
        "median_brightness",
        "regional_statistics",
        "decision",
        "diagnostics",
        "thresholds",
    }
    assert expected_keys.issubset(result.keys())

    # Check regional sub-keys
    reg = result["regional_statistics"]
    assert "quadrant_means" in reg
    assert len(reg["quadrant_means"]) == 4
    assert "quadrant_imbalance" in reg
    assert "center_mean" in reg
    assert "periphery_mean" in reg
    assert "center_periphery_ratio" in reg

    # Check thresholds metadata
    thresh = result["thresholds"]
    assert thresh["clinical_validation"] is False
    assert "engineering" in thresh["status"]


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_illumination_numeric_validity_and_bounds(image_path: Path):
    """Verify all returned illumination metrics are finite, not NaN/Inf, and properly bounded."""
    result = assess_illumination(image_path)

    e_score = result["exposure_score"]
    u_score = result["uniformity_score"]
    overall = result["overall_illumination_score"]
    dark_pct = result["dark_pixel_pct"]
    bright_pct = result["bright_pixel_pct"]
    mean_b = result["mean_brightness"]
    med_b = result["median_brightness"]

    # Finiteness checks
    for val, name in [
        (e_score, "exposure_score"),
        (u_score, "uniformity_score"),
        (overall, "overall_illumination_score"),
        (dark_pct, "dark_pixel_pct"),
        (bright_pct, "bright_pixel_pct"),
        (mean_b, "mean_brightness"),
        (med_b, "median_brightness"),
    ]:
        assert isinstance(val, (int, float)) and np.isfinite(val), f"{name} not finite: {val}"

    # Range checks
    assert 0.0 <= e_score <= 100.0, f"Exposure score {e_score} out of [0, 100]"
    assert 0.0 <= u_score <= 100.0, f"Uniformity score {u_score} out of [0, 100]"
    assert 0.0 <= overall <= 100.0, f"Overall score {overall} out of [0, 100]"
    assert 0.0 <= dark_pct <= 100.0, f"Dark percentage {dark_pct} out of [0, 100]"
    assert 0.0 <= bright_pct <= 100.0, f"Bright percentage {bright_pct} out of [0, 100]"
    assert 0.0 <= mean_b <= 255.0, f"Mean brightness {mean_b} out of [0, 255]"
    assert 0.0 <= med_b <= 255.0, f"Median brightness {med_b} out of [0, 255]"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_illumination_decision_consistency(image_path: Path):
    """Verify decision strictly aligns with overall score and clipping sanity rules."""
    result = assess_illumination(image_path)
    overall = result["overall_illumination_score"]
    decision = result["decision"]
    dark_pct = result["dark_pixel_pct"]
    bright_pct = result["bright_pixel_pct"]

    assert decision in {"Well Illuminated", "Borderline Illumination", "Poor Illumination"}

    if dark_pct >= 20.0 or bright_pct >= 15.0 or overall < ENGINEERING_POOR_THRESHOLD:
        assert decision == "Poor Illumination"
    elif overall >= ENGINEERING_WELL_THRESHOLD:
        assert decision == "Well Illuminated"
    else:
        assert decision == "Borderline Illumination"


def test_in_memory_numpy_array_input():
    """Verify assess_illumination accepts in-memory NumPy RGB arrays."""
    sample_path = get_real_image_paths()[0]
    raw_arr = load_raw_image(sample_path)

    result = assess_illumination(raw_arr)
    assert result["image_path"] == "in_memory_array"
    assert 0.0 <= result["overall_illumination_score"] <= 100.0
    assert result["decision"] in {"Well Illuminated", "Borderline Illumination", "Poor Illumination"}


def test_exposure_score_penalty_on_extremes():
    """Verify exposure score properly penalizes dark or over-saturated conditions."""
    normal_score = compute_exposure_score(mean_val=115.0, dark_pct=0.0, bright_pct=0.0)
    assert normal_score == 100.0

    # Very dark image
    dark_score = compute_exposure_score(mean_val=20.0, dark_pct=50.0, bright_pct=0.0)
    assert dark_score < 20.0

    # Very bright/saturated image
    bright_score = compute_exposure_score(mean_val=240.0, dark_pct=0.0, bright_pct=40.0)
    assert bright_score < 20.0


def test_uniformity_score_penalty_on_imbalance():
    """Verify uniformity score properly reflects spatial variance."""
    uniform_score = compute_uniformity_score(std_val=5.0, mean_val=100.0, quadrant_imbalance=0.02)
    assert uniform_score > 90.0

    imbalanced_score = compute_uniformity_score(std_val=40.0, mean_val=100.0, quadrant_imbalance=0.50)
    assert imbalanced_score < uniform_score


def test_classification_logic():
    """Verify classify_illumination boundary rules."""
    assert classify_illumination(75.0, dark_pct=1.0, bright_pct=1.0) == "Well Illuminated"
    assert classify_illumination(65.0, dark_pct=0.0, bright_pct=0.0) == "Well Illuminated"
    assert classify_illumination(64.9, dark_pct=0.0, bright_pct=0.0) == "Borderline Illumination"
    assert classify_illumination(45.0, dark_pct=0.0, bright_pct=0.0) == "Borderline Illumination"
    assert classify_illumination(44.9, dark_pct=0.0, bright_pct=0.0) == "Poor Illumination"
    # Severe clipping overrides to Poor
    assert classify_illumination(80.0, dark_pct=25.0, bright_pct=0.0) == "Poor Illumination"
    assert classify_illumination(80.0, dark_pct=0.0, bright_pct=18.0) == "Poor Illumination"


def test_missing_image_file_raises():
    """Verify FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        assess_illumination(DATA_DIR / "non_existent_fundus_image_8888.png")


def test_invalid_image_shape_raises():
    """Verify ValueError on malformed array input."""
    invalid_2d = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
        assess_illumination(invalid_2d)


def test_deterministic_reproducibility():
    """Verify repeated runs on the same real image produce identical values."""
    sample_path = get_real_image_paths()[0]
    run1 = assess_illumination(sample_path)
    run2 = assess_illumination(sample_path)

    assert run1["exposure_score"] == run2["exposure_score"]
    assert run1["uniformity_score"] == run2["uniformity_score"]
    assert run1["overall_illumination_score"] == run2["overall_illumination_score"]
    assert run1["decision"] == run2["decision"]
