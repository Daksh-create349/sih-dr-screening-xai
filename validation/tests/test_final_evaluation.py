"""Tests for final clinical evaluation audit and leakage-aware benchmark.

Verifies:
- Saved metric consistency
- Confusion matrix dimensions (5x5 and 2x2)
- Sensitivity and specificity calculations
- Threshold metadata (0.50, 0.33, 0.1181)
- Dataset split contamination quality warning
- Clinical benchmark vs 9-image integration distinction
- JSON serializability
- Internal mathematical consistency (no contradictions)
"""

import json
from pathlib import Path
import pytest

from validation.final_evaluation import (
    CONFUSION_MATRIX_5CLASS,
    CONFUSION_MATRIX_REFERABLE_ORIG,
    CONFUSION_MATRIX_REFERABLE_VAL_THRESH,
    recompute_5class_metrics,
    recompute_binary_metrics,
    get_dataset_contamination_warning,
    get_integration_pipeline_evidence,
    build_final_clinical_evaluation,
    generate_final_evaluation_markdown,
    save_final_evaluation_reports,
)


@pytest.fixture
def workspace_root():
    return Path(__file__).resolve().parent.parent.parent


def test_confusion_matrix_dimensions():
    """Verify exact matrix dimensions and sample counts."""
    # 5-class matrix must be 5x5
    assert len(CONFUSION_MATRIX_5CLASS) == 5
    for row in CONFUSION_MATRIX_5CLASS:
        assert len(row) == 5

    total_5class = sum(sum(r) for r in CONFUSION_MATRIX_5CLASS)
    assert total_5class == 366

    # Binary original matrix must be 2x2
    assert len(CONFUSION_MATRIX_REFERABLE_ORIG) == 2
    for row in CONFUSION_MATRIX_REFERABLE_ORIG:
        assert len(row) == 2
    assert sum(sum(r) for r in CONFUSION_MATRIX_REFERABLE_ORIG) == 366

    # Binary val-selected matrix must be 2x2
    assert len(CONFUSION_MATRIX_REFERABLE_VAL_THRESH) == 2
    for row in CONFUSION_MATRIX_REFERABLE_VAL_THRESH:
        assert len(row) == 2
    assert sum(sum(r) for r in CONFUSION_MATRIX_REFERABLE_VAL_THRESH) == 366


def test_5class_metric_recomputation():
    """Verify recomputed 5-class metrics match audited Colab results."""
    res = recompute_5class_metrics(CONFUSION_MATRIX_5CLASS)

    assert res["total_samples"] == 366
    assert res["accuracy"] == 0.8115
    assert res["accuracy_pct"] == 81.15
    assert res["macro_precision"] == 0.6434
    assert res["macro_recall"] == 0.5738
    assert res["macro_f1"] == 0.5827
    assert res["weighted_f1"] == 0.8036

    # Verify per-class metrics
    classes = res["per_class"]
    assert len(classes) == 5

    # Grade 0
    assert classes[0]["precision"] == 0.9751
    assert classes[0]["recall"] == 0.9849
    assert classes[0]["f1_score"] == 0.9800
    assert classes[0]["support"] == 199

    # Grade 1
    assert classes[1]["precision"] == 0.5625
    assert classes[1]["recall"] == 0.6000
    assert classes[1]["f1_score"] == 0.5806
    assert classes[1]["support"] == 30

    # Grade 2
    assert classes[2]["precision"] == 0.6796
    assert classes[2]["recall"] == 0.8046
    assert classes[2]["f1_score"] == 0.7368
    assert classes[2]["support"] == 87

    # Grade 3
    assert classes[3]["precision"] == 0.1667
    assert classes[3]["recall"] == 0.1765
    assert classes[3]["f1_score"] == 0.1714
    assert classes[3]["support"] == 17

    # Grade 4
    assert classes[4]["precision"] == 0.8333
    assert classes[4]["recall"] == 0.3030
    assert classes[4]["f1_score"] == 0.4444
    assert classes[4]["support"] == 33


def test_binary_metrics_original_threshold():
    """Verify binary metrics at original default operating point."""
    res = recompute_binary_metrics(CONFUSION_MATRIX_REFERABLE_ORIG)

    assert res["true_negatives"] == 219
    assert res["false_positives"] == 10
    assert res["false_negatives"] == 14
    assert res["true_positives"] == 123

    assert res["non_referable_support"] == 229
    assert res["referable_support"] == 137
    assert res["total_samples"] == 366

    assert res["sensitivity"] == 0.8978
    assert res["sensitivity_pct"] == 89.78
    assert res["specificity"] == 0.9563
    assert res["specificity_pct"] == 95.63
    assert res["precision"] == 0.9248
    assert res["precision_pct"] == 92.48
    assert res["binary_accuracy"] == 0.9344
    assert res["binary_accuracy_pct"] == 93.44


def test_binary_metrics_validation_selected_threshold():
    """Verify binary metrics at validation-selected threshold 0.1181."""
    res = recompute_binary_metrics(CONFUSION_MATRIX_REFERABLE_VAL_THRESH)

    assert res["true_negatives"] == 202
    assert res["false_positives"] == 27
    assert res["false_negatives"] == 1
    assert res["true_positives"] == 136

    assert res["non_referable_support"] == 229
    assert res["referable_support"] == 137

    assert res["sensitivity"] == 0.9927
    assert res["sensitivity_pct"] == 99.27
    assert res["specificity"] == 0.8821
    assert res["specificity_pct"] == 88.21
    assert res["precision"] == 0.8344
    assert res["precision_pct"] == 83.44
    assert res["binary_accuracy"] == 0.9235
    assert res["binary_accuracy_pct"] == 92.35


def test_threshold_metadata_and_provenance(workspace_root):
    """Verify threshold metadata, recovery source, and labeling."""
    data = build_final_clinical_evaluation(workspace_root)

    # Original threshold (0.50)
    ref_orig = data["referable_dr_original_threshold"]
    assert ref_orig["threshold"] == 0.50
    assert ref_orig["threshold_type"] == "default_operating_point"
    assert ref_orig["target_comparison"]["sensitivity_met"] is False
    assert ref_orig["target_comparison"]["specificity_met"] is True

    # Validation-selected threshold (0.1181)
    ref_val = data["referable_dr_validation_selected_threshold"]
    assert ref_val["threshold"] == 0.1181
    assert ref_val["threshold_type"] == "validation_selected_operating_point"
    assert ref_val["selection_split"] == "validation_data_only"
    assert ref_val["evaluation_split"] == "held_out_test"
    assert ref_val["target_comparison"]["sensitivity_met"] is True
    assert ref_val["target_comparison"]["specificity_met"] is True

    # Classifier active threshold (0.33)
    active = data["active_classifier_threshold"]
    assert active["threshold"] == 0.33
    assert "Cell 39" in active["provenance"]
    assert active["status"] == "FROZEN_ACTIVE_IN_CLASSIFIER"


def test_dataset_split_contamination_warning():
    """Verify formal contamination warning details and examples."""
    w = get_dataset_contamination_warning()

    assert w["warning_id"] == "DATASET_SPLIT_CONTAMINATION_DETECTED"
    assert w["severity"] == "CRITICAL"
    assert w["duplicate_hash_groups_count"] == 46
    assert w["same_label_duplicate_groups"] == 40
    assert w["conflicting_label_duplicate_groups"] == 6
    assert w["split_counts"]["total"] == 3662

    examples = w["conflicting_label_examples"]
    assert len(examples) == 6
    # Verify presence of key conflict types
    has_train_test_conflict = any(
        (e["split_a"] == "train" and e["split_b"] == "test")
        for e in examples
    )
    assert has_train_test_conflict is True


def test_integration_vs_clinical_distinction(workspace_root):
    """Verify 9-image integration set is distinct from clinical benchmark."""
    integ = get_integration_pipeline_evidence(workspace_root)

    assert integ["purpose"] == "SYSTEM_INTEGRATION_VERIFICATION"
    assert integ["clinical_benchmark_validity"] is False
    assert "MUST NOT" in integ["warning"]
    assert integ["total_images"] == 9
    assert integ["accepted_for_classification"] == 9
    assert integ["deterministic"] is True


def test_no_contradictory_metric_values(workspace_root):
    """Ensure mathematical consistency between 5-class and binary metrics."""
    data = build_final_clinical_evaluation(workspace_root)
    five = data["five_class_evaluation"]
    ref_orig = data["referable_dr_original_threshold"]["metrics"]
    ref_val = data["referable_dr_validation_selected_threshold"]["metrics"]

    # Grade 0 + Grade 1 supports must equal non-referable support
    grade_0_supp = five["per_class"][0]["support"]
    grade_1_supp = five["per_class"][1]["support"]
    non_ref_supp = grade_0_supp + grade_1_supp
    assert non_ref_supp == 229
    assert ref_orig["non_referable_support"] == non_ref_supp
    assert ref_val["non_referable_support"] == non_ref_supp

    # Grades 2 + 3 + 4 supports must equal referable support
    grade_2_supp = five["per_class"][2]["support"]
    grade_3_supp = five["per_class"][3]["support"]
    grade_4_supp = five["per_class"][4]["support"]
    ref_supp = grade_2_supp + grade_3_supp + grade_4_supp
    assert ref_supp == 137
    assert ref_orig["referable_support"] == ref_supp
    assert ref_val["referable_support"] == ref_supp

    # Total supports
    assert non_ref_supp + ref_supp == 366

    # Model never retrained
    assert data["model_metadata"]["retrained"] is False


def test_json_serializability_and_report_generation(workspace_root):
    """Verify JSON serialization and markdown report generation."""
    data = build_final_clinical_evaluation(workspace_root)

    # Must be JSON serializable without error
    dumped = json.dumps(data)
    assert len(dumped) > 0
    loaded = json.loads(dumped)
    assert loaded["overall_status"] == "VERIFIED_EXISTING_RESULTS"

    # Markdown generator
    md = generate_final_evaluation_markdown(data)
    assert "# Final Clinical Evaluation Audit" in md
    assert "Section A: Existing Model Evaluation" in md
    assert "Section B: Referable DR Screening" in md
    assert "Section C: Validation-Selected Threshold" in md
    assert "Section D: Dataset Leakage & Contamination" in md
    assert "Section E: Integrated Pipeline Evidence" in md
    assert "Section F: Limitations" in md
    assert "Section G: What Can and Cannot Legitimately Be Claimed" in md
    assert "Section H: Final Performance Summary Table" in md

    # File save
    json_path, md_path = save_final_evaluation_reports(workspace_root)
    assert json_path.exists() and json_path.stat().st_size > 0
    assert md_path.exists() and md_path.stat().st_size > 0


def test_invalid_matrix_dimensions_raise():
    """Verify invalid matrix inputs raise ValueError."""
    with pytest.raises(ValueError):
        recompute_5class_metrics([[1, 2], [3, 4]])

    with pytest.raises(ValueError):
        recompute_binary_metrics([[1, 2, 3], [4, 5, 6]])
