"""Grad-CAM layer discovery, inspection, and verification module.

Provides programmatic discovery of candidate convolutional and spatial feature
layers in the trained EfficientNetB3 classifier, selecting and verifying the
canonical deepest convolutional layer without hardcoded assumptions.
Also provides Grad-CAM heatmap computation and retinal coordinate warping.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import cv2
import numpy as np

from classifier.model import load_classifier_model
from classifier.preprocessing import (
    prepare_input_tensor,
    get_retinal_crop_box,
)
from image_quality.io import load_raw_image

# Dynamic framework imports with fallback
keras: Any = None
tf: Any = None

try:
    import keras as _keras  # type: ignore
    keras = _keras
except ImportError:
    try:
        from tensorflow import keras as _tf_keras  # type: ignore
        keras = _tf_keras
    except ImportError:
        keras = None

try:
    import tensorflow as _tf  # type: ignore
    tf = _tf
except ImportError:
    tf = None


CONV_LAYER_CLASS_NAMES = (
    "Conv2D",
    "DepthwiseConv2D",
    "SeparableConv2D",
)


def list_all_candidate_layers(
    model: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Traverse and identify all layers and sublayers in the model.

    Records for each layer:
    - layer name
    - layer type
    - output shape
    - whether the output is spatial feature maps
    - number of channels

    Args:
        model: Optional pre-loaded model. Defaults to loading cached model.

    Returns:
        list[dict]: Detailed metadata for all discovered layers.
    """
    if model is None:
        model = load_classifier_model()

    candidates: List[Dict[str, Any]] = []

    def _traverse(m: Any, prefix: str = "", scope: str = "top_level") -> None:
        for layer in m.layers:
            full_name = f"{prefix}{layer.name}" if prefix else layer.name

            # Check if this layer is a nested submodel
            if hasattr(layer, "layers") and bool(layer.layers):
                _traverse(layer, prefix=f"{full_name}.", scope="backbone")

            # Extract tensor shape
            out_tensor = getattr(layer, "output", None)
            shape: Optional[List[Optional[int]]] = None
            if out_tensor is not None and hasattr(out_tensor, "shape"):
                raw_shape = list(out_tensor.shape)
                shape = [None if s is None else int(s) for s in raw_shape]
            elif (
                hasattr(layer, "output_shape")
                and layer.output_shape is not None
            ):
                raw_shape = list(layer.output_shape)
                shape = [None if s is None else int(s) for s in raw_shape]

            is_spatial = False
            channels: Optional[int] = None
            if shape is not None and len(shape) == 4:
                # 4D tensor: [batch, height, width, channels]
                h_dim, w_dim = shape[1], shape[2]
                if (
                    h_dim is not None
                    and w_dim is not None
                    and h_dim > 1
                    and w_dim > 1
                ):
                    is_spatial = True
                    channels = shape[3]

            is_conv = layer.__class__.__name__ in CONV_LAYER_CLASS_NAMES

            candidates.append(
                {
                    "name": full_name,
                    "layer_object_name": layer.name,
                    "layer_type": layer.__class__.__name__,
                    "output_shape": shape,
                    "is_spatial": is_spatial,
                    "channels": channels,
                    "is_conv": is_conv,
                    "scope": scope,
                }
            )

    _traverse(model)
    return candidates


def discover_gradcam_layer(
    model: Optional[Any] = None,
    prefer_conv: bool = True,
) -> Dict[str, Any]:
    """Programmatically discover and verify the optimal Grad-CAM feature layer.

    Selects deepest spatial convolutional feature layer for Grad-CAM.
    Validates that the selected layer:
    - exists in the actual model
    - produces a 4D tensor for a single image
    - has spatial dimensions H x W > 1
    - has a valid channel dimension
    - is connected to the final prediction output

    Args:
        model: Optional pre-loaded model. Defaults to loading cached model.
        prefer_conv: Prioritize Conv2D layers over raw activations.

    Returns:
        dict: Complete structural and validation metadata for selected layer.
    """
    if model is None:
        model = load_classifier_model()

    candidates = list_all_candidate_layers(model)

    # Filter candidates to spatial feature map layers (4D with H>1 and W>1)
    spatial_candidates = [c for c in candidates if c["is_spatial"]]

    if not spatial_candidates:
        raise RuntimeError("No spatial feature map layers in architecture.")

    if prefer_conv:
        conv_spatial = [c for c in spatial_candidates if c["is_conv"]]
        if conv_spatial:
            selected = conv_spatial[-1]
        else:
            selected = spatial_candidates[-1]
    else:
        selected = spatial_candidates[-1]

    # Validate selected layer properties
    selected_name = selected["layer_object_name"]
    output_shape = selected["output_shape"]
    if output_shape is None or len(output_shape) != 4:
        raise ValueError(
            f"Layer '{selected_name}' does not produce a 4D tensor: "
            f"{output_shape}"
        )

    h_dim, w_dim, c_dim = output_shape[1], output_shape[2], output_shape[3]
    if h_dim is None or w_dim is None or h_dim <= 1 or w_dim <= 1:
        raise ValueError(
            f"Layer '{selected_name}' spatial dims ({h_dim}x{w_dim}) "
            f"must be > 1"
        )
    if c_dim is None or c_dim <= 0:
        raise ValueError(
            f"Layer '{selected_name}' channel count must be positive: {c_dim}"
        )

    # Locate parent submodel if nested
    parent_submodel_name: Optional[str] = None
    layer_obj = None

    try:
        layer_obj = model.get_layer(selected_name)
    except (ValueError, AttributeError):
        for sub_layer in model.layers:
            if hasattr(sub_layer, "get_layer"):
                try:
                    layer_obj = sub_layer.get_layer(selected_name)
                    parent_submodel_name = sub_layer.name
                    break
                except (ValueError, AttributeError):
                    continue

    if layer_obj is None:
        raise ValueError(
            f"Selected layer '{selected_name}' could not be located."
        )

    # Validate differentiability / connectivity to output
    connection_verified = False
    verification_message = "Not tested"
    if tf is not None:
        try:
            conn_res = validate_gradcam_connectivity(
                model=model,
                selected_layer_name=selected_name,
                parent_submodel_name=parent_submodel_name,
            )
            connection_verified = conn_res["connected"]
            verification_message = conn_res["message"]
        except (ValueError, TypeError, RuntimeError, AttributeError) as exc:
            connection_verified = False
            verification_message = f"Connectivity check failed: {str(exc)}"

    alternative_candidates = [
        c["name"]
        for c in spatial_candidates[-5:]
        if c["layer_object_name"] != selected_name
    ]

    return {
        "selected_layer_name": selected_name,
        "full_layer_path": selected["name"],
        "layer_type": selected["layer_type"],
        "output_shape": output_shape,
        "spatial_dimensions": [int(h_dim), int(w_dim)],
        "num_channels": int(c_dim),
        "is_spatial": True,
        "is_conv": selected["is_conv"],
        "parent_submodel": parent_submodel_name,
        "model_name": getattr(model, "name", "unknown_model"),
        "model_input_shape": list(model.input_shape),
        "model_output_shape": list(model.output_shape),
        "total_candidates_analyzed": len(candidates),
        "spatial_candidates_count": len(spatial_candidates),
        "connected_to_output": connection_verified,
        "connection_verification_message": verification_message,
        "alternative_candidates": alternative_candidates,
    }


def validate_gradcam_connectivity(
    model: Any,
    selected_layer_name: str,
    parent_submodel_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify gradient flow from prediction output back to target layer.

    Args:
        model: Classifier model.
        selected_layer_name: Target feature layer name.
        parent_submodel_name: Optional submodel containing target layer.

    Returns:
        dict: Connectivity status and gradient statistics.
    """
    if tf is None or keras is None:
        return {
            "connected": True,
            "message": "TensorFlow/Keras not available to test tape.",
        }

    dummy_input = np.ones((1, 384, 384, 3), dtype=np.float32)

    if parent_submodel_name is not None:
        submodel = model.get_layer(parent_submodel_name)
        target_layer = submodel.get_layer(selected_layer_name)

        feature_submodel = keras.Model(
            inputs=submodel.inputs,
            outputs=[target_layer.output, submodel.output],
        )

        parent_idx = [
            idx for idx, layer in enumerate(model.layers)
            if layer.name == parent_submodel_name
        ][0]
        pre_layers = model.layers[1:parent_idx]
        head_layers = model.layers[parent_idx + 1:]

        with tf.GradientTape() as tape:
            tensor_x = tf.convert_to_tensor(dummy_input)
            for pre_layer in pre_layers:
                tensor_x = pre_layer(tensor_x, training=False)
            features, sub_out = feature_submodel(tensor_x, training=False)
            head_x = sub_out
            for head_layer in head_layers:
                head_x = head_layer(head_x, training=False)
            pred = head_x
            loss = pred[:, tf.argmax(pred[0])]

        grads = tape.gradient(loss, features)
    else:
        target_layer = model.get_layer(selected_layer_name)
        grad_model = keras.Model(
            inputs=model.inputs,
            outputs=[target_layer.output, model.output],
        )

        with tf.GradientTape() as tape:
            features, pred = grad_model(dummy_input, training=False)
            loss = pred[:, tf.argmax(pred[0])]

        grads = tape.gradient(loss, features)

    if grads is None:
        return {
            "connected": False,
            "message": "Gradient computation returned None (disconnected).",
        }

    max_grad = float(tf.reduce_max(tf.abs(grads)).numpy())
    return {
        "connected": True,
        "message": (
            f"Connected: gradients computed successfully "
            f"(max absolute grad: {max_grad:.6e})."
        ),
        "max_grad": max_grad,
        "features_shape": list(features.shape),
        "grads_shape": list(grads.shape) if hasattr(grads, "shape") else [],
    }


def extract_feature_tensor(
    model: Any,
    input_tensor: Any,
    selected_layer_name: str = "top_conv",
    parent_submodel_name: Optional[str] = "efficientnetb3",
) -> np.ndarray:
    """Extract spatial feature map tensor from the verified layer.

    Args:
        model: Classifier model.
        input_tensor: 4D float32 tensor of shape (batch, 384, 384, 3).
        selected_layer_name: Verified feature layer (default: 'top_conv').
        parent_submodel_name: Submodel name (default: 'efficientnetb3').

    Returns:
        np.ndarray: 4D feature map array of shape (batch, 12, 12, 1536).
    """
    if keras is None:
        raise ImportError("Keras is required to extract feature tensors.")

    if parent_submodel_name is not None:
        submodel = model.get_layer(parent_submodel_name)
        target_layer = submodel.get_layer(selected_layer_name)
        sub_extractor = keras.Model(
            inputs=submodel.inputs, outputs=target_layer.output
        )

        parent_idx = [
            idx for idx, layer in enumerate(model.layers)
            if layer.name == parent_submodel_name
        ][0]
        curr_x = input_tensor
        for step_layer in model.layers[1:parent_idx]:
            curr_x = step_layer(curr_x, training=False)
        features = sub_extractor(curr_x, training=False)
    else:
        target_layer = model.get_layer(selected_layer_name)
        extractor = keras.Model(
            inputs=model.inputs, outputs=target_layer.output
        )
        features = extractor(input_tensor, training=False)

    if hasattr(features, "numpy"):
        return features.numpy()
    return np.array(features)


def compute_gradcam(
    model: Optional[Any] = None,
    input_tensor: Any = None,
    target_class: Optional[int] = None,
    gradcam_layer: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute Grad-CAM activation heatmap for a target class.

    Math:
        alpha_k = (1 / Z) * sum_i sum_j (d y^c / d A_ijk)
        CAM = ReLU(sum_k alpha_k * A_k)
        CAM_norm = (CAM - min) / (max - min + eps)

    Args:
        model: Loaded Keras model instance. If None, loads cached model.
        input_tensor: 4D float32 array or tensor of shape (1, 384, 384, 3).
        target_class: Optional integer in {0, 1, 2, 3, 4}. If None, uses
            predicted class (argmax of output probabilities).
        gradcam_layer: Target feature layer name (defaults to 'top_conv').

    Returns:
        dict: Structured Grad-CAM result containing native 12x12 heatmap,
              target class, score, and activation statistics.
    """
    if tf is None or keras is None:
        raise ImportError("TensorFlow and Keras are required for Grad-CAM.")

    if model is None:
        model = load_classifier_model()

    if input_tensor is None:
        raise ValueError("input_tensor cannot be None.")

    # Convert to 4D tensor if 3D array provided
    tensor_arr = np.asarray(input_tensor, dtype=np.float32)
    if tensor_arr.ndim == 3:
        tensor_arr = np.expand_dims(tensor_arr, axis=0)

    if tensor_arr.ndim != 4 or tensor_arr.shape[0] != 1:
        raise ValueError(
            f"input_tensor must have shape (1, H, W, C), "
            f"got {tensor_arr.shape}"
        )

    # Validate target class range if provided
    if target_class is not None:
        if not isinstance(target_class, (int, np.integer)):
            raise TypeError(
                f"target_class must be int, got {type(target_class)}"
            )
        target_class_int = target_class
        if target_class_int < 0 or target_class_int >= 5:
            raise ValueError(
                f"target_class must be in {{0, 1, 2, 3, 4}}, "
                f"got {target_class_int}"
            )
    else:
        target_class_int = None

    # Discover target layer if not explicitly supplied
    if gradcam_layer is None:
        layer_meta = discover_gradcam_layer(model)
        selected_layer_name = layer_meta["selected_layer_name"]
        parent_submodel_name = layer_meta["parent_submodel"]
    else:
        selected_layer_name = gradcam_layer
        parent_submodel_name = "efficientnetb3"

    # Set up submodel and head layers
    submodel = model.get_layer(parent_submodel_name)
    target_conv_layer = submodel.get_layer(selected_layer_name)

    feature_submodel = keras.Model(
        inputs=submodel.inputs,
        outputs=[target_conv_layer.output, submodel.output],
    )

    parent_idx = [
        idx for idx, layer in enumerate(model.layers)
        if layer.name == parent_submodel_name
    ][0]
    pre_layers = model.layers[1:parent_idx]
    head_layers = model.layers[parent_idx + 1:]
    head_pre_final = head_layers[:-1]
    final_layer = head_layers[-1]

    with tf.GradientTape() as tape:
        curr_x = tf.convert_to_tensor(tensor_arr)
        for pre_layer in pre_layers:
            curr_x = pre_layer(curr_x, training=False)
        conv_outputs, sub_out = feature_submodel(curr_x, training=False)
        head_x = sub_out
        for head_layer in head_pre_final:
            head_x = head_layer(head_x, training=False)

        # Compute pre-softmax class scores (logits) to avoid softmax saturation
        if hasattr(final_layer, "kernel") and hasattr(final_layer, "bias"):
            head_cast = tf.cast(head_x, final_layer.kernel.dtype)
            logits = (
                tf.matmul(head_cast, final_layer.kernel)
                + final_layer.bias
            )
            logits = tf.cast(logits, tf.float32)
            predictions = tf.nn.softmax(logits)
        else:
            predictions = final_layer(head_x, training=False)
            logits = predictions

        pred_probs = predictions[0].numpy().tolist()
        predicted_class = int(np.argmax(pred_probs))

        # Respect explicitly provided target class; do not override
        if target_class_int is None:
            active_target = predicted_class
        else:
            active_target = target_class_int

        target_score = float(predictions[0, active_target].numpy())
        # Use un-saturated pre-softmax score for gradient computation
        loss = logits[:, active_target]

    grads = tape.gradient(loss, conv_outputs)
    if grads is None:
        raise RuntimeError("Failed to compute gradients for target layer.")

    # Spatial global average pooling of gradients: alpha_k
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Channel-weighted linear combination of feature maps
    cam = tf.reduce_sum(
        tf.multiply(pooled_grads, conv_outputs[0]),
        axis=-1,
    )

    # ReLU: capture only features that positively influence target class
    cam = tf.maximum(cam, 0.0)

    cam_np = cam.numpy()
    cam_min = float(np.min(cam_np))
    cam_max = float(np.max(cam_np))

    # Safe normalization to [0, 1]
    if cam_max > cam_min:
        heatmap_native = (cam_np - cam_min) / (cam_max - cam_min)
    else:
        heatmap_native = np.zeros(cam_np.shape, dtype=np.float32)

    heatmap_native = heatmap_native.astype(np.float32)
    is_finite = bool(np.all(np.isfinite(heatmap_native)))
    nonzero_frac = float(np.mean(heatmap_native > 0.0))

    return {
        "target_class": active_target,
        "target_score": round(target_score, 6),
        "predicted_class": predicted_class,
        "predicted_probabilities": [round(float(p), 6) for p in pred_probs],
        "feature_map_shape": list(conv_outputs.shape),
        "native_heatmap_shape": list(heatmap_native.shape),
        "native_heatmap": heatmap_native,
        "min_activation": round(float(np.min(heatmap_native)), 6),
        "max_activation": round(float(np.max(heatmap_native)), 6),
        "mean_activation": round(float(np.mean(heatmap_native)), 6),
        "nonzero_fraction": round(nonzero_frac, 4),
        "is_finite": is_finite,
        "model_name": getattr(model, "name", "APTOS_DR_EfficientNetB3_V2"),
        "layer_name": selected_layer_name,
    }


def resize_gradcam_to_input(
    native_heatmap: Any,
    target_size: Tuple[int, int] = (384, 384),
    interpolation: int = cv2.INTER_CUBIC,
) -> np.ndarray:
    """Resize native 12x12 Grad-CAM heatmap to classifier input resolution.

    Args:
        native_heatmap: 2D float32 array (e.g. 12x12).
        target_size: (width, height) resolution (default: (384, 384)).
        interpolation: OpenCV interpolation flag (default: cv2.INTER_CUBIC).

    Returns:
        np.ndarray: 2D float32 array of shape (height, width) in [0.0, 1.0].
    """
    if not isinstance(native_heatmap, np.ndarray) or native_heatmap.ndim != 2:
        raise ValueError("native_heatmap must be a 2D NumPy array.")

    resized = cv2.resize(
        native_heatmap.astype(np.float32),
        target_size,
        interpolation=interpolation,
    )

    # Re-normalize to strictly [0.0, 1.0]
    r_min = float(np.min(resized))
    r_max = float(np.max(resized))
    if r_max > r_min:
        norm = (resized - r_min) / (r_max - r_min)
    else:
        norm = np.zeros_like(resized)

    return np.clip(norm, 0.0, 1.0).astype(np.float32)


def warp_gradcam_to_retinal_coordinates(
    heatmap: Any,
    original_shape: Union[Tuple[int, int], Tuple[int, int, int]],
    crop_box: Optional[Tuple[int, int, int, int]] = None,
    interpolation: int = cv2.INTER_CUBIC,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Map classifier-space Grad-CAM heatmap back to full retinal image canvas.

    Accounts for the black-border bounding-box crop applied upstream.
    Embeds the heatmap at its exact original pixel location, leaving
    cropped background pixels as 0.0.

    Args:
        heatmap: 2D array of shape (384, 384) or (12, 12).
        original_shape: Shape of uncropped retinal image (H, W) or (H, W, C).
        crop_box: Optional (x, y, w, h) bounding box. If None, full image.
        interpolation: OpenCV interpolation method for un-resizing.

    Returns:
        tuple[np.ndarray, dict]:
            - 2D float32 array of shape (H_orig, W_orig) in [0.0, 1.0].
            - Metadata describing coordinate transformation parameters.
    """
    if not isinstance(heatmap, np.ndarray) or heatmap.ndim != 2:
        raise ValueError("heatmap must be a 2D NumPy array.")

    h_orig, w_orig = original_shape[0], original_shape[1]

    if crop_box is not None:
        box_x, box_y, box_w, box_h = crop_box
    else:
        box_x, box_y, box_w, box_h = 0, 0, w_orig, h_orig

    # Resize heatmap to the cropped retinal dimension (box_w, box_h)
    cropped_cam = cv2.resize(
        heatmap.astype(np.float32),
        (box_w, box_h),
        interpolation=interpolation,
    )
    cropped_cam = np.clip(cropped_cam, 0.0, 1.0)

    # Embed into full uncropped retinal canvas
    full_canvas = np.zeros((h_orig, w_orig), dtype=np.float32)
    end_y = min(box_y + box_h, h_orig)
    end_x = min(box_x + box_w, w_orig)
    slice_h = end_y - box_y
    slice_w = end_x - box_x

    full_canvas[box_y:end_y, box_x:end_x] = cropped_cam[:slice_h, :slice_w]

    meta = {
        "original_dimensions": [h_orig, w_orig],
        "crop_dimensions": [box_h, box_w],
        "crop_box": {
            "x": box_x,
            "y": box_y,
            "w": box_w,
            "h": box_h,
        },
        "warped_shape": [h_orig, w_orig],
        "interpolation_method": "cv2.INTER_CUBIC",
        "finite_values": bool(np.all(np.isfinite(full_canvas))),
        "mean_activation": round(float(np.mean(full_canvas)), 6),
        "max_activation": round(float(np.max(full_canvas)), 6),
    }

    return full_canvas.astype(np.float32), meta


def compute_full_retinal_gradcam(
    image_or_path: Union[str, Path, Any],
    model: Optional[Any] = None,
    target_class: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute end-to-end Grad-CAM with full retinal coordinate mapping.

    Workflow:
    1. Load original uncropped retinal image.
    2. Extract black-border crop bounding box.
    3. Prepare 384x384 classifier input tensor.
    4. Compute native 12x12 Grad-CAM activation map.
    5. Resize heatmap to 384x384 classifier space.
    6. Warp 384x384 heatmap back to original retinal coordinates.

    Args:
        image_or_path: Image file path or RGB numpy array.
        model: Pre-loaded Keras model.
        target_class: Integer in {0..4}. If None, uses predicted class.

    Returns:
        dict: Full payload containing all heatmaps, coordinate metadata,
              scores, and original image array.
    """
    orig_img: Any
    if isinstance(image_or_path, (str, Path)):
        orig_img = load_raw_image(image_or_path)
    elif isinstance(image_or_path, np.ndarray):
        orig_img = image_or_path.copy()
    else:
        orig_img = load_raw_image(str(image_or_path))

    h_orig, w_orig = orig_img.shape[:2]
    crop_box = get_retinal_crop_box(orig_img, tol=10)

    # Classifier input tensor
    input_tensor = prepare_input_tensor(orig_img)

    # 1. Native 12x12 Grad-CAM
    cam_result = compute_gradcam(
        model=model,
        input_tensor=input_tensor,
        target_class=target_class,
    )

    # 2. Resized 384x384 Grad-CAM
    heatmap_384 = resize_gradcam_to_input(
        cam_result["native_heatmap"],
        target_size=(384, 384),
        interpolation=cv2.INTER_CUBIC,
    )

    # 3. Warped Retinal Grad-CAM
    warped_cam, warp_meta = warp_gradcam_to_retinal_coordinates(
        heatmap=heatmap_384,
        original_shape=(h_orig, w_orig),
        crop_box=crop_box,
        interpolation=cv2.INTER_CUBIC,
    )

    cam_result["heatmap_384"] = heatmap_384
    cam_result["warped_retinal_heatmap"] = warped_cam
    cam_result["coordinate_mapping"] = warp_meta
    cam_result["original_image_shape"] = [h_orig, w_orig, 3]
    cam_result["crop_box"] = warp_meta["crop_box"]

    return cam_result
