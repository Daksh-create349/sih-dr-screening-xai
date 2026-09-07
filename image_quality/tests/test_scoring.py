"""Automated tests for composite image quality scoring (image_quality.scoring).

Validates:
- Mathematical correctness of weighted composite score calculation
- Weight validation and constraint enforcement (sum to 1.0)
- Bounds validation [0.0, 100.0] and non-finite value handling
- Output data structure completeness and schema consistency
- In-memory NumPy array support
- Deterministic reproducibility on all real retinal images in data/real_retinal_images/
"""

from pathlib import Path
import pytest
import numpy as np

from image_quality.scoring import (
    compute_composite_score,
    score_image_quality,
    DEFAULT_WEIGHTS,
)
from image_quality.io import load_raw_image


DATA_DIR = Path("/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images")
REAL_IMAGE_FILES = sorted([f.name for f in DATA_DIR.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])


def test_default_weights_sum_to_one():
    """Verify that DEFAULT_WEIGHTS keys are valid and sum strictly to 1.0."""
    required = {"focus", "illumination", "fov", "centering"}
    assert set(DEFAULT_WEIGHTS.keys()) == required
    assert pytest.approx(sum(DEFAULT_WEIGHTS.values()), rel=1e-5) == 1.0
    for k, v in DEFAULT_WEIGHTS.items():
        assert 0.0 < v < 1.0


def test_compute_composite_score_deterministic_math():
    """Verify weighted score calculation using deterministic numeric inputs."""
    focus_mock = {"normalized_score": 80.0, "decision": "Sharp", "raw_metric": 120.0}
    illum_mock = {"overall_illumination_score": 70.0, "decision": "Well Illuminated", "mean_brightness": 110.0}
    fov_mock = {
        "fov_score": 90.0,
        "centering_score": 85.0,
        "fov_decision": "Adequate FOV",
        "centering_decision": "Well Centered",
        "coverage_pct": 82.0,
        "radial_center_offset": 0.04,
        "optic_disc": {"detected": True, "confidence": 0.85},
    }

    # Expected: 0.40 * 80.0 + 0.30 * 70.0 + 0.20 * 90.0 + 0.10 * 85.0
    # = 32.0 + 21.0 + 18.0 + 8.5 = 79.5
    result = compute_composite_score(focus_mock, illum_mock, fov_mock)
    assert pytest.approx(result["composite_score"], abs=0.01) == 79.50
    assert result["component_scores"]["focus_score"] == 80.0
    assert result["component_scores"]["illumination_score"] == 70.0
    assert result["component_scores"]["fov_score"] == 90.0
    assert result["component_scores"]["centering_score"] == 85.0
    assert result["sub_decisions"]["focus_decision"] == "Sharp"
    assert result["sub_decisions"]["illumination_decision"] == "Well Illuminated"
    assert result["diagnostics"]["optic_disc_confidence"] == 0.85
    assert result["diagnostics"]["optic_disc_detected"] is True


def test_custom_weights_support():
    """Verify custom weight configuration is respected."""
    focus_mock = {"normalized_score": 100.0}
    illum_mock = {"overall_illumination_score": 0.0}
    fov_mock = {"fov_score": 0.0, "centering_score": 0.0}

    custom_w = {"focus": 0.70, "illumination": 0.10, "fov": 0.10, "centering": 0.10}
    res = compute_composite_score(focus_mock, illum_mock, fov_mock, weights=custom_w)
    assert pytest.approx(res["composite_score"], abs=0.01) == 70.0


def test_invalid_weights_raise_error():
    """Verify weights that do not sum to 1.0 or have missing keys raise ValueError."""
    focus_mock = {"normalized_score": 50.0}
    illum_mock = {"overall_illumination_score": 50.0}
    fov_mock = {"fov_score": 50.0, "centering_score": 50.0}

    # Weights don't sum to 1.0
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        compute_composite_score(focus_mock, illum_mock, fov_mock, weights={"focus": 0.5, "illumination": 0.2, "fov": 0.1, "centering": 0.1})

    # Missing required key
    with pytest.raises(ValueError, match="Missing required weight keys"):
        compute_composite_score(focus_mock, illum_mock, fov_mock, weights={"focus": 0.5, "illumination": 0.5})


def test_invalid_component_scores_raise_error():
    """Verify component scores outside [0.0, 100.0] or non-finite values raise ValueError."""
    illum_mock = {"overall_illumination_score": 50.0}
    fov_mock = {"fov_score": 50.0, "centering_score": 50.0}

    with pytest.raises(ValueError, match="within"):
        compute_composite_score({"normalized_score": 120.0}, illum_mock, fov_mock)

    with pytest.raises(ValueError, match="within"):
        compute_composite_score({"normalized_score": -5.0}, illum_mock, fov_mock)

    with pytest.raises(ValueError, match="finite"):
        compute_composite_score({"normalized_score": float("nan")}, illum_mock, fov_mock)


def test_in_memory_numpy_array_support():
    """Verify score_image_quality runs seamlessly on loaded RGB NumPy arrays."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    img_rgb = load_raw_image(img_path)
    res = score_image_quality(img_rgb)

    assert "composite_score" in res
    assert 0.0 <= res["composite_score"] <= 100.0
    assert res["image_path"] == "in_memory_array"


@pytest.mark.parametrize("filename", REAL_IMAGE_FILES)
def test_real_image_composite_scoring_end_to_end(filename):
    """Verify all 9 real retinal images produce valid, bounded composite scores."""
    img_path = DATA_DIR / filename
    res = score_image_quality(img_path)

    # Validate output structure
    assert "composite_score" in res
    assert "component_scores" in res
    assert "weights" in res
    assert "sub_decisions" in res
    assert "diagnostics" in res
    assert "focus_assessment" in res
    assert "illumination_assessment" in res
    assert "fov_assessment" in res

    # Validate bounds
    score = res["composite_score"]
    assert np.isfinite(score)
    assert 0.0 <= score <= 100.0

    comp = res["component_scores"]
    for k in ["focus_score", "illumination_score", "fov_score", "centering_score"]:
        assert k in comp
        assert np.isfinite(comp[k])
        assert 0.0 <= comp[k] <= 100.0


def test_deterministic_scoring_reproducibility():
    """Verify identical inputs yield strictly identical composite scores."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    res1 = score_image_quality(img_path)
    res2 = score_image_quality(img_path)
    assert res1["composite_score"] == res2["composite_score"]
    assert res1["component_scores"] == res2["component_scores"]
