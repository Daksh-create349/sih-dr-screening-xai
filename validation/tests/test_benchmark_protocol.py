"""Automated tests for 5-class and referable DR benchmark evaluation formulas.

Pure mathematical unit tests using synthetic controlled arrays solely to
verify metric formulas, thresholding mechanics, and edge case handling.
These synthetic vectors are NOT retinal data and not evaluation results.
"""

import json
import numpy as np
import pytest

from validation.benchmark_protocol import (
    compute_5class_metrics,
    compute_referable_dr_metrics,
    compute_binary_metrics,
    get_frozen_benchmark_protocol_config,
)


def test_compute_5class_metrics_perfect_predictions():
    """Verify 5-class metrics under ideal 100% accurate predictions."""
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 3, 4]

    m = compute_5class_metrics(y_true, y_pred)

    assert m["accuracy"] == 1.0
    assert m["balanced_accuracy"] == 1.0
    assert m["macro_f1"] == 1.0
    assert m["weighted_f1"] == 1.0
    assert np.array_equal(m["confusion_matrix"], np.eye(5, dtype=int))


def test_compute_5class_metrics_mixed_predictions():
    """Verify 5-class metric calculations on known mixed test vector."""
    y_true = [0, 0, 1, 2, 3, 4]
    y_pred = [0, 1, 1, 2, 3, 4]

    m = compute_5class_metrics(y_true, y_pred)

    assert m["num_samples"] == 6
    assert m["accuracy"] == pytest.approx(5 / 6, rel=1e-3)
    assert 0.0 <= m["macro_f1"] <= 1.0
    assert len(m["per_class_metrics"]) == 5


def test_compute_referable_dr_metrics_classification():
    """Verify referable DR sensitivity, specificity, and confusion matrix."""
    # Grades 0, 1 -> Negative (0)
    # Grades 2, 3, 4 -> Positive (1)
    y_true = [0, 1, 2, 3, 4]

    # Probabilities:
    # item 0: high class 0 (P_ref = 0.05) -> Neg
    # item 1: high class 1 (P_ref = 0.20) -> Neg
    # item 2: moderate class 2 (P_ref = 0.60) -> Pos
    # item 3: high class 3 (P_ref = 0.85) -> Pos
    # item 4: high class 4 (P_ref = 0.95) -> Pos
    probs = np.array([
        [0.90, 0.05, 0.05, 0.00, 0.00],
        [0.10, 0.70, 0.15, 0.05, 0.00],
        [0.10, 0.30, 0.40, 0.15, 0.05],
        [0.05, 0.10, 0.15, 0.60, 0.10],
        [0.01, 0.04, 0.05, 0.10, 0.80],
    ])

    res = compute_referable_dr_metrics(y_true, probs, threshold=0.33)

    assert res["num_samples"] == 5
    assert res["positive_count"] == 3
    assert res["negative_count"] == 2
    assert res["true_positives"] == 3
    assert res["true_negatives"] == 2
    assert res["false_positives"] == 0
    assert res["false_negatives"] == 0
    assert res["sensitivity"] == 1.0
    assert res["specificity"] == 1.0
    assert res["binary_accuracy"] == 1.0
    assert res["roc_auc"] == 1.0


def test_compute_referable_dr_single_class_auc_graceful():
    """Verify graceful handling of ROC-AUC when one class is absent."""
    # All true labels are negative (Grades 0 and 1)
    y_true = [0, 0, 1, 1]
    probs = np.full((4, 5), 0.20)

    res = compute_referable_dr_metrics(y_true, probs, threshold=0.33)

    assert res["positive_count"] == 0
    assert res["roc_auc"] is None
    assert "ROC-AUC requires both classes" in res["roc_auc_note"]


def test_compute_binary_metrics_helper():
    """Verify binary helper metric calculation."""
    y_t = [1, 1, 0, 0]
    y_p = [1, 0, 0, 1]

    bm = compute_binary_metrics(y_t, y_p)

    assert bm["accuracy"] == 0.5
    assert bm["sensitivity"] == 0.5
    assert bm["specificity"] == 0.5


def test_get_frozen_benchmark_protocol_config():
    """Verify benchmark protocol configuration schema and serializability."""
    config = get_frozen_benchmark_protocol_config()

    assert config["protocol_version"] == "1.0.0"
    assert config["referable_dr"]["frozen_operating_threshold"] == 0.33
    assert config["referable_dr"]["test_set_tuning_permitted"] is False
    assert "baseline_1_classifier_only" in config["baselines"]
    assert "baseline_2_integrated_pipeline" in config["baselines"]

    serialized = json.dumps(config)
    assert len(serialized) > 0
