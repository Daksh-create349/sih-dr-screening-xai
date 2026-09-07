"""Automated tests for DR inference and upstream IQA screening pipeline."""

from pathlib import Path
from typing import List, Union
import numpy as np

from classifier.predictor import (
    predict_image,
    predict_batch,
    run_screening_pipeline,
)

DATA_DIR: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "real_retinal_images"
)
REAL_GOOD_IMAGE: Path = DATA_DIR / "confirmed_grade4_proliferative.jpg"
REAL_BORDERLINE_IMAGE: Path = DATA_DIR / "aptos_train_sample_c10.png"


def test_predict_image_real_image():
    """Verify single-image prediction returns valid prediction payload."""
    assert REAL_GOOD_IMAGE.exists(), f"Image missing at {REAL_GOOD_IMAGE}"
    res = predict_image(REAL_GOOD_IMAGE)

    assert isinstance(res["predicted_grade"], int)
    assert 0 <= res["predicted_grade"] <= 4
    assert isinstance(res["class_name"], str)
    assert 0.0 <= res["confidence"] <= 1.0

    probs = res["probabilities"]
    assert len(probs) == 5
    prob_sum = sum(probs.values())
    assert abs(prob_sum - 1.0) < 1e-4, f"Prob sum error: {prob_sum}"

    assert res["confidence"] == max(probs.values())
    assert "referable" in res
    assert isinstance(res["referable"]["is_referable"], bool)
    assert "APTOS_DR_EfficientNetB3" in res["model_identifier"]


def test_predict_image_determinism():
    """Verify inference on same real image is strictly deterministic."""
    res1 = predict_image(REAL_GOOD_IMAGE)
    res2 = predict_image(REAL_GOOD_IMAGE)

    assert res1["predicted_grade"] == res2["predicted_grade"]
    assert res1["confidence"] == res2["confidence"]
    for grade in range(5):
        p1 = res1["probabilities"][grade]
        p2 = res2["probabilities"][grade]
        assert abs(p1 - p2) < 1e-6


def test_predict_batch():
    """Verify batch inference matches single-image inference."""
    items: List[Union[str, Path, np.ndarray]] = [
        REAL_GOOD_IMAGE,
        REAL_BORDERLINE_IMAGE,
    ]
    batch_res = predict_batch(items)

    assert len(batch_res) == 2
    single_res0 = predict_image(REAL_GOOD_IMAGE)
    single_res1 = predict_image(REAL_BORDERLINE_IMAGE)

    assert batch_res[0]["predicted_grade"] == single_res0["predicted_grade"]
    assert batch_res[1]["predicted_grade"] == single_res1["predicted_grade"]
    assert abs(batch_res[0]["confidence"] - single_res0["confidence"]) < 1e-5
    assert abs(batch_res[1]["confidence"] - single_res1["confidence"]) < 1e-5


def test_predict_batch_empty():
    """Verify empty batch returns empty list."""
    assert predict_batch([]) == []


def test_upstream_iqa_good_image_routing():
    """Verify GOOD retinal image routes original image directly to classifier."""  # noqa: E501
    res = run_screening_pipeline(REAL_GOOD_IMAGE)

    assert res["iqa_status"] == "GOOD"
    assert res["final_quality_status"] == "GOOD"
    assert res["classifier_run"] is True
    assert res["image_sent_to_classifier"] == "original"
    assert res["predicted_dr_grade"] is not None
    assert res["probabilities"] is not None
    assert res["operator_action"] == "Proceed to DR classification."


def test_upstream_iqa_borderline_image_routing():
    """Verify BORDERLINE retinal image applies enhancement and routes it."""
    res = run_screening_pipeline(REAL_BORDERLINE_IMAGE)

    assert res["iqa_status"] == "BORDERLINE"
    assert res["enhancement_attempted"] is True
    assert res["enhancement_accepted"] is True
    assert res["classifier_run"] is True
    assert res["image_sent_to_classifier"] == "enhanced_clahe"
    assert res["predicted_dr_grade"] is not None
    assert "Enhanced image may proceed" in res["operator_message"]


def test_upstream_iqa_ungradeable_blocked():
    """Verify UNGRADEABLE image is blocked and NEVER reaches classifier."""
    black_array = np.zeros((200, 200, 3), dtype=np.uint8)

    res = run_screening_pipeline(black_array)

    # IQA must flag as UNGRADEABLE
    assert res["final_quality_status"] == "UNGRADEABLE"
    # Classifier MUST NOT run
    assert res["classifier_run"] is False
    assert res["image_sent_to_classifier"] is None
    assert res["predicted_dr_grade"] is None
    assert res["predicted_dr_class"] is None
    assert res["probabilities"] is None
    assert res["confidence"] is None
    assert res["referable_status"] == "N/A (Image Rejected by IQA)"
    # Recapture feedback must be provided
    assert res["recapture_feedback"] is not None
    assert "recapture" in res["operator_action"].lower()
