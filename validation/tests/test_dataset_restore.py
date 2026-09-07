"""Unit tests for APTOS 2019 dataset recovery and limit enforcement."""

import json
from pathlib import Path
import tempfile
import pytest
import pandas as pd
import numpy as np
import cv2

from validation.dataset import (
    MAX_DOWNLOAD_LIMIT_BYTES,
    get_available_disk_space,
    check_download_eligibility,
    enforce_download_limit,
    scan_local_aptos_assets,
    load_and_validate_split,
    check_data_leakage,
    generate_dataset_provenance,
    generate_restored_dataset_manifest,
    generate_restored_dataset_audit_markdown,
)


def test_hard_download_limit_constant():
    """Verify download limit is strictly 500 MB."""
    expected_limit = 500 * 1024 * 1024  # 524,288,000 bytes
    assert MAX_DOWNLOAD_LIMIT_BYTES == expected_limit
    assert MAX_DOWNLOAD_LIMIT_BYTES / (1024 * 1024) == 500.0


def test_no_permitted_download_size_over_500mb():
    """Ensure no download request exceeding 500 MB is permitted."""
    # Test boundary conditions
    boundary_exact = MAX_DOWNLOAD_LIMIT_BYTES
    boundary_over = MAX_DOWNLOAD_LIMIT_BYTES + 1
    large_archive = 9_500_000_000  # 9.5 GB Kaggle archive

    res_exact = check_download_eligibility(boundary_exact)
    assert res_exact["eligible"] is True
    assert res_exact["status"] == "PERMITTED"

    res_over = check_download_eligibility(boundary_over)
    assert res_over["eligible"] is False
    assert res_over["status"] == "BLOCKED"
    assert "exceeds hard 500 MB download limit" in res_over["reason"]

    res_large = check_download_eligibility(
        large_archive, "kaggle_full_dataset"
    )
    assert res_large["eligible"] is False
    assert res_large["status"] == "BLOCKED"

    # Verify enforcement exception
    with pytest.raises(ValueError, match="HARD RESOURCE LIMIT VIOLATION"):
        enforce_download_limit(boundary_over)

    with pytest.raises(ValueError, match="HARD RESOURCE LIMIT VIOLATION"):
        enforce_download_limit(large_archive)

    # Permitted sizes should not raise
    enforce_download_limit(100 * 1024 * 1024)
    enforce_download_limit(boundary_exact)


def test_available_disk_space_check():
    """Verify disk space inspection returns valid positive numbers."""
    disk = get_available_disk_space(".")
    assert "total_bytes" in disk
    assert "used_bytes" in disk
    assert "free_bytes" in disk
    assert "free_gb" in disk
    assert disk["free_bytes"] > 0
    assert disk["free_gb"] > 0.0


def test_scan_local_aptos_assets():
    """Verify local asset scanning discovers known retinal files."""
    assets = scan_local_aptos_assets()
    assert isinstance(assets, list)
    assert len(assets) > 0

    found_names = [a["filename"] for a in assets]
    # Check known integration sample is discovered
    assert any("aptos" in name.lower() for name in found_names)

    for a in assets:
        assert "path" in a
        assert "filename" in a
        assert "size_bytes" in a
        assert "file_type" in a
        assert "has_labels" in a
        assert a["size_bytes"] > 0


def test_csv_schema_and_diagnosis_validation():
    """Test tabular schema, missing label, and diagnosis range checking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        csv_file = tmp_path / "valid_split.csv"

        # Valid split
        df_valid = pd.DataFrame({
            "id_code": ["img_001", "img_002", "img_003"],
            "diagnosis": [0, 2, 4],
        })
        df_valid.to_csv(csv_file, index=False)

        audit = load_and_validate_split(csv_file, split_name="test_split")
        assert audit["status"] == "AUDIT_OK"
        assert audit["record_count"] == 3
        assert audit["invalid_label_count"] == 0
        assert audit["missing_label_count"] == 0
        assert audit["class_distribution"][0] == 1
        assert audit["class_distribution"][2] == 1
        assert audit["class_distribution"][4] == 1

        # Invalid diagnosis values
        csv_invalid = tmp_path / "invalid_split.csv"
        df_invalid = pd.DataFrame({
            "id_code": ["img_010", "img_011", "img_012"],
            "diagnosis": [0, 5, -1],  # 5 and -1 are invalid
        })
        df_invalid.to_csv(csv_invalid, index=False)

        audit_inv = load_and_validate_split(
            csv_invalid, split_name="inv_split"
        )
        assert audit_inv["invalid_label_count"] == 2
        assert audit_inv["status"] == "AUDIT_WARNINGS"

        # Missing required columns
        csv_bad_schema = tmp_path / "bad_schema.csv"
        df_bad = pd.DataFrame({"random_col": [1, 2, 3]})
        df_bad.to_csv(csv_bad_schema, index=False)

        audit_bad = load_and_validate_split(csv_bad_schema, split_name="bad")
        assert audit_bad["status"] == "INVALID_SCHEMA"


def test_image_resolution_and_missing_detection():
    """Test resolution of image paths and missing file reporting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Create one real image file
        img_file = images_dir / "img_real.png"
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(img_file), dummy_img)

        # CSV references 2 images: one present, one missing
        csv_path = tmp_path / "labels.csv"
        df = pd.DataFrame({
            "id_code": ["img_real", "img_missing"],
            "diagnosis": [0, 1],
        })
        df.to_csv(csv_path, index=False)

        audit = load_and_validate_split(
            csv_path, images_dir=images_dir, split_name="test"
        )
        assert audit["images_resolved"] == 1
        assert audit["images_missing"] == 1
        assert audit["status"] == "AUDIT_WARNINGS"


def test_duplicate_id_detection():
    """Test duplicate image IDs detection within a split."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        csv_path = tmp_path / "duplicates.csv"
        df = pd.DataFrame({
            "id_code": ["dup_001", "dup_001", "dup_002"],
            "diagnosis": [1, 1, 2],
        })
        df.to_csv(csv_path, index=False)

        audit = load_and_validate_split(csv_path, split_name="dup_test")
        assert audit["duplicate_id_count"] == 1
        assert audit["status"] == "AUDIT_WARNINGS"


def test_split_leakage_checks():
    """Verify cross-split leakage detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        train_csv = tmp_path / "train.csv"
        test_csv = tmp_path / "test.csv"

        # Case 1: Leakage present (shared_001 in both)
        pd.DataFrame({
            "id_code": ["train_001", "shared_001"],
            "diagnosis": [0, 1],
        }).to_csv(train_csv, index=False)

        pd.DataFrame({
            "id_code": ["test_001", "shared_001"],
            "diagnosis": [0, 1],
        }).to_csv(test_csv, index=False)

        split_audits = {
            "train": {"csv_path": str(train_csv), "id_column": "id_code"},
            "test": {"csv_path": str(test_csv), "id_column": "id_code"},
        }
        leakage = check_data_leakage(split_audits)
        assert leakage["has_leakage"] is True
        assert leakage["id_overlaps"]["train_vs_test"] == 1

        # Case 2: Clean separation
        pd.DataFrame({
            "id_code": ["test_clean_001"],
            "diagnosis": [2],
        }).to_csv(test_csv, index=False)

        clean_leakage = check_data_leakage(split_audits)
        assert clean_leakage["has_leakage"] is False
        assert clean_leakage["id_overlaps"]["train_vs_test"] == 0


def test_provenance_structure():
    """Verify structure and fields of dataset provenance."""
    prov = generate_dataset_provenance(
        source="Test Source",
        source_url="https://example.com/data",
        local_path="/path/to/data",
        original_file_size_bytes=400 * 1024 * 1024,
        downloaded_size_bytes=400 * 1024 * 1024,
        extraction_status="EXTRACTED",
        image_count=3662,
        label_count=3662,
        completeness_status="PASS",
    )

    assert prov["source"] == "Test Source"
    assert prov["download_used_mb"] == 400.0
    assert prov["hard_download_limit_mb"] == 500.0
    assert prov["download_limit_respected"] is True
    assert prov["dataset_completeness_status"] == "PASS"
    assert prov["image_count"] == 3662
    assert prov["label_count"] == 3662


def test_restored_manifest_serialization():
    """Test full restored dataset manifest serialization and completeness."""
    manifest = generate_restored_dataset_manifest()
    serialized = json.dumps(manifest, indent=2)
    assert len(serialized) > 0

    assert "protocol_version" in manifest
    assert "overall_status" in manifest
    assert "download_limit_mb" in manifest
    assert manifest["download_limit_mb"] == 500.0
    assert "provenance" in manifest
    assert "exact_files_found" in manifest
    assert "disk_space" in manifest


def test_restored_dataset_audit_markdown():
    """Test human-readable markdown generation for restored dataset audit."""
    manifest = generate_restored_dataset_manifest()
    md = generate_restored_dataset_audit_markdown(manifest)
    assert "# APTOS 2019 Dataset Recovery & Integrity Audit Report" in md
    assert "Dataset Status" in md
    assert "Discovered Local Assets" in md
    assert "Authentic Source Evaluation" in md
    assert "500 MB Limit Check" in md
