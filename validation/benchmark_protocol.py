"""Benchmark evaluation protocol module for Diabetic Retinopathy screening.

Defines frozen evaluation metrics for:
1. 5-Class Multiclass Classification (Grades 0-4)
2. Referable Diabetic Retinopathy Binary Classification (Grades 2..4 vs 0..1)
3. Operating Threshold Protocol (Frozen at 0.33; validation-only recalibration)
4. Evaluation Baselines (Classifier-Only vs Integrated IQA Screening Pipeline)
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np


def _safe_trapz(y: Any, x: Any) -> float:
    """Compute trapezoidal integration compatible with numpy 1.x and 2.x."""
    fn = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)
    if fn is not None:
        return float(fn(y, x))
    from scipy.integrate import trapezoid
    return float(trapezoid(y, x))


FROZEN_REFERABLE_THRESHOLD = 0.33
CLASS_NAMES = {
    0: "No DR",
    1: "Mild DR",
    2: "Moderate DR",
    3: "Severe DR",
    4: "Proliferative DR",
}


def compute_confusion_matrix(
    y_true: Any,
    y_pred: Any,
    num_classes: int = 5,
) -> Any:
    """Compute integer confusion matrix of shape (num_classes, num_classes)."""
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t, p] += 1
    return cm


def compute_5class_metrics(
    y_true: Any,
    y_pred: Any,
) -> Dict[str, Any]:
    """Calculate comprehensive 5-class evaluation metrics.

    Metrics:
    - Overall Accuracy
    - Balanced Accuracy (macro recall)
    - Macro Precision, Recall, F1
    - Weighted F1
    - Per-class Precision, Recall, F1
    - 5x5 Confusion Matrix

    Args:
        y_true: True class labels in {0, 1, 2, 3, 4}.
        y_pred: Predicted class labels in {0, 1, 2, 3, 4}.

    Returns:
        dict: Metric dictionary.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_pred, dtype=int)

    n_samples = len(y_t)
    if n_samples == 0:
        return {"error": "Empty ground truth and prediction arrays."}

    cm = compute_confusion_matrix(y_t, y_p, num_classes=5)

    per_class = {}
    precisions = []
    recalls = []
    f1s = []
    support = []

    for c in range(5):
        tp = cm[c, c]
        fp = int(np.sum(cm[:, c]) - tp)
        fn = int(np.sum(cm[c, :]) - tp)
        sup = int(np.sum(cm[c, :]))

        p = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        r = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f = float(2 * p * r / (p + r)) if (p + r) > 0 else 0.0

        per_class[str(c)] = {
            "class_name": CLASS_NAMES.get(c, f"Class {c}"),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f, 4),
            "support": sup,
        }
        precisions.append(p)
        recalls.append(r)
        f1s.append(f)
        support.append(sup)

    total_correct = int(np.trace(cm))
    accuracy = float(total_correct / n_samples)
    balanced_accuracy = float(np.mean(recalls))
    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))

    # Weighted F1
    total_support = sum(support)
    if total_support > 0:
        weighted_f1 = float(
            sum(f * s for f, s in zip(f1s, support)) / total_support
        )
    else:
        weighted_f1 = 0.0

    return {
        "num_samples": n_samples,
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class_metrics": per_class,
        "confusion_matrix": cm.tolist(),
    }


def compute_roc_auc_binary(
    y_true_binary: Any,
    y_scores: Any,
) -> Tuple[Optional[float], Optional[str]]:
    """Calculate binary ROC-AUC using trapezoidal integration.

    Returns:
        (auc, reason): Float AUC score or None with reason string.
    """
    y_t = np.asarray(y_true_binary, dtype=int)
    scores = np.asarray(y_scores, dtype=float)
    pos = int(np.sum(y_t == 1))
    neg = int(np.sum(y_t == 0))

    if pos == 0 or neg == 0:
        return (
            None,
            f"ROC-AUC requires both classes (pos={pos}, neg={neg}).",
        )

    # Sort descending by predicted score
    desc_idx = np.argsort(-scores)
    y_sorted = y_t[desc_idx]

    # Compute TPR and FPR across thresholds
    tps = np.cumsum(y_sorted == 1)
    fps = np.cumsum(y_sorted == 0)

    tpr = np.concatenate([[0.0], tps / pos])
    fpr = np.concatenate([[0.0], fps / neg])

    # Trapezoidal integration
    auc = _safe_trapz(tpr, fpr)
    return round(max(0.0, min(1.0, auc)), 4), None


def compute_pr_auc_binary(
    y_true_binary: Any,
    y_scores: Any,
) -> Tuple[Optional[float], Optional[str]]:
    """Calculate binary Precision-Recall AUC (Average Precision)."""
    y_t = np.asarray(y_true_binary, dtype=int)
    scores = np.asarray(y_scores, dtype=float)
    pos = int(np.sum(y_t == 1))
    if pos == 0:
        return None, "PR-AUC requires at least one positive sample."

    desc_idx = np.argsort(-scores)
    y_sorted = y_t[desc_idx]

    tp_cumsum = np.cumsum(y_sorted == 1)
    fp_cumsum = np.cumsum(y_sorted == 0)

    recalls = tp_cumsum / pos
    precisions = tp_cumsum / (tp_cumsum + fp_cumsum)

    recalls = np.concatenate([[0.0], recalls])
    precisions = np.concatenate([[1.0], precisions])

    # Area under PR curve
    pr_auc = _safe_trapz(precisions, recalls)
    return round(max(0.0, min(1.0, pr_auc)), 4), None


def compute_referable_dr_metrics(
    y_true: Any,
    probabilities: Any,
    threshold: float = FROZEN_REFERABLE_THRESHOLD,
) -> Dict[str, Any]:
    """Calculate Referable DR screening metrics.

    Referable DR:
    - Positive: Grades 2, 3, 4
    - Negative: Grades 0, 1
    - Score: sum P(Grade 2..4)
    - Classification: Score >= threshold

    Args:
        y_true: True class labels in {0, 1, 2, 3, 4}.
        probabilities: Predicted probabilities of shape (N, 5).
        threshold: Referable threshold (default: 0.33).

    Returns:
        dict: Binary screening metrics, confusion matrix, ROC-AUC, PR-AUC.
    """
    y_t = np.asarray(y_true, dtype=int)
    probs = np.asarray(probabilities, dtype=float)

    if len(y_t) == 0:
        return {"error": "Empty input arrays."}

    # Binary ground truth
    y_true_binary = (y_t >= 2).astype(int)

    # Referable probability: sum of classes 2, 3, 4
    if probs.ndim == 2 and probs.shape[1] == 5:
        p_referable = np.sum(probs[:, 2:5], axis=1)
    elif probs.ndim == 1:
        p_referable = probs
    else:
        raise ValueError(
            f"Expected shape (N, 5) or (N,), got {probs.shape}"
        )

    y_pred_binary = (p_referable >= threshold).astype(int)

    tp = int(np.sum((y_true_binary == 1) & (y_pred_binary == 1)))
    fp = int(np.sum((y_true_binary == 0) & (y_pred_binary == 1)))
    tn = int(np.sum((y_true_binary == 0) & (y_pred_binary == 0)))
    fn = int(np.sum((y_true_binary == 1) & (y_pred_binary == 0)))

    n_samples = len(y_true_binary)
    accuracy = (tp + tn) / n_samples if n_samples > 0 else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0

    roc_auc, roc_reason = compute_roc_auc_binary(y_true_binary, p_referable)
    pr_auc, pr_reason = compute_pr_auc_binary(y_true_binary, p_referable)

    return {
        "threshold": float(threshold),
        "num_samples": n_samples,
        "positive_count": int(np.sum(y_true_binary == 1)),
        "negative_count": int(np.sum(y_true_binary == 0)),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "sensitivity": round(float(sensitivity), 4),
        "specificity": round(float(specificity), 4),
        "precision_ppv": round(float(ppv), 4),
        "npv": round(float(npv), 4),
        "binary_accuracy": round(float(accuracy), 4),
        "roc_auc": roc_auc,
        "roc_auc_note": roc_reason,
        "pr_auc": pr_auc,
        "pr_auc_note": pr_reason,
        "confusion_matrix_2x2": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
    }


def compute_binary_metrics(
    y_true_binary: Any,
    y_pred_binary: Any,
) -> Dict[str, Any]:
    """Helper for pure binary 0/1 inputs."""
    y_t = np.asarray(y_true_binary, dtype=int)
    y_p = np.asarray(y_pred_binary, dtype=int)
    tp = int(np.sum((y_t == 1) & (y_p == 1)))
    fp = int(np.sum((y_t == 0) & (y_p == 1)))
    tn = int(np.sum((y_t == 0) & (y_p == 0)))
    fn = int(np.sum((y_t == 1) & (y_p == 0)))

    n = len(y_t)
    acc = float((tp + tn) / n) if n > 0 else 0.0
    sens = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    ppv = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    npv = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "sensitivity": round(sens, 4),
        "specificity": round(spec, 4),
        "ppv": round(ppv, 4),
        "npv": round(npv, 4),
    }


def get_frozen_benchmark_protocol_config() -> Dict[str, Any]:
    """Return the frozen benchmark protocol configuration."""
    return {
        "protocol_version": "1.0.0",
        "model_checkpoint": "model/MODEL_V2_80pct_backup.keras",
        "model_architecture": "APTOS_DR_EfficientNetB3_V2",
        "input_resolution": [384, 384, 3],
        "classes": CLASS_NAMES,
        "referable_dr": {
            "positive_grades": [2, 3, 4],
            "negative_grades": [0, 1],
            "frozen_operating_threshold": FROZEN_REFERABLE_THRESHOLD,
            "threshold_definition": "sum P(Grade 2..4) >= 0.33",
            "test_set_tuning_permitted": False,
            "recalibration_rule": (
                "Validation split only; search range [0.10, 0.90], step 0.01 "
                "optimizing Youden's J index (Sens + Spec - 1)."
            ),
        },
        "baselines": {
            "baseline_1_classifier_only": {
                "name": "Single-Technique Classifier Baseline",
                "pipeline": (
                    "Raw Image -> Crop + INTER_AREA 384x384 -> "
                    "EfficientNetB3 -> Prediction"
                ),
                "iqa_gating_included": False,
            },
            "baseline_2_integrated_pipeline": {
                "name": "Integrated Clinical Screening Pipeline",
                "pipeline": (
                    "Raw Image -> IQA -> "
                    "GOOD: Direct classifier | "
                    "BORDERLINE: CLAHE -> Re-check -> Classifier | "
                    "UNGRADEABLE: Reject & Recapture -> "
                    "DR Prediction -> Referable Decision -> Evidence"
                ),
                "iqa_gating_included": True,
            },
        },
        "dataset_separation_rules": {
            "integration_set": (
                "9 real local images strictly for regression testing."
            ),
            "clinical_benchmark_set": (
                "Labelled APTOS splits (Train ~2930, Val ~366, Test ~366)."
            ),
            "metric_mixing_prohibited": True,
        },
    }
