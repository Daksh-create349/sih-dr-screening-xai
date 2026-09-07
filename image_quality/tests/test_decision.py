"""Automated tests for quality classification and screening decisions (image_quality.decision).

Validates:
- Quality gate triggering mechanics (severe blur, underexposure, truncation, soft focus)
- Decision hierarchy: UNGRADEABLE gates override high composite scores
- Decision hierarchy: BORDERLINE gates override high composite scores
- Valid classification categories strictly restricted to {"GOOD", "BORDERLINE", "UNGRADEABLE"}
- Standard recommended action strings strictly match clinical routing policy
- Output structure completeness, schema validation, non-finite handling
- In-memory NumPy array support
- End-to-end evaluation on all 9 real retinal images in data/real_retinal_images/
"""

from pathlib import Path
import pytest
import numpy as np

from image_quality.decision import (
    evaluate_quality_gates,
    classify_quality_decision,
    classify_image_quality,
    ACTION_PROCEED,
    ACTION_ENHANCE,
    ACTION_RECAPTURE,
    DEFAULT_UNGRADEABLE_THRESHOLDS,
    DEFAULT_BORDERLINE_THRESHOLDS,
)
from image_quality.io import load_raw_image


DATA_DIR = Path("/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images")
REAL_IMAGE_FILES = sorted([f.name for f in DATA_DIR.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])


def test_classify_quality_good_case():
    """Verify high-scoring pristine image classifies as GOOD with proceed action."""
    mock_composite = {
        "composite_score": 85.0,
        "component_scores": {
            "focus_score": 85.0,
            "illumination_score": 85.0,
            "fov_score": 85.0,
            "centering_score": 85.0,
        },
        "sub_decisions": {},
        "weights": {},
        "diagnostics": {},
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "GOOD"
    assert decision["recommended_action"] == ACTION_PROCEED
    assert len(decision["triggered_quality_gates"]) == 0
    assert "acceptance criteria" in decision["diagnostic_reasons"][0]


def test_severe_blur_gate_overrides_high_composite():
    """Verify severe blur (<15.0) forces UNGRADEABLE even with high scores elsewhere."""
    # Composite could be mathematically high: 0.4*10 + 0.3*95 + 0.2*95 + 0.1*95 = 4.0 + 28.5 + 19.0 + 9.5 = 61.0
    mock_composite = {
        "composite_score": 61.0,
        "component_scores": {
            "focus_score": 10.0,
            "illumination_score": 95.0,
            "fov_score": 95.0,
            "centering_score": 95.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    assert decision["recommended_action"] == ACTION_RECAPTURE
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "severe_blur" in gate_names


def test_severe_illumination_defect_forces_ungradeable():
    """Verify severe illumination failure (<35.0) forces UNGRADEABLE."""
    mock_composite = {
        "composite_score": 65.0,
        "component_scores": {
            "focus_score": 90.0,
            "illumination_score": 25.0,
            "fov_score": 90.0,
            "centering_score": 90.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    assert decision["recommended_action"] == ACTION_RECAPTURE
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "severe_illumination_defect" in gate_names


def test_severe_dark_and_glare_clipping_forces_ungradeable():
    """Verify excessive dark or glare clipping triggers ungradeable gate."""
    mock_composite = {
        "composite_score": 75.0,
        "component_scores": {
            "focus_score": 75.0,
            "illumination_score": 70.0,
            "fov_score": 80.0,
            "centering_score": 80.0,
        },
        "illumination_assessment": {
            "dark_pixel_percentage": 58.2,
            "bright_pixel_percentage": 2.1,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "severe_dark_clipping" in gate_names


def test_severe_fov_truncation_forces_ungradeable():
    """Verify severe FOV truncation (<40.0) forces UNGRADEABLE."""
    mock_composite = {
        "composite_score": 60.0,
        "component_scores": {
            "focus_score": 80.0,
            "illumination_score": 80.0,
            "fov_score": 30.0,
            "centering_score": 80.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "severe_fov_truncation" in gate_names


def test_severe_off_center_forces_ungradeable():
    """Verify severe off-centering (<30.0) forces UNGRADEABLE."""
    mock_composite = {
        "composite_score": 72.0,
        "component_scores": {
            "focus_score": 80.0,
            "illumination_score": 80.0,
            "fov_score": 80.0,
            "centering_score": 20.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "severe_off_center" in gate_names


def test_soft_focus_gate_forces_borderline_despite_high_composite():
    """Verify soft focus (<50.0) overrides composite >= 70.0 into BORDERLINE."""
    # 0.4*48 + 0.3*90 + 0.2*95 + 0.1*95 = 19.2 + 27.0 + 19.0 + 9.5 = 74.7 (mathematically >= 70)
    mock_composite = {
        "composite_score": 74.7,
        "component_scores": {
            "focus_score": 48.0,
            "illumination_score": 90.0,
            "fov_score": 95.0,
            "centering_score": 95.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "BORDERLINE"
    assert decision["recommended_action"] == ACTION_ENHANCE
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "suboptimal_focus" in gate_names


def test_suboptimal_illumination_forces_borderline_despite_high_composite():
    """Verify sub-optimal illumination (<65.0) overrides composite >= 70.0 into BORDERLINE."""
    # Matches real case cell13_r1_c1_grade3.png where illumination is 55.02 and composite is 70.00
    mock_composite = {
        "composite_score": 70.0,
        "component_scores": {
            "focus_score": 77.0,
            "illumination_score": 55.0,
            "fov_score": 90.0,
            "centering_score": 98.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "BORDERLINE"
    assert decision["recommended_action"] == ACTION_ENHANCE
    gate_names = [g["gate"] for g in decision["triggered_quality_gates"]]
    assert "suboptimal_illumination" in gate_names


def test_composite_score_between_45_and_70_is_borderline():
    """Verify composite between 45.0 and 70.0 without hard gate triggers is BORDERLINE."""
    mock_composite = {
        "composite_score": 68.0,
        "component_scores": {
            "focus_score": 65.0,
            "illumination_score": 70.0,
            "fov_score": 80.0,
            "centering_score": 80.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "BORDERLINE"
    assert decision["recommended_action"] == ACTION_ENHANCE


def test_composite_score_below_45_is_ungradeable():
    """Verify composite < 45.0 triggers ungradeable gate."""
    mock_composite = {
        "composite_score": 42.0,
        "component_scores": {
            "focus_score": 42.0,
            "illumination_score": 42.0,
            "fov_score": 42.0,
            "centering_score": 42.0,
        },
    }
    decision = classify_quality_decision(mock_composite)
    assert decision["final_class"] == "UNGRADEABLE"
    assert decision["recommended_action"] == ACTION_RECAPTURE


def test_invalid_decision_input_raises_error():
    """Verify invalid input types or missing required keys raise appropriate errors."""
    with pytest.raises(TypeError):
        classify_quality_decision(["not", "a", "dict"])

    with pytest.raises(ValueError, match="missing"):
        classify_quality_decision({"composite_score": 75.0})

    with pytest.raises(ValueError, match="missing"):
        classify_quality_decision({"component_scores": {}})


def test_in_memory_numpy_array_end_to_end():
    """Verify classify_image_quality runs seamlessly on RGB NumPy arrays."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    img_rgb = load_raw_image(img_path)
    res = classify_image_quality(img_rgb)

    assert res["final_class"] in {"GOOD", "BORDERLINE", "UNGRADEABLE"}
    assert res["recommended_action"] in {ACTION_PROCEED, ACTION_ENHANCE, ACTION_RECAPTURE}
    assert res["image_path"] == "in_memory_array"
    assert "focus_assessment" in res
    assert "illumination_assessment" in res
    assert "fov_assessment" in res


@pytest.mark.parametrize("filename", REAL_IMAGE_FILES)
def test_real_image_decision_pipeline_end_to_end(filename):
    """Verify all 9 real retinal images execute end-to-end without unhandled errors."""
    img_path = DATA_DIR / filename
    res = classify_image_quality(img_path)

    assert res["final_class"] in {"GOOD", "BORDERLINE", "UNGRADEABLE"}
    assert np.isfinite(res["composite_score"])
    assert 0.0 <= res["composite_score"] <= 100.0

    # Verify action matches class
    if res["final_class"] == "GOOD":
        assert res["recommended_action"] == ACTION_PROCEED
        assert res["composite_score"] >= 70.0
    elif res["final_class"] == "BORDERLINE":
        assert res["recommended_action"] == ACTION_ENHANCE
    elif res["final_class"] == "UNGRADEABLE":
        assert res["recommended_action"] == ACTION_RECAPTURE

    # Verify diagnostic reasons exist and non-empty
    assert len(res["diagnostic_reasons"]) > 0
    for r in res["diagnostic_reasons"]:
        assert isinstance(r, str) and len(r) > 0


def test_deterministic_decision_reproducibility():
    """Verify consecutive executions produce identical decisions."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    res1 = classify_image_quality(img_path)
    res2 = classify_image_quality(img_path)
    assert res1["final_class"] == res2["final_class"]
    assert res1["composite_score"] == res2["composite_score"]
    assert res1["recommended_action"] == res2["recommended_action"]
    assert res1["triggered_quality_gates"] == res2["triggered_quality_gates"]
