"""Automated tests for Grad-CAM heatmap computation and retinal warping."""

from pathlib import Path
import numpy as np
import pytest

from classifier.model import load_classifier_model
from classifier.preprocessing import prepare_input_tensor
from explainability.gradcam import (
    compute_gradcam,
    resize_gradcam_to_input,
    warp_gradcam_to_retinal_coordinates,
    compute_full_retinal_gradcam,
)

REAL_IMAGE_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "real_retinal_images"
    / "confirmed_grade4_proliferative.jpg"
)


def test_model_compatibility():
    """Verify loaded model is compatible with Grad-CAM computation."""
    model = load_classifier_model()
    assert "APTOS_DR_EfficientNetB3" in model.name
    assert model.input_shape == (None, 384, 384, 3)
    assert model.output_shape == (None, 5)


def test_predicted_class_gradcam():
    """Verify Grad-CAM on predicted class produces valid 12x12 heatmap."""
    assert REAL_IMAGE_PATH.exists()
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)

    res = compute_gradcam(model=model, input_tensor=inp, target_class=None)

    assert res["target_class"] == res["predicted_class"]
    assert 0 <= res["target_class"] <= 4
    assert 0.0 <= res["target_score"] <= 1.0

    cam = res["native_heatmap"]
    assert isinstance(cam, np.ndarray)
    assert cam.shape == (12, 12)
    assert res["native_heatmap_shape"] == [12, 12]
    assert res["is_finite"] is True
    assert np.min(cam) >= 0.0
    assert np.max(cam) <= 1.0
    assert res["nonzero_fraction"] > 0.0


def test_explicit_target_class_gradcam():
    """Verify explicit target class is preserved and not replaced by argmax."""
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)

    # Supply class 0 explicitly
    res_0 = compute_gradcam(model=model, input_tensor=inp, target_class=0)
    assert res_0["target_class"] == 0

    # Supply class 3 explicitly
    res_3 = compute_gradcam(model=model, input_tensor=inp, target_class=3)
    assert res_3["target_class"] == 3


def test_target_class_validation():
    """Verify invalid target class indices raise appropriate errors."""
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)

    with pytest.raises(ValueError, match="target_class must be in"):
        compute_gradcam(model=model, input_tensor=inp, target_class=-1)

    with pytest.raises(ValueError, match="target_class must be in"):
        compute_gradcam(model=model, input_tensor=inp, target_class=5)

    with pytest.raises(TypeError, match="target_class must be int"):
        compute_gradcam(
            model=model,
            input_tensor=inp,
            target_class="grade2",  # type: ignore
        )


def test_heatmap_dimensions_and_normalization():
    """Verify native 12x12 heatmap resizes properly to 384x384 in [0, 1]."""
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)
    res = compute_gradcam(model=model, input_tensor=inp)

    native_cam = res["native_heatmap"]
    assert native_cam.shape == (12, 12)

    resized_cam = resize_gradcam_to_input(native_cam, target_size=(384, 384))
    assert resized_cam.shape == (384, 384)
    assert resized_cam.dtype == np.float32
    assert np.all(np.isfinite(resized_cam))
    assert np.min(resized_cam) >= 0.0
    assert np.max(resized_cam) <= 1.0


def test_deterministic_gradcam_output():
    """Verify Grad-CAM is strictly deterministic across dual forward passes."""
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)

    res1 = compute_gradcam(model=model, input_tensor=inp, target_class=4)
    res2 = compute_gradcam(model=model, input_tensor=inp, target_class=4)

    cam1 = res1["native_heatmap"]
    cam2 = res2["native_heatmap"]

    max_diff = float(np.max(np.abs(cam1 - cam2)))
    tolerance = 1e-5
    assert max_diff < tolerance, f"Non-deterministic delta: {max_diff}"


def test_predicted_vs_explicit_numerical_consistency():
    """Verify predicted-mode and explicit-mode with same index match."""
    model = load_classifier_model()
    inp = prepare_input_tensor(REAL_IMAGE_PATH)

    res_auto = compute_gradcam(
        model=model, input_tensor=inp, target_class=None
    )
    pred_cls = res_auto["predicted_class"]

    res_explicit = compute_gradcam(
        model=model, input_tensor=inp, target_class=pred_cls
    )

    cam_auto = res_auto["native_heatmap"]
    cam_explicit = res_explicit["native_heatmap"]

    max_diff = float(np.max(np.abs(cam_auto - cam_explicit)))
    assert max_diff < 1e-6, f"Mismatch between auto and explicit: {max_diff}"
    assert abs(res_auto["target_score"] - res_explicit["target_score"]) < 1e-6


def test_retinal_coordinate_warping():
    """Verify coordinate warping embeds cropped heatmap into full canvas."""
    # Synthetic 384x384 heatmap
    cam_384 = np.ones((384, 384), dtype=np.float32)

    # Full canvas (500, 600) with crop at y=50, x=40, h=300, w=400
    orig_shape = (500, 600)
    crop_box = (40, 50, 400, 300)  # x, y, w, h

    warped, meta = warp_gradcam_to_retinal_coordinates(
        heatmap=cam_384,
        original_shape=orig_shape,
        crop_box=crop_box,
    )

    assert warped.shape == (500, 600)
    assert warped.dtype == np.float32

    # Background outside crop box must be strictly 0.0
    assert np.all(warped[:50, :] == 0.0)  # Top background
    assert np.all(warped[350:, :] == 0.0)  # Bottom background
    assert np.all(warped[:, :40] == 0.0)  # Left background
    assert np.all(warped[:, 440:] == 0.0)  # Right background

    # Content inside crop box must have positive activations
    assert float(warped[50:350, 40:440].mean()) > 0.0
    assert meta["crop_dimensions"] == [300, 400]
    assert meta["original_dimensions"] == [500, 600]


def test_compute_full_retinal_gradcam_end_to_end():
    """Verify complete retinal Grad-CAM pipeline on real fundus image."""
    assert REAL_IMAGE_PATH.exists()
    model = load_classifier_model()

    res = compute_full_retinal_gradcam(REAL_IMAGE_PATH, model=model)

    required_keys = [
        "target_class",
        "target_score",
        "predicted_class",
        "predicted_probabilities",
        "native_heatmap",
        "heatmap_384",
        "warped_retinal_heatmap",
        "coordinate_mapping",
        "original_image_shape",
        "crop_box",
        "is_finite",
    ]
    for key in required_keys:
        assert key in res, f"Missing key in full Grad-CAM result: {key}"

    orig_shape = res["original_image_shape"][:2]
    warped_shape = list(res["warped_retinal_heatmap"].shape)
    assert warped_shape == orig_shape, "Warped heatmap shape must match image"
    assert res["is_finite"] is True


def test_malformed_inputs_handling():
    """Verify malformed inputs raise clear ValueErrors."""
    model = load_classifier_model()

    with pytest.raises(ValueError, match="input_tensor cannot be None"):
        compute_gradcam(model=model, input_tensor=None)

    # 2D array to compute_gradcam (needs 3D or 4D)
    with pytest.raises(ValueError, match="input_tensor must have shape"):
        compute_gradcam(model=model, input_tensor=np.zeros((100, 100)))

    # Batch size > 1
    with pytest.raises(ValueError, match="input_tensor must have shape"):
        compute_gradcam(
            model=model, input_tensor=np.zeros((2, 384, 384, 3))
        )

    # 1D array to resize_gradcam_to_input
    with pytest.raises(ValueError, match="native_heatmap must be a 2D"):
        resize_gradcam_to_input(np.zeros((100,)))

    # 1D array to warp_gradcam_to_retinal_coordinates
    with pytest.raises(ValueError, match="heatmap must be a 2D"):
        warp_gradcam_to_retinal_coordinates(
            heatmap=np.zeros((100,)), original_shape=(200, 200)
        )
