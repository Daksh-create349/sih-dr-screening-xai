"""Automated test suite for Field of View (FOV), Centering, and Optic Disc localization."""

from pathlib import Path
import pytest
import numpy as np

from image_quality.field_of_view import (
    assess_field_of_view,
    detect_retinal_field,
    estimate_retinal_center,
    locate_optic_disc_candidate,
    classify_fov_and_centering,
    ENGINEERING_POOR_FOV_THRESHOLD,
    ENGINEERING_ADEQUATE_FOV_THRESHOLD,
    ENGINEERING_WELL_CENTERED_MAX_OFFSET,
    ENGINEERING_POOR_CENTERED_MIN_OFFSET,
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
def test_assess_field_of_view_returns_expected_structure(image_path: Path):
    """Verify assess_field_of_view returns complete structured dictionary on all real images."""
    result = assess_field_of_view(image_path)

    expected_keys = {
        "image_path",
        "image_dimensions",
        "retinal_foreground_area",
        "coverage_pct",
        "bounding_box",
        "aspect_ratio",
        "retinal_center",
        "image_center",
        "normalized_horizontal_offset",
        "normalized_vertical_offset",
        "radial_center_offset",
        "fov_score",
        "centering_score",
        "optic_disc",
        "fov_decision",
        "centering_decision",
        "diagnostics",
        "thresholds",
    }
    assert expected_keys.issubset(result.keys())

    # Check bounding box
    bbox = result["bounding_box"]
    assert len(bbox) == 4
    assert bbox[2] > 0 and bbox[3] > 0

    # Check dimensions
    dims = result["image_dimensions"]
    assert len(dims) == 2 and dims[0] > 0 and dims[1] > 0

    # Check centers
    rc = result["retinal_center"]
    ic = result["image_center"]
    assert len(rc) == 2 and len(ic) == 2

    # Check thresholds metadata
    thresh = result["thresholds"]
    assert thresh["clinical_validation"] is False
    assert "engineering" in thresh["status"]


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_fov_numeric_validity_and_bounds(image_path: Path):
    """Verify all returned FOV and centering metrics are finite, non-NaN, and properly bounded."""
    result = assess_field_of_view(image_path)

    area = result["retinal_foreground_area"]
    cov = result["coverage_pct"]
    aspect = result["aspect_ratio"]
    dx = result["normalized_horizontal_offset"]
    dy = result["normalized_vertical_offset"]
    rad_offset = result["radial_center_offset"]
    fov_score = result["fov_score"]
    center_score = result["centering_score"]

    for val, name in [
        (area, "retinal_foreground_area"),
        (cov, "coverage_pct"),
        (aspect, "aspect_ratio"),
        (dx, "normalized_horizontal_offset"),
        (dy, "normalized_vertical_offset"),
        (rad_offset, "radial_center_offset"),
        (fov_score, "fov_score"),
        (center_score, "centering_score"),
    ]:
        assert isinstance(val, (int, float)) and np.isfinite(val), f"{name} not finite: {val}"

    assert area > 0, "Retinal foreground area must be positive"
    assert 0.0 <= cov <= 100.0, f"Coverage {cov} out of [0, 100]"
    assert 0.0 <= fov_score <= 100.0, f"FOV score {fov_score} out of [0, 100]"
    assert 0.0 <= center_score <= 100.0, f"Centering score {center_score} out of [0, 100]"
    assert rad_offset >= 0.0, f"Radial offset {rad_offset} must be non-negative"
    assert aspect > 0.0, f"Aspect ratio {aspect} must be positive"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_fov_decisions_validity_and_consistency(image_path: Path):
    """Verify FOV and Centering decisions belong to documented set and match metrics."""
    result = assess_field_of_view(image_path)

    fov_dec = result["fov_decision"]
    center_dec = result["centering_decision"]
    fov_score = result["fov_score"]
    offset = result["radial_center_offset"]

    assert fov_dec in {"Adequate FOV", "Borderline FOV", "Poor FOV"}
    assert center_dec in {"Well Centered", "Borderline Centering", "Poor Centering"}

    if fov_score >= ENGINEERING_ADEQUATE_FOV_THRESHOLD:
        assert fov_dec == "Adequate FOV"
    elif fov_score >= ENGINEERING_POOR_FOV_THRESHOLD:
        assert fov_dec == "Borderline FOV"
    else:
        assert fov_dec == "Poor FOV"

    if offset <= ENGINEERING_WELL_CENTERED_MAX_OFFSET:
        assert center_dec == "Well Centered"
    elif offset <= ENGINEERING_POOR_CENTERED_MIN_OFFSET:
        assert center_dec == "Borderline Centering"
    else:
        assert center_dec == "Poor Centering"


@pytest.mark.parametrize("image_path", get_real_image_paths(), ids=lambda p: p.name)
def test_optic_disc_candidate_localization_structure(image_path: Path):
    """Verify optic disc candidate returns complete schema with valid confidence."""
    result = assess_field_of_view(image_path)
    disc = result["optic_disc"]

    assert "detected" in disc
    assert "confidence" in disc
    assert "is_reliable" in disc
    assert isinstance(disc["detected"], bool)
    assert 0.0 <= disc["confidence"] <= 1.0

    if disc["detected"]:
        assert len(disc["center"]) == 2
        assert disc["radius"] > 0
        w, h = result["image_dimensions"]
        dc_x, dc_y = disc["center"]
        assert 0 <= dc_x <= w and 0 <= dc_y <= h


def test_in_memory_numpy_array_input():
    """Verify assess_field_of_view accepts in-memory NumPy RGB arrays."""
    sample_path = get_real_image_paths()[0]
    raw_arr = load_raw_image(sample_path)

    result = assess_field_of_view(raw_arr)
    assert result["image_path"] == "in_memory_array"
    assert 0.0 <= result["fov_score"] <= 100.0
    assert 0.0 <= result["centering_score"] <= 100.0
    assert result["fov_decision"] in {"Adequate FOV", "Borderline FOV", "Poor FOV"}
    assert result["centering_decision"] in {"Well Centered", "Borderline Centering", "Poor Centering"}


def test_centering_offset_calculation():
    """Verify estimate_retinal_center correctly handles centered and shifted masks."""
    # Perfectly centered circular mask
    mask_centered = np.zeros((100, 100), dtype=bool)
    y, x = np.ogrid[:100, :100]
    mask_centered[(y - 50) ** 2 + (x - 50) ** 2 <= 30 ** 2] = True

    res_centered = estimate_retinal_center(mask_centered, (100, 100))
    assert res_centered["retinal_center"] == [50.0, 50.0]
    assert res_centered["radial_center_offset"] == 0.0
    assert res_centered["centering_score"] == 100.0

    # Shifted mask (shifted to right by 20 px)
    mask_shifted = np.zeros((100, 100), dtype=bool)
    mask_shifted[(y - 50) ** 2 + (x - 70) ** 2 <= 20 ** 2] = True

    res_shifted = estimate_retinal_center(mask_shifted, (100, 100))
    assert res_shifted["retinal_center"] == [70.0, 50.0]
    assert res_shifted["normalized_horizontal_offset"] == pytest.approx(0.40, rel=1e-2)
    assert res_shifted["centering_score"] < 100.0


def test_classification_logic():
    """Verify boundary cases in classify_fov_and_centering."""
    fov_dec, center_dec = classify_fov_and_centering(80.0, 0.02)
    assert fov_dec == "Adequate FOV" and center_dec == "Well Centered"

    fov_dec, center_dec = classify_fov_and_centering(60.0, 0.12)
    assert fov_dec == "Borderline FOV" and center_dec == "Borderline Centering"

    fov_dec, center_dec = classify_fov_and_centering(30.0, 0.35)
    assert fov_dec == "Poor FOV" and center_dec == "Poor Centering"


def test_missing_image_file_raises():
    """Verify FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        assess_field_of_view(DATA_DIR / "non_existent_fundus_image_7777.png")


def test_invalid_image_shape_raises():
    """Verify ValueError on malformed array input."""
    invalid_2d = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
        assess_field_of_view(invalid_2d)


def test_deterministic_reproducibility():
    """Verify repeated runs on the same real image produce identical values."""
    sample_path = get_real_image_paths()[0]
    run1 = assess_field_of_view(sample_path)
    run2 = assess_field_of_view(sample_path)

    assert run1["fov_score"] == run2["fov_score"]
    assert run1["centering_score"] == run2["centering_score"]
    assert run1["coverage_pct"] == run2["coverage_pct"]
    assert run1["radial_center_offset"] == run2["radial_center_offset"]
    assert run1["retinal_center"] == run2["retinal_center"]
    assert run1["fov_decision"] == run2["fov_decision"]
    assert run1["centering_decision"] == run2["centering_decision"]
