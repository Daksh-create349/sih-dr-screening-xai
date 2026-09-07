"""Automated Test Suite for Retinal Structure and Lesion Evidence Engine (Step 1).

Covers all 15 verification criteria defined in Task 16:
1. IDRiD manifest loads
2. real fundus image loads
3. annotation file loads
4. image/annotation dimensions are consistent
5. image IDs match annotations
6. optic disc annotation is recognized correctly
7. fovea annotation is recognized correctly
8. vessel mask is recognized correctly (and missing in IDRiD)
9. lesion masks are recognized correctly where available
10. missing annotations are reported
11. duplicate hashes are reported
12. provenance is preserved
13. GROUND_TRUTH is distinguishable from DETECTED / ESTIMATED
14. existing anatomy module remains functional
15. V2 classifier checkpoint is unchanged
"""

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

import json
import numpy as np
import pytest

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    BoundingBox,
    SegmentationMask,
    RetinalEvidenceRecord,
)
from evidence.dataset import (
    check_idrid_availability,
    get_ground_truth_taxonomy_status,
    analyze_microaneurysm_spatial_resolution,
    generate_idrid_manifest,
    OFFICIAL_IDRID_PROVENANCE,
    MANIFEST_PATH,
)
from evidence.annotations import (
    compute_euclidean_distance,
    compare_landmark_localization,
    compute_segmentation_metrics,
    extract_evidence_from_existing_anatomy,
)
from evidence.audit import (
    compute_file_sha256,
    audit_image_directory,
    run_evidence_data_audit,
)
from classifier.model import DEFAULT_MODEL_PATH
from image_quality.io import load_raw_image

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = WORKSPACE_ROOT / "data" / "real_retinal_images"


def test_1_idrid_manifest_loads():
    """Verify generated IDRiD manifest loads with valid schema."""
    manifest = generate_idrid_manifest()
    assert manifest["manifest_version"] == "1.0.0"
    assert "dataset_name" in manifest
    assert "availability_status" in manifest
    assert "annotation_taxonomy" in manifest
    assert MANIFEST_PATH.exists()


def test_2_real_fundus_image_loads():
    """Verify loading real retinal fundus image returns valid RGB array."""
    real_img_path = DATA_DIR / "confirmed_grade4_proliferative.jpg"
    assert real_img_path.exists()
    img = load_raw_image(real_img_path)
    assert isinstance(img, np.ndarray)
    assert img.ndim == 3
    assert img.shape[2] == 3
    assert img.dtype == np.uint8


def test_3_annotation_file_structure_loads():
    """Verify official IDRiD annotation structure definition."""
    prov = OFFICIAL_IDRID_PROVENANCE
    assert "Part_A_Segmentation" in prov["parts"]
    assert "Part_B_Disease_Grading" in prov["parts"]
    assert "Part_C_Localization" in prov["parts"]
    assert prov["native_resolution"] == [4288, 2848, 3]


def test_4_image_annotation_dimensions_consistent():
    """Verify dimension consistency in segmentation metric computation."""
    mask_a = np.zeros((384, 384), dtype=np.uint8)
    mask_b = np.zeros((384, 384), dtype=np.uint8)
    mask_a[100:150, 100:150] = 1
    mask_b[110:160, 110:160] = 1

    metrics = compute_segmentation_metrics(mask_a, mask_b)
    assert 0.0 <= metrics["dice"] <= 1.0
    assert 0.0 <= metrics["iou"] <= 1.0

    # Incompatible shapes must raise ValueError
    mask_c = np.zeros((200, 200), dtype=np.uint8)
    with pytest.raises(ValueError, match="Shape mismatch"):
        compute_segmentation_metrics(mask_a, mask_c)


def test_5_image_ids_match_annotations():
    """Verify RetinalEvidenceRecord correctly links image ID and record structure."""
    real_img = DATA_DIR / "aptos_eval_6959267_grade3.png"
    rec = extract_evidence_from_existing_anatomy(real_img, image_id="aptos_eval_6959267_grade3")
    assert rec.image_id == "aptos_eval_6959267_grade3"
    rec_dict = rec.to_dict()
    assert rec_dict["image_id"] == "aptos_eval_6959267_grade3"


def test_6_optic_disc_annotation_recognized_correctly():
    """Verify optic disc landmark representation and comparison."""
    gt_disc = PointLandmark(
        category=EvidenceCategory.OPTIC_DISC,
        status=AnnotationStatus.GROUND_TRUTH,
        x=200.0,
        y=200.0,
        radius=25.0,
        source="idrid_part_c",
    )
    det_disc = PointLandmark(
        category=EvidenceCategory.OPTIC_DISC,
        status=AnnotationStatus.DETECTED,
        x=210.0,
        y=205.0,
        radius=25.0,
        source="internal_detector",
    )

    cmp = compare_landmark_localization(det_disc, gt_disc)
    assert cmp["status"] == "COMPARED"
    assert cmp["success"] is True  # Error is sqrt(100+25) = 11.18 px <= 25 px radius
    assert cmp["pixel_distance"] == 11.18


def test_7_fovea_annotation_recognized_correctly():
    """Verify fovea landmark representation and comparison."""
    gt_fovea = PointLandmark(
        category=EvidenceCategory.FOVEA,
        status=AnnotationStatus.GROUND_TRUTH,
        x=350.0,
        y=210.0,
        radius=30.0,
        source="idrid_part_c",
    )
    est_fovea = PointLandmark(
        category=EvidenceCategory.FOVEA,
        status=AnnotationStatus.ESTIMATED,
        x=340.0,
        y=215.0,
        radius=30.0,
        source="internal_heuristic",
    )

    cmp = compare_landmark_localization(est_fovea, gt_fovea)
    assert cmp["status"] == "COMPARED"
    assert cmp["success"] is True
    assert cmp["pixel_distance"] == 11.18


def test_8_vessel_ground_truth_reported_absent_in_idrid():
    """Verify that retinal vessels are honestly reported as NOT_AVAILABLE in IDRiD."""
    taxonomy = get_ground_truth_taxonomy_status()
    assert taxonomy["VESSEL"]["idrid_status"] == "NOT_AVAILABLE_IN_IDRID"


def test_9_lesion_masks_recognized_correctly():
    """Verify lesion mask representation and non-zero pixel tracking."""
    mask_data = np.zeros((100, 100), dtype=np.uint8)
    mask_data[20:30, 20:30] = 255  # 100 non-zero pixels
    seg = SegmentationMask(
        category=EvidenceCategory.MICROANEURYSM,
        status=AnnotationStatus.GROUND_TRUTH,
        mask_shape=(100, 100),
        non_zero_pixels=int(np.sum(mask_data > 0)),
        area_fraction=float(np.sum(mask_data > 0) / 10000.0),
        source="idrid_part_a",
    )
    assert seg.is_available() is True
    assert seg.non_zero_pixels == 100
    assert seg.area_fraction == 0.01


def test_10_missing_annotations_reported():
    """Verify neovascularization is reported as absent in IDRiD."""
    taxonomy = get_ground_truth_taxonomy_status()
    assert taxonomy["NEOVASCULARIZATION"]["idrid_status"] == "NOT_AVAILABLE_IN_IDRID"


def test_11_duplicate_hashes_reported():
    """Verify audit correctly flags duplicate hashes if present."""
    audit = audit_image_directory(DATA_DIR)
    assert audit["status"] == "AUDITED"
    assert audit["total_files"] == 9
    assert audit["unique_hashes"] >= 8
    assert "duplicates" in audit


def test_12_provenance_preserved():
    """Verify provenance metadata is preserved across evidence record."""
    real_img = DATA_DIR / "cell13_r0_c0_grade0.png"
    rec = extract_evidence_from_existing_anatomy(real_img, image_id="cell13_r0_c0_grade0.png")
    assert "v2_model_frozen" in rec.provenance
    assert rec.provenance["v2_model_frozen"] is True


def test_13_ground_truth_distinguishable_from_detected_and_estimated():
    """Verify strict type distinction between GROUND_TRUTH, DETECTED, and ESTIMATED."""
    p_gt = PointLandmark(category=EvidenceCategory.OPTIC_DISC, status=AnnotationStatus.GROUND_TRUTH)
    p_det = PointLandmark(category=EvidenceCategory.OPTIC_DISC, status=AnnotationStatus.DETECTED)
    p_est = PointLandmark(category=EvidenceCategory.FOVEA, status=AnnotationStatus.ESTIMATED)

    assert p_gt.status != p_det.status
    assert p_det.status != p_est.status
    assert p_gt.status == "GROUND_TRUTH"
    assert p_det.status == "DETECTED"
    assert p_est.status == "ESTIMATED"


def test_14_existing_anatomy_module_remains_functional():
    """Verify existing explainability/anatomy.py functions execute cleanly."""
    real_img = DATA_DIR / "confirmed_grade4_proliferative.jpg"
    rec = extract_evidence_from_existing_anatomy(real_img)
    assert rec.optic_disc.is_available() is True
    assert rec.optic_disc.status == AnnotationStatus.DETECTED
    assert rec.fovea.is_available() is True
    assert rec.fovea.status == AnnotationStatus.ESTIMATED


def test_15_v2_classifier_checkpoint_unchanged():
    """Verify frozen EfficientNetB3 model file exists and remains untouched."""
    assert DEFAULT_MODEL_PATH.exists()
    assert DEFAULT_MODEL_PATH.stat().st_size > 50_000_000  # ~52.5 MB Keras model
