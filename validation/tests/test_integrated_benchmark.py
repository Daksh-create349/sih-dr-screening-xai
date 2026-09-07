"""Automated tests for Integrated Pipeline vs Classifier-Only Benchmark.

Verifies:
1. classifier-only evaluation works
2. integrated evaluation works
3. referable threshold = 0.33
4. Grade 2-4 aggregation is correct
5. GOOD routing works
6. BORDERLINE enhancement routing works
7. UNGRADEABLE is rejected
8. no fake prediction is generated for rejected images
9. confusion matrix dimensions are correct
10. metric calculations are correct
11. historical 0.1181 threshold remains metadata-only unless explicitly selected
12. contamination warning is present
13. output files are reproducible in schema
14. frozen model checkpoint is used
15. real 9-image integration path still passes
"""

from pathlib import Path
import json
import tempfile
import numpy as np
import pytest
import cv2

from classifier.referable import REFERABLE_THRESHOLD
from classifier.model import DEFAULT_MODEL_PATH
from validation.integrated_benchmark import (
    load_labelled_records,
    evaluate_classifier_only,
    evaluate_integrated_pipeline,
    analyze_enhancement_effect,
    run_comprehensive_benchmark,
    export_benchmark_artifacts,
    CONTAMINATION_WARNING,
    HISTORICAL_HELD_OUT_BENCHMARK,
    REAL_IMAGE_GROUND_TRUTHS,
)
from validation.benchmark_protocol import (
    compute_5class_metrics,
    compute_referable_dr_metrics,
    compute_confusion_matrix,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = WORKSPACE_ROOT / "data" / "real_retinal_images"


@pytest.fixture(scope="module")
def real_records():
    """Load verified local real labelled retinal records."""
    records = load_labelled_records()
    assert len(records) == 9
    return records


def test_1_classifier_only_evaluation_works(real_records):
    """Verify Mode A classifier-only evaluation executes on real images."""
    res = evaluate_classifier_only(real_records[:2], threshold=0.33)
    assert res["mode"] == "classifier_only"
    assert res["num_evaluated"] == 2
    assert res["num_classified"] == 2
    assert res["num_rejected"] == 0
    assert len(res["predictions"]) == 2
    for p in res["predictions"]:
        assert 0 <= p["predicted_grade"] <= 4
        assert 0.0 <= p["confidence"] <= 1.0
        assert 0.0 <= p["referable_probability"] <= 1.0
        assert isinstance(p["is_referable"], bool)


def test_2_integrated_evaluation_works(real_records):
    """Verify Mode B integrated screening pipeline executes with IQA gating."""
    res = evaluate_integrated_pipeline(real_records[:2], threshold=0.33)
    assert res["mode"] == "integrated_pipeline"
    assert res["num_evaluated"] == 2
    assert res["routing_counts"]["total"] == 2
    assert len(res["predictions"]) == 2
    for p in res["predictions"]:
        assert p["iqa_status"] in {"GOOD", "BORDERLINE", "UNGRADEABLE"}


def test_3_referable_threshold_is_point_33():
    """Verify active production threshold is exactly 0.33."""
    assert REFERABLE_THRESHOLD == 0.33


def test_4_grade_2_to_4_aggregation():
    """Verify sum P(Grade 2..4) calculation for referable screening."""
    # Class probabilities: Grade 0: 0.1, Grade 1: 0.2, Grade 2: 0.3, Grade 3: 0.25, Grade 4: 0.15
    # Sum P(2..4) = 0.3 + 0.25 + 0.15 = 0.70 >= 0.33 -> Referable
    probs = np.array([[0.1, 0.2, 0.3, 0.25, 0.15]])
    y_true = np.array([2])
    metrics = compute_referable_dr_metrics(y_true, probs, threshold=0.33)
    assert metrics["true_positives"] == 1
    assert metrics["false_negatives"] == 0

    # Non-referable case: Sum P(2..4) = 0.20 < 0.33
    probs_non_ref = np.array([[0.5, 0.3, 0.1, 0.05, 0.05]])
    y_true_non = np.array([0])
    metrics_non = compute_referable_dr_metrics(y_true_non, probs_non_ref, threshold=0.33)
    assert metrics_non["true_negatives"] == 1
    assert metrics_non["false_positives"] == 0


def test_5_good_routing_works():
    """Verify pristine quality images route directly to classifier."""
    good_img = DATA_DIR / "confirmed_grade4_proliferative.jpg"
    rec = [{
        "filename": "confirmed_grade4_proliferative.jpg",
        "path": str(good_img),
        "true_grade": 4,
        "true_referable": True,
    }]
    res = evaluate_integrated_pipeline(rec, threshold=0.33)
    p = res["predictions"][0]
    assert p["iqa_status"] == "GOOD"
    assert p["enhancement_attempted"] is False
    assert p["classifier_run"] is True
    assert p["image_sent_to_classifier"] == "original"


def test_6_borderline_enhancement_routing_works():
    """Verify borderline acquisitions trigger CLAHE enhancement."""
    borderline_img = DATA_DIR / "aptos_train_sample_c10.png"
    rec = [{
        "filename": "aptos_train_sample_c10.png",
        "path": str(borderline_img),
        "true_grade": 0,
        "true_referable": False,
    }]
    res = evaluate_integrated_pipeline(rec, threshold=0.33)
    p = res["predictions"][0]
    assert p["iqa_status"] == "BORDERLINE"
    assert p["enhancement_attempted"] is True
    assert p["enhancement_accepted"] is True
    assert p["classifier_run"] is True
    assert "enhanced" in p["image_sent_to_classifier"]


def test_7_ungradeable_is_rejected(tmp_path):
    """Verify UNGRADEABLE images fail quality gate and bypass classifier."""
    black_img = np.zeros((384, 384, 3), dtype=np.uint8)
    black_path = tmp_path / "synthetic_black_ungradeable.png"
    cv2.imwrite(str(black_path), black_img)

    rec = [{
        "filename": "synthetic_black_ungradeable.png",
        "path": str(black_path),
        "true_grade": 0,
        "true_referable": False,
    }]
    res = evaluate_integrated_pipeline(rec, threshold=0.33)
    assert res["routing_counts"]["ungradeable"] == 1
    assert res["routing_counts"]["rejected"] == 1
    assert res["num_rejected"] == 1


def test_8_no_fake_prediction_for_rejected_images(tmp_path):
    """Verify strictly NO clinical prediction is fabricated for rejected images."""
    black_img = np.zeros((384, 384, 3), dtype=np.uint8)
    black_path = tmp_path / "synthetic_black_ungradeable.png"
    cv2.imwrite(str(black_path), black_img)

    rec = [{
        "filename": "synthetic_black_ungradeable.png",
        "path": str(black_path),
        "true_grade": 0,
        "true_referable": False,
    }]
    res = evaluate_integrated_pipeline(rec, threshold=0.33)
    p = res["predictions"][0]
    assert p["classifier_run"] is False
    assert p["predicted_grade"] is None
    assert p["confidence"] is None
    assert p["referable_probability"] is None
    assert p["is_referable"] is None
    assert p["probabilities"] is None
    assert p["recapture_feedback"] is not None


def test_9_confusion_matrix_dimensions():
    """Verify 5x5 and 2x2 confusion matrix shapes and summation."""
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 2, 4]
    cm = compute_confusion_matrix(y_true, y_pred, num_classes=5)
    assert cm.shape == (5, 5)
    assert np.sum(cm) == 5
    assert cm[3, 2] == 1


def test_10_metric_calculations():
    """Verify precision, recall, F1, sensitivity, specificity calculations."""
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 3, 4]
    m5 = compute_5class_metrics(y_true, y_pred)
    assert m5["accuracy"] == 1.0
    assert m5["macro_f1"] == 1.0

    probs = np.eye(5)
    m_ref = compute_referable_dr_metrics(y_true, probs, threshold=0.33)
    assert m_ref["sensitivity"] == 1.0
    assert m_ref["specificity"] == 1.0
    assert m_ref["binary_accuracy"] == 1.0


def test_11_historical_threshold_metadata_only():
    """Verify historical 0.1181 threshold is documented as validation-tuned reference."""
    assert HISTORICAL_HELD_OUT_BENCHMARK["validation_selected_threshold"]["threshold"] == 0.1181
    assert "validation" in HISTORICAL_HELD_OUT_BENCHMARK["validation_selected_threshold"]["selection_split"]
    assert "held-out" in HISTORICAL_HELD_OUT_BENCHMARK["validation_selected_threshold"]["evaluation_split"]
    # Default active threshold is 0.33, NOT 0.1181
    assert REFERABLE_THRESHOLD == 0.33


def test_12_contamination_warning_present():
    """Verify explicit dataset contamination warning is present."""
    assert "contamination" in CONTAMINATION_WARNING.lower()
    assert "splits" in CONTAMINATION_WARNING.lower()


def test_13_output_files_reproducible_in_schema(tmp_path):
    """Verify exported JSON and CSV follow exact expected schema."""
    payload = run_comprehensive_benchmark(output_dir=tmp_path)
    json_path = tmp_path / "integrated_benchmark_results.json"
    csv_path = tmp_path / "raw_predictions.csv"

    assert json_path.exists()
    assert csv_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "benchmark_version" in data
    assert "model" in data
    assert "baseline_1_classifier_only" in data
    assert "baseline_2_integrated_pipeline" in data
    assert "enhancement_effect_analysis" in data
    assert "engineering_conclusion" in data


def test_14_frozen_model_checkpoint_used():
    """Verify frozen model checkpoint path is loaded."""
    assert DEFAULT_MODEL_PATH.exists()
    assert "MODEL_V2_80pct_backup.keras" in str(DEFAULT_MODEL_PATH)


def test_15_real_9_image_integration_path_passes(real_records):
    """Verify all 9 real retinal images execute cleanly without exceptions."""
    assert len(real_records) == 9
    res = evaluate_integrated_pipeline(real_records, threshold=0.33)
    assert res["num_classified"] == 9
    assert len(res["enhancement_events"]) == 5
