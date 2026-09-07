"""Test Suite for MODULE 1A — IDRiD Dataset Staging Contract.

Verifies all 12 contractual requirements:
1. root discovery (CLI arg -> env var -> config -> default)
2. missing-root behavior ('IDRiD DATASET NOT FOUND')
3. manifest generation (includes image ID, path, split, dimensions, annotations, checksum, flags)
4. image discovery (locates raw IDRiD images, ignores masks)
5. annotation discovery (finds OD, fovea, MA, hard/soft exudates, hemorrhages)
6. image/annotation matching (maps image ID to corresponding masks)
7. checksum generation (SHA-256 hashing)
8. split identification (train vs test partition assignment)
9. provenance preservation (IEEE DataPort, Kowa VX-10alpha, native resolution)
10. no synthetic fallback (no fake masks, no synthetic images, no APTOS substitution)
11. IDRiD/DRIVE separation (distinct dirs, VESSEL and NEOVASCULARIZATION flagged as EXTERNAL_DATASET_REQUIRED)
12. V2 checkpoint remains untouched (exact frozen hash and byte size preserved)
"""

import hashlib
import json
import os
import sys
from pathlib import Path
import pytest
from PIL import Image

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from evidence.idrid import (
    IDRiDDataset,
    IDRiDNotFoundError,
    resolve_idrid_root,
    compute_file_sha256,
    GROUND_TRUTH,
    DETECTED,
    ESTIMATED,
    NOT_AVAILABLE,
    EXTERNAL_DATASET_REQUIRED,
    OPTIC_DISC,
    FOVEA,
    MICROANEURYSM,
    HARD_EXUDATE,
    SOFT_EXUDATE,
    HEMORRHAGE,
    VESSEL,
    NEOVASCULARIZATION,
    IDRID_SUPPORTED_CATEGORIES,
    EXTERNAL_REQUIRED_CATEGORIES,
    OFFICIAL_IDRID_PROVENANCE,
    DEFAULT_LOCAL_IDRID_DIR,
)
from classifier.model import DEFAULT_MODEL_PATH

FROZEN_V2_SHA256 = "34601510c281430edf0944f5124107ee5b02f8bc5a5ce553cabfe720fe8c60e9"
FROZEN_V2_SIZE = 52489324


@pytest.fixture
def mock_idrid_structure(tmp_path):
    """Minimal structural fixture to test parser and loader behavior.

    Does not contain clinical data or claim clinical performance.
    """
    root = tmp_path / "IDRiD_mock"
    train_imgs = root / "A. Segmentation" / "1. Original Images" / "a. Training Set"
    test_imgs = root / "A. Segmentation" / "1. Original Images" / "b. Testing Set"
    train_masks_ma = root / "A. Segmentation" / "2. Groundtruths" / "a. Training Set" / "1. Microaneurysms"
    train_masks_od = root / "A. Segmentation" / "2. Groundtruths" / "a. Training Set" / "5. Optic Disc"
    train_masks_ex = root / "A. Segmentation" / "2. Groundtruths" / "a. Training Set" / "3. Hard Exudates"

    for d in [train_imgs, test_imgs, train_masks_ma, train_masks_od, train_masks_ex]:
        d.mkdir(parents=True, exist_ok=True)

    # Create dummy images (small 32x32 RGB)
    im1 = Image.new("RGB", (32, 32), color=(100, 50, 20))
    im1.save(train_imgs / "IDRiD_01.jpg")

    im2 = Image.new("RGB", (32, 32), color=(110, 55, 25))
    im2.save(test_imgs / "IDRiD_55.jpg")

    # Create dummy masks (small 32x32 L)
    m1 = Image.new("L", (32, 32), color=0)
    m1.save(train_masks_ma / "IDRiD_01_MA.tif")

    m2 = Image.new("L", (32, 32), color=0)
    m2.save(train_masks_od / "IDRiD_01_OD.tif")

    m3 = Image.new("L", (32, 32), color=0)
    m3.save(train_masks_ex / "IDRiD_01_EX.tif")

    return root


def test_1_root_discovery(tmp_path, monkeypatch):
    """Verify root resolution priority: CLI arg -> env var -> config file -> default."""
    custom_cli = tmp_path / "cli_path"
    custom_env = tmp_path / "env_path"
    custom_cfg_dir = tmp_path / "cfg_path"
    cfg_file = tmp_path / "dataset_config.json"

    with open(cfg_file, "w") as f:
        json.dump({"IDRID_ROOT": str(custom_cfg_dir)}, f)

    # 1. CLI argument wins over env var and config
    monkeypatch.setenv("IDRID_ROOT", str(custom_env))
    resolved = resolve_idrid_root(cli_arg=custom_cli, config_file=cfg_file)
    assert resolved == custom_cli.resolve()

    # 2. Env var wins when CLI is None
    resolved = resolve_idrid_root(cli_arg=None, config_file=cfg_file)
    assert resolved == custom_env.resolve()

    # 3. Config file wins when env var and CLI are unset
    monkeypatch.delenv("IDRID_ROOT", raising=False)
    resolved = resolve_idrid_root(cli_arg=None, config_file=cfg_file)
    assert resolved == custom_cfg_dir.resolve()

    # 4. Default fallback when no overrides
    resolved = resolve_idrid_root(cli_arg=None, config_file=tmp_path / "nonexistent.json")
    assert resolved == DEFAULT_LOCAL_IDRID_DIR.resolve()


def test_2_missing_root_behavior(tmp_path):
    """Verify missing or empty root raises IDRiDNotFoundError with exact message."""
    nonexistent = tmp_path / "nonexistent_dir"
    with pytest.raises(IDRiDNotFoundError, match="IDRiD DATASET NOT FOUND"):
        IDRiDDataset(root=nonexistent, require_exists=True)

    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(IDRiDNotFoundError, match="IDRiD DATASET NOT FOUND"):
        IDRiDDataset(root=empty_dir, require_exists=True)


def test_3_manifest_generation(mock_idrid_structure, tmp_path):
    """Verify manifest generator includes all required fields."""
    ds = IDRiDDataset(root=mock_idrid_structure, require_exists=True)
    manifest_out = tmp_path / "test_manifest.json"
    manifest = ds.generate_manifest(output_path=manifest_out)

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["dataset_status"] == "AVAILABLE"
    assert manifest["available_locally"] is True
    assert manifest["total_images"] == 2
    assert len(manifest["images"]) == 2

    first = manifest["images"][0]
    required_fields = [
        "image_id",
        "image_path",
        "split",
        "image_width",
        "image_height",
        "available_annotations",
        "annotation_paths",
        "checksum",
        "missing_annotation_flags",
    ]
    for field in required_fields:
        assert field in first, f"Missing field {field} in manifest record"

    assert first["image_width"] == 32
    assert first["image_height"] == 32
    assert len(first["checksum"]) == 64  # Valid SHA-256 hex string


def test_4_image_discovery(mock_idrid_structure):
    """Verify raw images are discovered and masks are excluded from raw images list."""
    ds = IDRiDDataset(root=mock_idrid_structure, require_exists=True)
    images = ds.discover_images()

    image_ids = [img["image_id"] for img in images]
    assert "IDRiD_01" in image_ids or "IDRiD_1" in image_ids
    assert "IDRiD_55" in image_ids

    # Mask files must NOT be in discovered raw images
    for img in images:
        assert "_MA" not in img["filename"]
        assert "_OD" not in img["filename"]
        assert "_EX" not in img["filename"]


def test_5_annotation_discovery(mock_idrid_structure):
    """Verify annotation discovery categorizes masks into supported taxonomy categories."""
    ds = IDRiDDataset(root=mock_idrid_structure, require_exists=True)
    ann = ds.discover_annotations()

    for cat in IDRID_SUPPORTED_CATEGORIES:
        assert cat in ann

    assert len(ann[MICROANEURYSM]["train"]) == 1
    assert len(ann[OPTIC_DISC]["train"]) == 1
    assert len(ann[HARD_EXUDATE]["train"]) == 1


def test_6_image_annotation_matching(mock_idrid_structure):
    """Verify image ID matches corresponding masks and records missing flags."""
    ds = IDRiDDataset(root=mock_idrid_structure, require_exists=True)
    match_01 = ds.match_image_annotations("IDRiD_01")

    assert MICROANEURYSM in match_01["available_annotations"]
    assert OPTIC_DISC in match_01["available_annotations"]
    assert HARD_EXUDATE in match_01["available_annotations"]
    assert match_01["missing_annotation_flags"][MICROANEURYSM] is False
    assert match_01["missing_annotation_flags"][HEMORRHAGE] is True

    # External dataset required must always be flagged as missing/external
    assert match_01["missing_annotation_flags"]["VESSEL"] is True
    assert match_01["missing_annotation_flags"]["NEOVASCULARIZATION"] is True


def test_7_checksum_generation(tmp_path):
    """Verify SHA-256 checksum generation accurately hashes file contents."""
    sample_file = tmp_path / "sample.bin"
    sample_content = b"IDRiD_RETINAL_VERIFICATION_SAMPLE_DATA_2026"
    sample_file.write_bytes(sample_content)

    expected_sha = hashlib.sha256(sample_content).hexdigest()
    computed_sha = compute_file_sha256(sample_file)
    assert computed_sha == expected_sha


def test_8_split_identification(mock_idrid_structure):
    """Verify train vs test split identification from folder paths."""
    ds = IDRiDDataset(root=mock_idrid_structure, require_exists=True)
    images = ds.discover_images()

    split_by_id = {img["image_id"]: img["split"] for img in images}
    # IDRiD_01 is in Training Set
    key_01 = "IDRiD_01" if "IDRiD_01" in split_by_id else "IDRiD_1"
    assert split_by_id[key_01] == "train"
    # IDRiD_55 is in Testing Set
    assert split_by_id["IDRiD_55"] == "test"


def test_9_provenance_preservation():
    """Verify official IDRiD provenance metadata is intact and preserved."""
    prov = OFFICIAL_IDRID_PROVENANCE
    assert prov["camera"] == "Kowa VX-10alpha digital fundus camera"
    assert prov["field_of_view_deg"] == 50
    assert prov["native_resolution"] == [4288, 2848, 3]
    assert "Part_A_Segmentation" in prov["parts"]
    assert "Part_B_Disease_Grading" in prov["parts"]
    assert "Part_C_Localization" in prov["parts"]


def test_10_no_synthetic_fallback(tmp_path):
    """Verify that when dataset is absent, loader NEVER fabricates data or uses APTOS."""
    empty_root = tmp_path / "empty_root"
    empty_root.mkdir()

    ds = IDRiDDataset(root=empty_root, require_exists=False)
    assert ds.is_available() is False

    # Generate manifest on missing dataset
    manifest = ds.generate_manifest(output_path=tmp_path / "missing_manifest.json")
    assert manifest["dataset_status"] == "IDRiD DATASET NOT FOUND"
    assert manifest["available_locally"] is False
    assert manifest["total_images"] == 0
    assert manifest["images"] == []

    # Calling require_exists fails explicitly
    with pytest.raises(IDRiDNotFoundError, match="IDRiD DATASET NOT FOUND"):
        ds.validate_dataset_present()


def test_11_idrid_drive_separation():
    """Verify IDRiD and DRIVE paths are separated and external requirements are enforced."""
    idrid_dir = WORKSPACE_ROOT / "data" / "external" / "IDRiD"
    drive_dir = WORKSPACE_ROOT / "data" / "external" / "DRIVE"

    assert idrid_dir.resolve() != drive_dir.resolve()
    assert idrid_dir.exists()
    assert drive_dir.exists()

    # Verify VESSEL and NEOVASCULARIZATION are strictly external requirements
    assert VESSEL == EXTERNAL_DATASET_REQUIRED
    assert NEOVASCULARIZATION == EXTERNAL_DATASET_REQUIRED
    assert "VESSEL" in EXTERNAL_REQUIRED_CATEGORIES
    assert "NEOVASCULARIZATION" in EXTERNAL_REQUIRED_CATEGORIES


def test_12_v2_checkpoint_remains_untouched():
    """Verify frozen EfficientNetB3 model file exists and is byte-identical."""
    assert DEFAULT_MODEL_PATH.exists()
    assert DEFAULT_MODEL_PATH.stat().st_size == FROZEN_V2_SIZE
    computed_hash = compute_file_sha256(DEFAULT_MODEL_PATH)
    assert computed_hash == FROZEN_V2_SHA256
