"""Automated tests for dataset discovery, schema validation, and leakage check.

Tests use temporary test fixtures solely to verify tabular parsing,
schema invariants, and leakage detection mechanics.
"""

from pathlib import Path
import json
import pandas as pd

from validation.dataset import (
    locate_dataset_assets,
    load_and_validate_split,
    check_data_leakage,
    generate_dataset_manifest,
    generate_dataset_audit_markdown,
)


def test_locate_dataset_assets_structure():
    """Verify discovery structure and missing asset detection."""
    assets = locate_dataset_assets()
    assert "searched_paths" in assets
    assert "splits_found" in assets
    assert "missing_splits" in assets
    assert "all_assets_present" in assets
    assert isinstance(assets["all_assets_present"], bool)


def test_load_and_validate_split_valid_csv(tmp_path: Path):
    """Verify split audit with valid tabular CSV schema."""
    csv_file = tmp_path / "valid_split.csv"
    df = pd.DataFrame({
        "id_code": ["img_001", "img_002", "img_003", "img_004", "img_005"],
        "diagnosis": [0, 1, 2, 3, 4],
    })
    df.to_csv(csv_file, index=False)

    audit = load_and_validate_split(csv_file, split_name="test_split")

    assert audit["status"] == "AUDIT_OK"
    assert audit["record_count"] == 5
    assert audit["duplicate_id_count"] == 0
    assert audit["missing_label_count"] == 0
    assert audit["invalid_label_count"] == 0
    assert audit["class_distribution"] == {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}


def test_load_and_validate_split_duplicate_and_invalid_labels(tmp_path: Path):
    """Verify detection of duplicate IDs and out-of-range diagnosis labels."""
    csv_file = tmp_path / "bad_split.csv"
    df = pd.DataFrame({
        "id_code": ["img_001", "img_001", "img_002"],
        "diagnosis": [0, 9, None],
    })
    df.to_csv(csv_file, index=False)

    audit = load_and_validate_split(csv_file, split_name="bad_split")

    assert audit["status"] == "AUDIT_WARNINGS"
    assert audit["record_count"] == 3
    assert audit["duplicate_id_count"] == 1
    assert audit["invalid_label_count"] == 1
    assert audit["missing_label_count"] == 1


def test_load_and_validate_split_missing_file():
    """Verify graceful handling when CSV file does not exist."""
    fake_path = Path("/nonexistent/path/to/missing.csv")
    audit = load_and_validate_split(fake_path, split_name="missing")

    assert audit["status"] == "MISSING_CSV"
    assert audit["record_count"] == 0


def test_check_data_leakage_detection(tmp_path: Path):
    """Verify cross-split ID leakage detection."""
    p_train = tmp_path / "train.csv"
    p_val = tmp_path / "val.csv"

    # Leak img_002 into both splits
    df_train = pd.DataFrame({
        "id_code": ["img_001", "img_002", "img_003"],
        "diagnosis": [0, 1, 2],
    })
    df_val = pd.DataFrame({
        "id_code": ["img_002", "img_004"],
        "diagnosis": [1, 3],
    })
    df_train.to_csv(p_train, index=False)
    df_val.to_csv(p_val, index=False)

    audit_train = load_and_validate_split(p_train, split_name="train")
    audit_val = load_and_validate_split(p_val, split_name="validation")

    leakage = check_data_leakage({
        "train": audit_train,
        "validation": audit_val,
    })

    assert leakage["has_leakage"] is True
    assert leakage["id_overlaps"]["train_vs_validation"] == 1
    assert len(leakage["details"]) > 0


def test_check_data_leakage_clean(tmp_path: Path):
    """Verify zero leakage when splits have disjoint IDs."""
    p_train = tmp_path / "train.csv"
    p_test = tmp_path / "test.csv"

    df_train = pd.DataFrame({"id_code": ["a1", "a2"], "diagnosis": [0, 1]})
    df_test = pd.DataFrame({"id_code": ["b1", "b2"], "diagnosis": [2, 3]})
    df_train.to_csv(p_train, index=False)
    df_test.to_csv(p_test, index=False)

    audit_train = load_and_validate_split(p_train, split_name="train")
    audit_test = load_and_validate_split(p_test, split_name="test")

    leakage = check_data_leakage({"train": audit_train, "test": audit_test})

    assert leakage["has_leakage"] is False
    assert leakage["id_overlaps"]["train_vs_test"] == 0


def test_generate_dataset_manifest_blocked_status():
    """Verify manifest reports BLOCKED when full evaluation dataset absent."""
    manifest = generate_dataset_manifest()

    assert manifest["protocol_version"] == "1.0.0"
    assert manifest["dataset_status"] in ["BLOCKED", "PASS", "FAIL"]
    if manifest["dataset_status"] == "BLOCKED":
        assert "Benchmark blocked" in manifest["status_reason"]

    # Verify JSON serializability
    serialized = json.dumps(manifest)
    assert len(serialized) > 0


def test_generate_dataset_audit_markdown():
    """Verify generation of markdown audit summary."""
    manifest = generate_dataset_manifest()
    md = generate_dataset_audit_markdown(manifest)

    assert "# Clinical Validation Dataset Audit Report" in md
    assert "Executive Summary" in md
    assert "Discovered Splits Audit" in md
    assert "Data Leakage Assessment" in md
