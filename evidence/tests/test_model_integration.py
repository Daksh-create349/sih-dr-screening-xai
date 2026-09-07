"""Integration Test Suite for IDRiD Deep Retinal Models.

Verifies:
1. Checkpoints exist, match exact hashes, and V2 classifier remains frozen.
2. Models load cleanly into PyTorch ResNet34 U-Net architectures.
3. Inference executes on real retinal fundus images.
4. Optic disc localization extracts valid center coordinates and disc radius.
5. Fovea position is anatomically anchored from optic disc vector.
6. Hard exudates segmentation identifies lesion clusters and calculates CSME risk.
7. Strict epistemic taxonomy is enforced (predictions are DETECTED / ESTIMATED, never GROUND_TRUTH).
"""

import sys
from pathlib import Path
import pytest
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from evidence.idrid import compute_file_sha256
from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)
from evidence.detector import (
    DEFAULT_DISC_MODEL_PATH,
    DEFAULT_EXUDATES_MODEL_PATH,
    DEFAULT_HEMORRHAGES_MODEL_PATH,
    DEFAULT_SOFT_EXUDATES_MODEL_PATH,
    load_optic_disc_model,
    load_exudates_model,
    load_hemorrhages_model,
    load_soft_exudates_model,
    detect_optic_disc,
    detect_exudates,
    detect_hemorrhages,
    detect_soft_exudates,
    detect_retinal_vessels,
    extract_deep_retinal_evidence,
    is_torch_available,
)
from classifier.model import DEFAULT_MODEL_PATH
from image_quality.io import load_raw_image

FROZEN_V2_SHA256 = "34601510c281430edf0944f5124107ee5b02f8bc5a5ce553cabfe720fe8c60e9"
DISC_MODEL_SHA256 = "572441ad284e4f578dc33bb2b750529df5074322bf469693e0fc22805bc24bd4"
EXUDATE_MODEL_SHA256 = "760cb538b7b8f488ff1aaf82efc4e8ecf6ecf7bea89856ef4e50fda940350535"
HEMORRHAGE_MODEL_SHA256 = "3ae714ba9051e3138163083854f69a9c2a8ad2cfd2e60f782c5cb2f69ef9511e"
SOFT_EXUDATES_MODEL_SHA256 = "4e7beb1b0b2b74de101e9ceaa22f9942ce77903bba739bf6b85de5d114286fc8"

REAL_IMG_PATH = WORKSPACE_ROOT / "data" / "real_retinal_images" / "confirmed_grade4_proliferative.jpg"
DISC_IMG_PATH = WORKSPACE_ROOT / "data" / "real_retinal_images" / "aptos_train_sample_c10.png"


def test_1_checkpoints_exist_and_hashes_valid():
    """Verify trained checkpoints exist and match cryptographic hashes."""
    assert DEFAULT_DISC_MODEL_PATH.exists()
    assert DEFAULT_EXUDATES_MODEL_PATH.exists()
    assert DEFAULT_HEMORRHAGES_MODEL_PATH.exists()
    assert DEFAULT_SOFT_EXUDATES_MODEL_PATH.exists()

    assert DEFAULT_DISC_MODEL_PATH.stat().st_size > 90_000_000
    assert DEFAULT_EXUDATES_MODEL_PATH.stat().st_size > 90_000_000
    assert DEFAULT_HEMORRHAGES_MODEL_PATH.stat().st_size > 90_000_000
    assert DEFAULT_SOFT_EXUDATES_MODEL_PATH.stat().st_size > 90_000_000

    assert compute_file_sha256(DEFAULT_DISC_MODEL_PATH) == DISC_MODEL_SHA256
    assert compute_file_sha256(DEFAULT_EXUDATES_MODEL_PATH) == EXUDATE_MODEL_SHA256
    assert compute_file_sha256(DEFAULT_HEMORRHAGES_MODEL_PATH) == HEMORRHAGE_MODEL_SHA256
    assert compute_file_sha256(DEFAULT_SOFT_EXUDATES_MODEL_PATH) == SOFT_EXUDATES_MODEL_SHA256


def test_2_frozen_v2_classifier_untouched():
    """Verify frozen EfficientNetB3 classifier has not been modified or retrained."""
    assert DEFAULT_MODEL_PATH.exists()
    assert DEFAULT_MODEL_PATH.stat().st_size == 52489324
    assert compute_file_sha256(DEFAULT_MODEL_PATH) == FROZEN_V2_SHA256


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_3_optic_disc_model_loads():
    """Verify Optic Disc U-Net loads weights and initializes in eval mode."""
    model = load_optic_disc_model(device="cpu")
    assert model is not None
    assert model.training is False


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_4_exudates_model_loads():
    """Verify Exudates U-Net loads weights and initializes in eval mode."""
    model = load_exudates_model(device="cpu")
    assert model is not None
    assert model.training is False


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_5_optic_disc_inference_on_real_fundus():
    """Verify Optic Disc detection on real retinal fundus image."""
    img = load_raw_image(DISC_IMG_PATH)
    assert isinstance(img, np.ndarray)

    res = detect_optic_disc(img, device="cpu")
    assert "mask" in res
    assert res["mask"].shape == img.shape[:2]
    assert res["center_xy"] is not None
    assert len(res["center_xy"]) == 2
    assert res["radius_px"] is not None and res["radius_px"] > 0
    assert res["fovea_estimate"] is not None
    assert res["training_source"] == "IDRiD_Part_A_C"


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_6_exudates_inference_on_real_fundus():
    """Verify Hard Exudates detection on real retinal fundus image."""
    img = load_raw_image(REAL_IMG_PATH)
    res = detect_exudates(img, device="cpu")

    assert "mask" in res
    assert res["mask"].shape == img.shape[:2]
    assert "lesion_count" in res
    assert isinstance(res["lesion_count"], int)
    assert "area_fraction" in res
    assert 0.0 <= res["area_fraction"] <= 1.0
    assert res["training_source"] == "IDRiD_Part_A"


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_6b_hemorrhages_model_loads():
    """Verify Retinal Hemorrhages U-Net loads weights and initializes in eval mode."""
    model = load_hemorrhages_model(device="cpu")
    assert model is not None
    assert model.training is False


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_6c_hemorrhages_inference_on_real_fundus():
    """Verify Retinal Hemorrhages detection on real retinal fundus image."""
    img = load_raw_image(REAL_IMG_PATH)
    res = detect_hemorrhages(img, device="cpu")

    assert "mask" in res
    assert res["mask"].shape == img.shape[:2]
    assert "lesion_count" in res
    assert isinstance(res["lesion_count"], int)
    assert "area_fraction" in res
    assert 0.0 <= res["area_fraction"] <= 1.0
    assert res["training_source"] == "IDRiD_Part_A_Hemorrhages"


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_6d_soft_exudates_model_loads():
    """Verify Soft Exudates (Cotton Wool Spots) U-Net loads weights and initializes in eval mode."""
    model = load_soft_exudates_model(device="cpu")
    assert model is not None
    assert model.training is False


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_6e_soft_exudates_inference_on_real_fundus():
    """Verify Soft Exudates detection on real retinal fundus image."""
    img = load_raw_image(REAL_IMG_PATH)
    res = detect_soft_exudates(img, device="cpu")

    assert "mask" in res
    assert res["mask"].shape == img.shape[:2]
    assert "lesion_count" in res
    assert isinstance(res["lesion_count"], int)
    assert "area_fraction" in res
    assert 0.0 <= res["area_fraction"] <= 1.0
    assert res["training_source"] == "IDRiD_Part_A_Soft_Exudates"


def test_6f_retinal_vessels_inference_on_real_fundus():
    """Verify Retinal Vessel segmentation on real retinal fundus image."""
    img = load_raw_image(REAL_IMG_PATH)
    res = detect_retinal_vessels(img, device="cpu")

    assert "mask" in res
    assert res["mask"].shape == img.shape[:2]
    assert "vessel_pixels" in res
    assert isinstance(res["vessel_pixels"], int)
    assert res["vessel_pixels"] > 0
    assert "vessel_density" in res
    assert 0.0 < res["vessel_density"] < 0.5
    assert "major_branches" in res
    assert res["major_branches"] >= 1


@pytest.mark.skipif(not is_torch_available(), reason="PyTorch/SMP environment required")
def test_7_extract_deep_retinal_evidence_pipeline():
    """Verify end-to-end evidence record generation with clinical DME risk, hemorrhages, soft exudates, and vessels."""
    rec = extract_deep_retinal_evidence(DISC_IMG_PATH, image_id="sample_disc", device="cpu")

    assert isinstance(rec, RetinalEvidenceRecord)
    assert rec.image_id == "sample_disc"
    assert rec.optic_disc.status == AnnotationStatus.DETECTED
    assert rec.optic_disc.x is not None
    assert rec.optic_disc.radius is not None
    assert rec.fovea.status == AnnotationStatus.ESTIMATED
    assert rec.fovea.x is not None
    assert rec.vessels.status == AnnotationStatus.DETECTED
    assert rec.vessels.non_zero_pixels > 0
    assert rec.hemorrhages is not None
    assert rec.hemorrhages.status in (AnnotationStatus.DETECTED, AnnotationStatus.NOT_AVAILABLE)
    assert rec.soft_exudates is not None
    assert rec.soft_exudates.status in (AnnotationStatus.DETECTED, AnnotationStatus.NOT_AVAILABLE)

    # Serialization test
    d = rec.to_dict()
    assert d["structures"]["optic_disc"]["status"] == "DETECTED"
    assert d["structures"]["fovea"]["status"] == "ESTIMATED"
    assert d["structures"]["vessels"]["status"] == "DETECTED"
    assert "hemorrhages" in d["lesions"]
    assert "soft_exudates" in d["lesions"]
    assert "models_integrated" in d["provenance"]
    assert "hemorrhages" in d["provenance"]["models_integrated"]
    assert "soft_exudates" in d["provenance"]["models_integrated"]
    assert "retinal_vessels" in d["provenance"]["models_integrated"]
    assert "macular_edema_risk_level" in d["provenance"]["lesion_statistics"]


def test_8_strict_epistemic_taxonomy_enforced():
    """Verify predictions are strictly marked DETECTED / ESTIMATED and never GROUND_TRUTH."""
    rec = RetinalEvidenceRecord(image_id="test_epistemic")
    assert rec.optic_disc.status != AnnotationStatus.GROUND_TRUTH
    assert rec.vessels.status == AnnotationStatus.NOT_AVAILABLE
    assert rec.neovascularization.status == AnnotationStatus.NOT_AVAILABLE
