"""Integration tests for the DR screening REST API."""


from pathlib import Path
import cv2
from fastapi.testclient import TestClient
import numpy as np
import pytest

from api.main import app

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = WORKSPACE_ROOT / "data" / "real_retinal_images"


@pytest.fixture(scope="module")
def client():
    """Create reusable FastAPI TestClient."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    """Verify health endpoint returns live model information."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "EfficientNetB3" in data["model_name"]
    assert data["model_output_shape"] == [None, 5]


def test_screen_invalid_format(client):
    """Verify rejection of unsupported file extensions."""
    files = {"image": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    response = client.post("/api/screen", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_screen_empty_file(client):
    """Verify rejection of empty file upload."""
    files = {"image": ("empty.png", b"", "image/png")}
    response = client.post("/api/screen", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_screen_corrupted_image(client):
    """Verify rejection of unreadable image bytes."""
    files = {"image": ("corrupted.png", b"not-a-valid-png", "image/png")}
    response = client.post("/api/screen", files=files)
    assert response.status_code == 400
    assert "unable to decode" in response.json()["detail"].lower()


def test_screen_real_retinal_image(client):
    """Verify screening pipeline with real retinal image."""
    image_path = DATA_DIR / "aptos_eval_6959267_grade3.png"

    assert image_path.exists(), f"Image not found: {image_path}"

    with open(image_path, "rb") as f:
        file_bytes = f.read()

    files = {"image": (image_path.name, file_bytes, "image/png")}
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200
    data = response.json()

    # Schema integrity
    assert data["screening_status"] in {"COMPLETED", "BORDERLINE_PROCEEDED"}
    assert "result_id" in data
    result_id = data["result_id"]

    # Image Quality
    iq = data["image_quality"]
    assert iq["decision"] in {"GOOD", "BORDERLINE"}
    assert 0.0 <= iq["overall_score"] <= 100.0
    assert 0.0 <= iq["focus"] <= 100.0

    # Classifier
    cls = data["classification"]
    assert cls is not None
    assert cls["predicted_class"] in range(5)
    assert cls["predicted_label"] in {
        "No DR",
        "Mild DR",
        "Moderate DR",
        "Severe DR",
        "Proliferative DR",
    }
    prob_sum = sum(cls["probabilities"].values())
    assert abs(prob_sum - 1.0) < 1e-3
    assert 0.0 <= cls["top_probability"] <= 1.0

    # Referable DR
    ref = data["referable"]
    assert ref is not None
    assert isinstance(ref["is_referable"], bool)
    assert ref["threshold"] == 0.33

    # Explainability & Visual Artifacts
    exp = data["explainability"]
    assert exp is not None
    assert exp["gradcam_available"] is True
    assert exp["overlay_url"] == f"/api/result/{result_id}/overlay"
    assert exp["gradcam_url"] == f"/api/result/{result_id}/gradcam"

    # Evidence
    ev = data["evidence"]
    assert ev is not None
    assert len(ev["narrative"]) > 0

    # Processing time
    proc = data["processing"]
    assert proc["total_time_ms"] > 0.0

    # Verify visual asset downloads
    res_overlay = client.get(exp["overlay_url"])
    assert res_overlay.status_code == 200
    assert res_overlay.headers["content-type"] == "image/png"

    res_cam = client.get(exp["gradcam_url"])
    assert res_cam.status_code == 200
    assert res_cam.headers["content-type"] == "image/png"


def test_screen_ungradeable_safety_bypass(client):
    """Verify UNGRADEABLE image strictly bypasses classifier and Grad-CAM."""
    # Construct an all-black ungradeable image fixture encoded as PNG
    black_img = np.zeros((384, 384, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".png", black_img)
    file_bytes = buf.tobytes()

    files = {"image": ("black_test.png", file_bytes, "image/png")}
    response = client.post("/api/screen", files=files)
    assert response.status_code == 200
    data = response.json()

    # Verify safety routing
    assert data["screening_status"] == "REJECTED_UNGRADEABLE"
    assert data["image_quality"]["decision"] == "UNGRADEABLE"
    assert data["image_quality"]["recapture_guidance"] is not None

    # Classifier and explainability MUST be None
    assert data["classification"] is None
    assert data["referable"] is None
    assert data["explainability"] is None
    assert data["evidence"] is None


def test_asset_not_found(client):
    """Verify 404 response for nonexistent result assets."""
    response = client.get("/api/result/nonexistent-session-id/overlay")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_all_9_real_retinal_images(client):
    """Verify all 9 real local retinal images through the API pipeline."""
    image_paths = sorted(list(DATA_DIR.glob("*.png")) + list(DATA_DIR.glob("*.jpg")))
    assert len(image_paths) == 9, f"Expected 9 real images, found {len(image_paths)}"

    timing_records = []

    for img_p in image_paths:
        with open(img_p, "rb") as f:
            file_bytes = f.read()

        mime = "image/png" if img_p.suffix == ".png" else "image/jpeg"
        files = {"image": (img_p.name, file_bytes, mime)}
        resp = client.post("/api/screen", files=files)
        assert resp.status_code == 200, f"Failed on {img_p.name}: {resp.text}"
        data = resp.json()

        result_id = data["result_id"]
        status = data["screening_status"]
        iq = data["image_quality"]
        proc = data["processing"]

        timing_records.append({
            "image": img_p.name,
            "status": status,
            "total_ms": proc["total_time_ms"],
            "breakdown": proc["breakdown_ms"],
        })

        if status in {"COMPLETED", "BORDERLINE_PROCEEDED"}:
            cls = data["classification"]
            assert cls is not None
            assert cls["predicted_class"] in range(5)
            prob_sum = sum(cls["probabilities"].values())
            assert abs(prob_sum - 1.0) < 1e-3
            assert data["referable"] is not None
            assert data["explainability"] is not None
            assert data["evidence"] is not None
            assert len(data["evidence"]["narrative"]) > 0

            # Verify asset retrieval
            overlay_resp = client.get(f"/api/result/{result_id}/overlay")
            assert overlay_resp.status_code == 200
            assert overlay_resp.headers["content-type"] == "image/png"
            assert len(overlay_resp.content) > 100

            if iq.get("enhancement_applied"):
                assert iq.get("enhanced_url") is not None
                enh_resp = client.get(iq["enhanced_url"])
                assert enh_resp.status_code == 200
                assert enh_resp.headers["content-type"] == "image/png"
                assert len(enh_resp.content) > 100
        else:
            assert status == "REJECTED_UNGRADEABLE"
            assert data["classification"] is None

    # Verify all 9 processed
    assert len(timing_records) == 9

