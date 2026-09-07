"""Automated tests for model loading and metadata extraction."""

import pytest
import keras

from classifier.model import (
    load_classifier_model,
    get_model_metadata,
    clear_model_cache,
    resolve_model_path,
)


def test_model_file_exists():
    """Verify that the trained model checkpoint exists on disk."""
    path = resolve_model_path()
    assert path.exists(), f"Model file missing at {path}"
    assert path.stat().st_size > 50 * 1024 * 1024, (
        "Model file is smaller than expected 50MB"
    )


def test_model_loading_and_architecture():
    """Verify that model loads successfully with expected architecture."""
    clear_model_cache()
    model = load_classifier_model()
    assert isinstance(model, keras.Model)
    assert "APTOS_DR_EfficientNetB3" in model.name

    # Input shape: (None, 384, 384, 3)
    assert model.input_shape == (None, 384, 384, 3)

    # Output shape: (None, 5)
    assert model.output_shape == (None, 5)


def test_model_parameter_count():
    """Verify parameter count matches EfficientNetB3 (~11.18M)."""
    model = load_classifier_model()
    param_count = model.count_params()
    assert param_count == 11184436, (
        f"Expected 11184436 params, got {param_count}"
    )


def test_model_output_classes():
    """Verify output layer produces 5 classes with softmax activation."""
    model = load_classifier_model()
    out_layer = model.layers[-1]
    assert out_layer.units == 5
    assert hasattr(out_layer, "activation")
    assert out_layer.activation.__name__ == "softmax"


def test_model_caching():
    """Verify in-memory model caching prevents redundant disk loads."""
    clear_model_cache()
    m1 = load_classifier_model()
    m2 = load_classifier_model()
    assert m1 is m2, "Model loader should return cached instance"

    clear_model_cache()
    m3 = load_classifier_model()
    assert m3 is not None


def test_model_metadata_structure():
    """Verify metadata dictionary contains all expected structural fields."""
    meta = get_model_metadata()
    required_keys = [
        "model_name",
        "input_shape",
        "output_shape",
        "num_classes",
        "total_parameters",
        "num_layers",
        "output_layer_name",
        "output_activation",
        "model_file_size_bytes",
    ]
    for key in required_keys:
        assert key in meta, f"Missing key in metadata: {key}"

    assert meta["num_classes"] == 5
    assert meta["input_shape"] == [None, 384, 384, 3]
    assert meta["output_shape"] == [None, 5]
    assert meta["output_activation"] == "softmax"


def test_invalid_model_path_raises():
    """Verify FileNotFoundError on non-existent path."""
    with pytest.raises(FileNotFoundError):
        load_classifier_model(
            "/path/to/nonexistent/model.keras", force_reload=True
        )
