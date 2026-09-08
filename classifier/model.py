"""Classifier model loader and metadata extractor for trained EfficientNetB3.

Loads the existing trained Keras model checkpoint:
model/MODEL_V2_80pct_backup.keras

Guarantees:
- Loads model with compile=False to bypass custom loss functions.
- In-memory singleton caching to avoid repetitive disk I/O.
- Model architecture validation (input shape (384, 384, 3), output shape 5 classes).
- Does NOT alter model weights or retrain.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional
import os

try:
    import keras  # type: ignore
except ImportError:
    try:
        from tensorflow import keras  # type: ignore
    except ImportError:
        keras = None

DEFAULT_MODEL_PATH: Path = (
    Path(__file__).resolve().parent.parent / "model" / "MODEL_V2_80pct_backup.keras"
)

_CACHED_MODEL: Optional[Any] = None


def resolve_model_path(model_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve and validate the path to the trained model checkpoint."""
    if model_path is None:
        p = DEFAULT_MODEL_PATH
    else:
        p = Path(model_path)

    if not p.exists():
        raise FileNotFoundError(
            f"Trained model checkpoint not found at: {p.resolve()}"
        )
    return p


def load_classifier_model(
    model_path: Optional[Union[str, Path]] = None,
    compile: bool = False,
    force_reload: bool = False,
) -> Any:
    """Load the trained EfficientNetB3 DR classifier model.

    Args:
        model_path: Path to .keras model file. Defaults to model/MODEL_V2_80pct_backup.keras.
        compile: Whether to compile model on load. Defaults to False (inference only).
        force_reload: If True, reloads model even if cached.

    Returns:
        keras.Model: Loaded Keras model instance.
    """
    global _CACHED_MODEL

    if keras is None:
        raise ImportError(
            "Keras or TensorFlow is required to load the classifier. "
            "Please run with the Anaconda Python environment (/opt/anaconda3/bin/python) "
            "where Keras is installed, or install via: pip install keras tensorflow"
        )

    if _CACHED_MODEL is not None and not force_reload and model_path is None:
        return _CACHED_MODEL

    resolved_path = resolve_model_path(model_path)
    try:
        model = keras.models.load_model(str(resolved_path), compile=compile, safe_mode=False)
    except TypeError:
        model = keras.models.load_model(str(resolved_path), compile=compile)

    # Validate model architecture
    expected_input_shape = (None, 384, 384, 3)
    expected_output_shape = (None, 5)

    if model.input_shape != expected_input_shape:
        raise ValueError(
            f"Unexpected model input shape: {model.input_shape}, expected {expected_input_shape}"
        )

    if model.output_shape != expected_output_shape:
        raise ValueError(
            f"Unexpected model output shape: {model.output_shape}, expected {expected_output_shape}"
        )

    if model_path is None:
        _CACHED_MODEL = model

    return model


def clear_model_cache() -> None:
    """Clear cached in-memory model."""
    global _CACHED_MODEL
    _CACHED_MODEL = None


def get_model_metadata(model: Optional[Any] = None) -> Dict[str, Any]:
    """Extract structural metadata from loaded model.

    Args:
        model: Optional model instance. If None, loads from default path.

    Returns:
        dict: Model metadata including shapes, parameter count, and layers.
    """
    if model is None:
        model = load_classifier_model()

    out_layer = model.layers[-1]
    activation = getattr(out_layer, "activation", None)
    activation_name = activation.__name__ if activation is not None else "unknown"

    return {
        "model_name": model.name,
        "input_shape": list(model.input_shape),
        "output_shape": list(model.output_shape),
        "num_classes": int(model.output_shape[-1]),
        "total_parameters": int(model.count_params()),
        "num_layers": len(model.layers),
        "output_layer_name": out_layer.name,
        "output_activation": activation_name,
        "model_file_size_bytes": os.path.getsize(resolve_model_path()),
    }
