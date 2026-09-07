"""Automated tests for Grad-CAM layer discovery and verification."""

from pathlib import Path
import numpy as np
from classifier.model import load_classifier_model
from classifier.preprocessing import prepare_input_tensor
from explainability.gradcam import (
    list_all_candidate_layers,
    discover_gradcam_layer,
    extract_feature_tensor,
)

REAL_IMAGE_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "real_retinal_images"
    / "confirmed_grade4_proliferative.jpg"
)


def test_model_loading_and_architecture_integrity():
    """Verify model loads unchanged with 5 classes and valid parameters."""
    model = load_classifier_model()
    assert "APTOS_DR_EfficientNetB3" in model.name
    assert model.input_shape == (None, 384, 384, 3)
    assert model.output_shape == (None, 5)
    assert model.count_params() == 11184436


def test_candidate_layers_discovery():
    """Verify candidate layer traversal discovers all structural stages."""
    model = load_classifier_model()
    candidates = list_all_candidate_layers(model)

    assert len(candidates) > 50, (
        f"Expected >50 layers in EfficientNet, got {len(candidates)}"
    )

    for c in candidates:
        assert "name" in c
        assert "layer_type" in c
        assert "output_shape" in c
        assert "is_spatial" in c
        assert "channels" in c

    spatial_layers = [c for c in candidates if c["is_spatial"]]
    assert len(spatial_layers) > 0, "No spatial feature map layers identified"


def test_discover_gradcam_layer_selection():
    """Verify programmatic discovery selects deepest compatible Conv2D."""
    model = load_classifier_model()
    layer_info = discover_gradcam_layer(model)

    # Must be top_conv
    assert layer_info["selected_layer_name"] == "top_conv"
    assert layer_info["layer_type"] == "Conv2D"
    assert layer_info["is_conv"] is True
    assert layer_info["is_spatial"] is True

    # Spatial shape: (None, 12, 12, 1536)
    assert layer_info["spatial_dimensions"] == [12, 12]
    assert layer_info["num_channels"] == 1536
    assert layer_info["output_shape"] == [None, 12, 12, 1536]
    assert layer_info["parent_submodel"] == "efficientnetb3"


def test_gradcam_layer_connectivity():
    """Verify selected layer has validated gradient flow to predictions."""
    model = load_classifier_model()
    layer_info = discover_gradcam_layer(model)

    assert layer_info["connected_to_output"] is True
    assert "Connected" in layer_info["connection_verification_message"]


def test_gradcam_discovery_determinism():
    """Verify programmatic discovery produces deterministic metadata."""
    model = load_classifier_model()
    info1 = discover_gradcam_layer(model)
    info2 = discover_gradcam_layer(model)

    assert info1["selected_layer_name"] == info2["selected_layer_name"]
    assert info1["output_shape"] == info2["output_shape"]
    assert info1["num_channels"] == info2["num_channels"]
    assert info1["spatial_dimensions"] == info2["spatial_dimensions"]


def test_extract_feature_tensor_real_image():
    """Verify feature tensor extraction on actual real retinal image."""
    assert REAL_IMAGE_PATH.exists(), (
        f"Real retinal image not found at {REAL_IMAGE_PATH}"
    )

    model = load_classifier_model()
    input_tensor = prepare_input_tensor(REAL_IMAGE_PATH)

    features = extract_feature_tensor(
        model=model,
        input_tensor=input_tensor,
        selected_layer_name="top_conv",
        parent_submodel_name="efficientnetb3",
    )

    # 4D tensor verification
    assert isinstance(features, np.ndarray)
    assert features.ndim == 4
    assert features.shape == (1, 12, 12, 1536)

    # Value validity (no NaN or Inf)
    assert np.all(np.isfinite(features)), "Feature map has non-finite values"
    assert np.std(features.astype(np.float32)) > 0.0, "Zero variance map"
