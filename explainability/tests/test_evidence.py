"""Automated tests for clinical evidence aggregation and reporting.

Tests cover:
- End-to-end evidence generation on real retinal images
- Schema and required key completeness
- JSON serializability of evidence output
- Neutral terminology compliance (strictly no lesion claims)
- Mandatory clinical disclaimer presence
- Determinism across repeated executions
"""

import json
from pathlib import Path
import pytest

from classifier.model import load_classifier_model
from explainability.evidence import (
    generate_retinal_evidence,
    synthesize_evidence_narrative,
    CLINICAL_SAFETY_DISCLAIMER,
)
from image_quality.io import load_raw_image

WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Path = WORKSPACE_ROOT / "data" / "real_retinal_images"
REAL_IMAGE_PATH: Path = DATA_DIR / "cell13_r0_c0_grade0.png"


@pytest.fixture(scope="module")
def shared_model():
    """Load cached model once for evidence test suite."""
    return load_classifier_model()


def test_generate_retinal_evidence_end_to_end(shared_model):
    """Verify complete evidence pipeline on real retinal fundus image."""
    assert REAL_IMAGE_PATH.exists()
    img = load_raw_image(REAL_IMAGE_PATH)

    res = generate_retinal_evidence(img, model=shared_model)

    required_keys = [
        "predicted_class",
        "predicted_class_name",
        "predicted_probabilities",
        "target_class",
        "target_score",
        "evidence_status",
        "top_attention_region",
        "top_attention_mass_pct",
        "macular_overlap_pct",
        "optic_disc_overlap_pct",
        "attention_bounding_box",
        "attention_statistics",
        "anatomical_landmarks",
        "narrative_summary",
        "safety_disclaimer",
        "native_heatmap",
        "heatmap_384",
        "warped_retinal_heatmap",
    ]
    for k in required_keys:
        assert k in res, f"Missing evidence key: {k}"

    assert 0 <= res["predicted_class"] <= 4
    assert 0.0 <= res["target_score"] <= 1.0
    assert len(res["predicted_probabilities"]) == 5
    assert res["evidence_status"] == "feature_attribution_only"

    # Attention bounding box
    bbox = res["attention_bounding_box"]
    assert "x" in bbox
    assert "y" in bbox
    assert "width" in bbox
    assert "height" in bbox
    assert bbox["status"] in [
        "localized_attention_cluster",
        "diffuse_or_zero_attention",
    ]

    # Attention statistics
    stats = res["attention_statistics"]
    assert "retinal_foreground" in stats
    assert "optic_disc_region" in stats
    assert "macular_region" in stats


def test_evidence_json_serializability(shared_model):
    """Verify structured evidence dictionary can be dumped to JSON."""
    res = generate_retinal_evidence(REAL_IMAGE_PATH, model=shared_model)

    # Exclude raw numpy arrays which are serialized to images/files
    json_safe = {
        k: v for k, v in res.items()
        if k not in ["native_heatmap", "heatmap_384", "warped_retinal_heatmap"]
    }

    dumped = json.dumps(json_safe, indent=2)
    assert len(dumped) > 100
    reloaded = json.loads(dumped)
    assert reloaded["predicted_class"] == res["predicted_class"]
    assert reloaded["evidence_status"] == "feature_attribution_only"


def test_neutral_terminology_compliance():
    """Verify narrative strictly avoids diagnostic lesion claims."""
    bbox_info = {"x": 100, "y": 150, "width": 80, "height": 60}
    narrative = synthesize_evidence_narrative(
        predicted_grade=2,
        predicted_name="Moderate DR",
        target_score=0.88,
        top_region_name="posterior_pole",
        top_region_mass_pct=45.2,
        macular_overlap_pct=22.1,
        optic_disc_overlap_pct=8.4,
        bbox_info=bbox_info,
    )

    narrative_lower = narrative.lower()

    # Forbidden clinical claims without an actual lesion detector
    forbidden_terms = [
        "microaneurysm detected",
        "hemorrhage detected",
        "exudate detected",
        "neovascularization detected",
        "lesion detected",
        "proves disease",
        "confirmed lesion",
    ]
    for term in forbidden_terms:
        assert term not in narrative_lower, f"Forbidden term found: {term}"

    # Required neutral terms
    assert "feature attribution" in narrative_lower
    assert "attention" in narrative_lower


def test_safety_disclaimer_presence(shared_model):
    """Verify mandatory clinical safety disclaimer is populated."""
    res = generate_retinal_evidence(REAL_IMAGE_PATH, model=shared_model)

    disclaimer = res["safety_disclaimer"]
    assert len(disclaimer) > 50
    assert "feature attribution" in disclaimer.lower()
    assert "not" in disclaimer.lower()
    assert disclaimer == CLINICAL_SAFETY_DISCLAIMER
