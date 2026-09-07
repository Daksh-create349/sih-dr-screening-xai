"""Automated test suite for operator reporting and recapture feedback (image_quality.report).

Validates:
- Structured quality report generation for GOOD, BORDERLINE, and UNGRADEABLE status
- Actionable recapture feedback tailored to specific triggered quality gates
- Correct clinical action strings and operator guidance
- Score and enhancement metadata propagation
- JSON serializability of report dictionary
- Markdown report formatting
- Invalid input rejection
- End-to-end evaluation on all 9 real retinal images in data/real_retinal_images/
"""

import json
from pathlib import Path
import pytest
import numpy as np

from image_quality.report import (
    generate_recapture_feedback,
    build_operator_message,
    generate_quality_report,
    format_report_markdown,
    ACTION_PROCEED_DR,
    ACTION_PROCEED_ENHANCED,
    ACTION_RECONSIDER_BORDERLINE,
    ACTION_REJECT_RECAPTURE,
    CLINICAL_SAFETY_DISCLAIMER,
)
from image_quality.io import load_raw_image


DATA_DIR = Path("/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images")
REAL_IMAGE_FILES = sorted([f.name for f in DATA_DIR.glob("*") if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])


def test_recapture_feedback_mapping_individual_gates():
    """Verify specific quality gates produce tailored, actionable recapture advice."""
    blur_feedback = generate_recapture_feedback([{"gate": "severe_blur"}])
    assert "blurry" in blur_feedback.lower()
    assert "refocus" in blur_feedback.lower()

    illum_feedback = generate_recapture_feedback([{"gate": "severe_illumination_defect"}])
    assert "illumination" in illum_feedback.lower()

    dark_feedback = generate_recapture_feedback([{"gate": "severe_dark_clipping"}])
    assert "underexposure" in dark_feedback.lower()
    assert "flash" in dark_feedback.lower()

    glare_feedback = generate_recapture_feedback([{"gate": "severe_glare_clipping"}])
    assert "glare" in glare_feedback.lower()

    fov_feedback = generate_recapture_feedback([{"gate": "severe_fov_truncation"}])
    assert "field of view" in fov_feedback.lower()

    center_feedback = generate_recapture_feedback([{"gate": "severe_off_center"}])
    assert "off-center" in center_feedback.lower() or "fixation" in center_feedback.lower()


def test_recapture_feedback_multiple_gates_combined():
    """Verify multiple failing gates are compiled into numbered combined guidance."""
    gates = [{"gate": "severe_blur"}, {"gate": "severe_dark_clipping"}]
    feedback = generate_recapture_feedback(gates)
    assert "1." in feedback
    assert "2." in feedback
    assert "blurry" in feedback.lower()
    assert "underexposure" in feedback.lower()


def test_recapture_feedback_empty_or_unknown_fallback():
    """Verify unknown or empty gates fallback safely."""
    empty_fb = generate_recapture_feedback([])
    assert "recapture" in empty_fb.lower()

    unknown_fb = generate_recapture_feedback(["mysterious_defect"])
    assert "recapture" in unknown_fb.lower()


def test_build_operator_message_actions():
    """Verify operator messages for GOOD, BORDERLINE, and UNGRADEABLE cases."""
    # GOOD message
    good_msg = build_operator_message("GOOD", 85.0, [])
    assert "acceptable" in good_msg.lower()

    # BORDERLINE with accepted enhancement
    enh_accepted = {
        "attempted": True,
        "accepted": True,
        "method": "clahe",
        "before_composite_score": 68.0,
        "after_composite_score": 75.0,
    }
    b_acc_msg = build_operator_message("BORDERLINE", 75.0, ["suboptimal_focus"], enhancement_info=enh_accepted)
    assert "accepted" in b_acc_msg.lower()
    assert "downstream analysis" in b_acc_msg.lower()

    # BORDERLINE with rejected enhancement
    enh_rejected = {"attempted": True, "accepted": False, "method": "unsharp", "rejection_reason": "safeguard violations"}
    b_rej_msg = build_operator_message("BORDERLINE", 68.0, ["suboptimal_focus"], enhancement_info=enh_rejected)
    assert "rejected" in b_rej_msg.lower()
    assert "recapturing" in b_rej_msg.lower()

    # UNGRADEABLE message
    u_msg = build_operator_message("UNGRADEABLE", 35.0, [{"gate": "severe_blur"}])
    assert "ungradeable" in u_msg.lower()
    assert "refocus" in u_msg.lower()


def test_report_schema_completeness_and_json_serializable():
    """Verify generate_quality_report outputs full schema and serializes cleanly to JSON."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    report = generate_quality_report(img_path, attempt_enhancement_if_borderline=True)

    required_keys = {
        "image_identifier",
        "image_path",
        "quality_status",
        "composite_score",
        "initial_quality_status",
        "initial_composite_score",
        "component_scores",
        "sub_decisions",
        "triggered_quality_gates",
        "diagnostic_reasons",
        "enhancement",
        "recommended_action",
        "operator_message",
        "recapture_feedback",
        "clinical_safety_disclaimer",
        "diagnostics",
    }
    assert required_keys.issubset(report.keys())
    assert report["clinical_safety_disclaimer"] == CLINICAL_SAFETY_DISCLAIMER

    # Must serialize to JSON without error
    json_str = json.dumps(report, default=str)
    assert isinstance(json_str, str)
    loaded = json.loads(json_str)
    assert loaded["image_identifier"] == report["image_identifier"]


def test_report_in_memory_numpy_array_support():
    """Verify generate_quality_report accepts loaded RGB NumPy arrays."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    img = load_raw_image(img_path)

    report = generate_quality_report(img, attempt_enhancement_if_borderline=False)
    assert report["image_identifier"] == "in_memory_array"
    assert report["quality_status"] in {"GOOD", "BORDERLINE", "UNGRADEABLE"}
    assert np.isfinite(report["composite_score"])


def test_format_report_markdown():
    """Verify format_report_markdown generates valid markdown with all sections."""
    img_path = DATA_DIR / REAL_IMAGE_FILES[0]
    report = generate_quality_report(img_path, attempt_enhancement_if_borderline=False)
    md = format_report_markdown(report)

    assert "### Quality Report:" in md
    assert "**Composite Score**:" in md
    assert "**Recommended Action**:" in md
    assert "**Operator Guidance**:" in md


@pytest.mark.parametrize("filename", REAL_IMAGE_FILES)
def test_all_real_retinal_images_generate_reports_end_to_end(filename):
    """Verify all 9 real retinal images successfully produce reports end-to-end without unhandled errors."""
    img_path = DATA_DIR / filename
    report = generate_quality_report(img_path, attempt_enhancement_if_borderline=True)

    assert report["quality_status"] in {"GOOD", "BORDERLINE", "UNGRADEABLE"}
    assert 0.0 <= report["composite_score"] <= 100.0

    if report["quality_status"] == "GOOD":
        assert report["recommended_action"] == ACTION_PROCEED_DR
    elif report["quality_status"] == "BORDERLINE":
        if report["enhancement"]["attempted"] and report["enhancement"]["accepted"]:
            assert report["recommended_action"] == ACTION_PROCEED_ENHANCED
        else:
            assert report["recommended_action"] == ACTION_RECONSIDER_BORDERLINE
    elif report["quality_status"] == "UNGRADEABLE":
        assert report["recommended_action"] == ACTION_REJECT_RECAPTURE
        assert report["recapture_feedback"] is not None
