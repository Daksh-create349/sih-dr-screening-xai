"""Automated tests for Referable Diabetic Retinopathy screening logic."""

import numpy as np
import pytest

from classifier.referable import (
    evaluate_referable_dr,
    get_dr_grade_name,
    REFERABLE_THRESHOLD,
    DR_GRADE_NAMES,
)


def test_grade_names_mapping():
    """Verify 5-class clinical grade names."""
    assert len(DR_GRADE_NAMES) == 5
    assert get_dr_grade_name(0) == "No DR"
    assert get_dr_grade_name(1) == "Mild DR"
    assert get_dr_grade_name(2) == "Moderate DR"
    assert get_dr_grade_name(3) == "Severe DR"
    assert get_dr_grade_name(4) == "Proliferative DR"
    assert "Unknown" in get_dr_grade_name(99)


def test_referable_decision_non_referable():
    """Verify probability distribution dominated by Grade 0/1 yields Non-Referable."""
    # Grade 0: 0.70, Grade 1: 0.20, Grade 2: 0.05, Grade 3: 0.03, Grade 4: 0.02
    # P(2..4) = 0.10 < 0.33
    probs = [0.70, 0.20, 0.05, 0.03, 0.02]
    res = evaluate_referable_dr(probs, threshold=REFERABLE_THRESHOLD)

    assert res["is_referable"] is False
    assert res["referable_probability"] == 0.10
    assert res["screening_category"] == "Non-Referable DR"
    assert "annual" in res["clinical_action"].lower()
    assert res["derived_from_predicted_grade"] is False


def test_referable_decision_referable():
    """Verify probability distribution with elevated Grade 2+ yields Referable."""
    # Grade 0: 0.10, Grade 1: 0.15, Grade 2: 0.40, Grade 3: 0.20, Grade 4: 0.15
    # P(2..4) = 0.75 >= 0.33
    probs = [0.10, 0.15, 0.40, 0.20, 0.15]
    res = evaluate_referable_dr(probs, threshold=REFERABLE_THRESHOLD)

    assert res["is_referable"] is True
    assert res["referable_probability"] == 0.75
    assert res["screening_category"] == "Referable DR"
    assert "referral" in res["clinical_action"].lower()
    assert res["derived_from_predicted_grade"] is True


def test_referable_threshold_boundary_cases():
    """Verify exact threshold boundary behavior at 0.33."""
    # Exactly 0.33: Grade 0: 0.67, Grade 2: 0.33
    probs_at_boundary = [0.67, 0.0, 0.33, 0.0, 0.0]
    res_at = evaluate_referable_dr(probs_at_boundary, threshold=0.33)
    assert res_at["is_referable"] is True

    # Just below boundary: 0.329
    probs_below = [0.671, 0.0, 0.329, 0.0, 0.0]
    res_below = evaluate_referable_dr(probs_below, threshold=0.33)
    assert res_below["is_referable"] is False


def test_custom_threshold_override():
    """Verify custom decision threshold can be supplied."""
    probs = [0.50, 0.10, 0.20, 0.10, 0.10]  # P(2..4) = 0.40
    # With 0.50 threshold -> Non-referable
    res_high = evaluate_referable_dr(probs, threshold=0.50)
    assert res_high["is_referable"] is False

    # With 0.30 threshold -> Referable
    res_low = evaluate_referable_dr(probs, threshold=0.30)
    assert res_low["is_referable"] is True


def test_invalid_probability_length_raises():
    """Verify non-5-element arrays raise ValueError."""
    with pytest.raises(ValueError, match="Expected 5-element probability array"):
        evaluate_referable_dr([0.5, 0.5])

    with pytest.raises(ValueError, match="Expected 5-element probability array"):
        evaluate_referable_dr([0.2, 0.2, 0.2, 0.2, 0.1, 0.1])


def test_grade_components_breakdown():
    """Verify individual grade components for moderate, severe, and proliferative DR."""
    probs = [0.1, 0.2, 0.3, 0.25, 0.15]
    res = evaluate_referable_dr(probs)
    comps = res["grade_components"]
    assert comps["p_grade_2_moderate"] == 0.3
    assert comps["p_grade_3_severe"] == 0.25
    assert comps["p_grade_4_proliferative"] == 0.15
