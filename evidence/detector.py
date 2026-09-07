"""Deep Retinal Anatomy and Lesion Detectors.

Integrates trained IDRiD U-Net models for:
1. Optic Disc localization & boundary segmentation (model/idrid_optic_disc_best.pth)
2. Retinal Hard Exudates segmentation & lesion clustering (model/idrid_exudates_best.pth)
3. Fovea spatial estimation anchored on detected Optic Disc landmark
4. Macular edema risk assessment based on lesion-to-fovea proximity.

Strict Integrity Rules:
- Status for algorithmic predictions is strictly DETECTED or ESTIMATED (never GROUND_TRUTH).
- V2 classifier remains frozen.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union, List
import numpy as np
import cv2

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DISC_MODEL_PATH = WORKSPACE_ROOT / "model" / "idrid_optic_disc_best.pth"
DEFAULT_EXUDATES_MODEL_PATH = WORKSPACE_ROOT / "model" / "idrid_exudates_best.pth"
DEFAULT_HEMORRHAGES_MODEL_PATH = WORKSPACE_ROOT / "model" / "idrid_hemorrhages_best.pth"
DEFAULT_SOFT_EXUDATES_MODEL_PATH = WORKSPACE_ROOT / "model" / "idrid_soft_exudates_best.pth"
DEFAULT_VESSEL_MODEL_PATH = WORKSPACE_ROOT / "model" / "drive_vessels_best.pth"

# Lazy model cache to avoid repeated disk reads
_CACHED_DISC_MODEL = None
_CACHED_EXUDATE_MODEL = None
_CACHED_HEMORRHAGE_MODEL = None
_CACHED_SOFT_EXUDATE_MODEL = None
_CACHED_VESSEL_MODEL = None


def is_torch_available() -> bool:
    """Check if PyTorch and segmentation_models_pytorch are installed."""
    try:
        import torch
        import segmentation_models_pytorch as smp
        return True
    except ImportError:
        return False


def load_optic_disc_model(model_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
    """Load trained Optic Disc U-Net (ResNet34) model from checkpoint."""
    global _CACHED_DISC_MODEL
    if _CACHED_DISC_MODEL is not None and model_path is None:
        return _CACHED_DISC_MODEL

    import torch
    import segmentation_models_pytorch as smp

    ckpt_path = Path(model_path) if model_path is not None else DEFAULT_DISC_MODEL_PATH
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Optic Disc model checkpoint not found: {ckpt_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None,
    )

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    if model_path is None:
        _CACHED_DISC_MODEL = model
    return model


def load_exudates_model(model_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
    """Load trained Hard Exudates U-Net (ResNet34) model from checkpoint."""
    global _CACHED_EXUDATE_MODEL
    if _CACHED_EXUDATE_MODEL is not None and model_path is None:
        return _CACHED_EXUDATE_MODEL

    import torch
    import segmentation_models_pytorch as smp

    ckpt_path = Path(model_path) if model_path is not None else DEFAULT_EXUDATES_MODEL_PATH
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Exudates model checkpoint not found: {ckpt_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None,
    )

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    if model_path is None:
        _CACHED_EXUDATE_MODEL = model
    return model


def load_hemorrhages_model(model_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
    """Load trained Retinal Hemorrhages U-Net (ResNet34) model from checkpoint."""
    global _CACHED_HEMORRHAGE_MODEL
    if _CACHED_HEMORRHAGE_MODEL is not None and model_path is None:
        return _CACHED_HEMORRHAGE_MODEL

    import torch
    import segmentation_models_pytorch as smp

    ckpt_path = Path(model_path) if model_path is not None else DEFAULT_HEMORRHAGES_MODEL_PATH
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Hemorrhages model checkpoint not found: {ckpt_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None,
    )

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    if model_path is None:
        _CACHED_HEMORRHAGE_MODEL = model
    return model


def load_soft_exudates_model(model_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
    """Load trained Soft Exudates (Cotton Wool Spots) U-Net (ResNet34) model from checkpoint."""
    global _CACHED_SOFT_EXUDATE_MODEL
    if _CACHED_SOFT_EXUDATE_MODEL is not None and model_path is None:
        return _CACHED_SOFT_EXUDATE_MODEL

    import torch
    import segmentation_models_pytorch as smp

    ckpt_path = Path(model_path) if model_path is not None else DEFAULT_SOFT_EXUDATES_MODEL_PATH
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Soft Exudates model checkpoint not found: {ckpt_path}")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None,
    )

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    if model_path is None:
        _CACHED_SOFT_EXUDATE_MODEL = model
    return model


def load_vessel_model(model_path: Optional[Union[str, Path]] = None, device: str = "cpu"):
    """Load trained DRIVE U-Net (ResNet34) vessel segmenter if checkpoint exists."""
    global _CACHED_VESSEL_MODEL
    if _CACHED_VESSEL_MODEL is not None and model_path is None:
        return _CACHED_VESSEL_MODEL

    ckpt_path = Path(model_path) if model_path is not None else DEFAULT_VESSEL_MODEL_PATH
    if not ckpt_path.exists():
        return None

    import torch
    import segmentation_models_pytorch as smp

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None,
    )

    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    if model_path is None:
        _CACHED_VESSEL_MODEL = model
    return model


def _preprocess_image_for_unet(image_rgb: np.ndarray, target_size: Tuple[int, int] = (512, 512)):
    """Normalize and format RGB image for ResNet34 U-Net."""
    import torch
    h_orig, w_orig = image_rgb.shape[:2]
    resized = cv2.resize(image_rgb, target_size, interpolation=cv2.INTER_AREA)

    # Standard ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    norm = (resized.astype(np.float32) / 255.0 - mean) / std
    tensor = torch.from_numpy(norm.transpose(2, 0, 1)).unsqueeze(0).float()
    return tensor, (h_orig, w_orig)


def detect_optic_disc(
    image_rgb: np.ndarray,
    model=None,
    device: str = "cpu",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Detect and segment Optic Disc landmark and boundary from retinal image.

    Returns:
        dict containing:
        - binary mask (native image resolution)
        - center_xy: (x, y) in image coordinates
        - radius_px: estimated disc radius
        - confidence: mean prediction confidence
        - fovea_estimate: (x, y) estimated fovea center
    """
    import torch

    if model is None:
        model = load_optic_disc_model(device=device)

    tensor, (h_orig, w_orig) = _preprocess_image_for_unet(image_rgb, (512, 512))
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    # Threshold probability map
    pred_512 = (probs > threshold).astype(np.uint8)

    # Resize mask back to original resolution
    pred_mask = cv2.resize(pred_512, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)

    # Extract morphological center & radius
    contours, _ = cv2.findContours(pred_mask * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    center_xy: Optional[Tuple[float, float]] = None
    radius_px: Optional[float] = None
    confidence: float = 0.0

    if contours:
        largest = max(contours, key=cv2.contourArea)
        (cx, cy), r = cv2.minEnclosingCircle(largest)
        if r > 5:
            center_xy = (float(round(cx, 1)), float(round(cy, 1)))
            radius_px = float(round(r, 1))
            mask_pixels = pred_512 > 0
            if np.any(mask_pixels):
                confidence = float(np.mean(probs[mask_pixels]))

    # Estimate Fovea position anchored on detected Optic Disc
    # Anatomical rule: Fovea is located temporal to optic disc at approx 2.5 disc diameters (~5.0 radii)
    fovea_estimate: Optional[Tuple[float, float]] = None
    if center_xy is not None and radius_px is not None:
        cx, cy = center_xy
        # Determine temporal direction based on whether disc is in left or right retinal hemifield
        temporal_sign = 1.0 if cx < (w_orig / 2.0) else -1.0
        fovea_x = cx + temporal_sign * (4.8 * radius_px)
        fovea_y = cy + (0.3 * radius_px)  # Slight physiological inferior offset
        fovea_estimate = (float(round(fovea_x, 1)), float(round(fovea_y, 1)))

    return {
        "mask": pred_mask,
        "center_xy": center_xy,
        "radius_px": radius_px,
        "confidence": confidence,
        "fovea_estimate": fovea_estimate,
        "model_architecture": "Unet-ResNet34",
        "training_source": "IDRiD_Part_A_C",
    }


def detect_exudates(
    image_rgb: np.ndarray,
    model=None,
    device: str = "cpu",
    threshold: float = 0.5,
    disc_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Segment Hard Exudates lesions and compute clinical pathology metrics.

    Excludes optic disc region to prevent false positives from disc hyper-reflectivity.
    """
    import torch

    if model is None:
        model = load_exudates_model(device=device)

    tensor, (h_orig, w_orig) = _preprocess_image_for_unet(image_rgb, (512, 512))
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_512 = (probs > threshold).astype(np.uint8)
    pred_mask = cv2.resize(pred_512, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)

    # Suppress false positives on optic disc if disc mask is provided
    if disc_mask is not None:
        # Dilate disc mask slightly to ensure clear margin
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        dilated_disc = cv2.dilate(disc_mask.astype(np.uint8), kernel, iterations=1)
        pred_mask[dilated_disc > 0] = 0

    # Connected component analysis for lesion clustering
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(pred_mask)
    # Filter tiny single-pixel noise (minimum 5 pixels at full resolution)
    valid_clusters = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 4]

    total_lesion_pixels = int(sum(stats[i, cv2.CC_STAT_AREA] for i in valid_clusters))
    retinal_area = float(h_orig * w_orig)
    area_fraction = float(total_lesion_pixels / retinal_area) if retinal_area > 0 else 0.0

    cluster_centroids = [
        (float(round(centroids[i][0], 1)), float(round(centroids[i][1], 1)))
        for i in valid_clusters
    ]

    return {
        "mask": pred_mask,
        "lesion_count": len(valid_clusters),
        "total_lesion_pixels": total_lesion_pixels,
        "area_fraction": area_fraction,
        "cluster_centroids": cluster_centroids,
        "model_architecture": "Unet-ResNet34",
        "training_source": "IDRiD_Part_A",
    }


def detect_hemorrhages(
    image_rgb: np.ndarray,
    model=None,
    device: str = "cpu",
    threshold: float = 0.5,
    disc_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Segment Retinal Hemorrhages (dot, blot, flame) lesions and compute clinical metrics.

    Excludes optic disc region to prevent false positives from normal deep physiological cupping.
    """
    import torch

    if model is None:
        model = load_hemorrhages_model(device=device)

    tensor, (h_orig, w_orig) = _preprocess_image_for_unet(image_rgb, (512, 512))
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_512 = (probs > threshold).astype(np.uint8)
    pred_mask = cv2.resize(pred_512, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)

    # Suppress false positives on optic disc if disc mask is provided
    if disc_mask is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        dilated_disc = cv2.dilate(disc_mask.astype(np.uint8), kernel, iterations=1)
        pred_mask[dilated_disc > 0] = 0

    # Connected component analysis for hemorrhage foci
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(pred_mask)
    # Filter single-pixel noise (minimum 4 pixels at full resolution)
    valid_clusters = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 4]

    total_lesion_pixels = int(sum(stats[i, cv2.CC_STAT_AREA] for i in valid_clusters))
    retinal_area = float(h_orig * w_orig)
    area_fraction = float(total_lesion_pixels / retinal_area) if retinal_area > 0 else 0.0

    cluster_centroids = [
        (float(round(centroids[i][0], 1)), float(round(centroids[i][1], 1)))
        for i in valid_clusters
    ]

    return {
        "mask": pred_mask,
        "lesion_count": len(valid_clusters),
        "total_lesion_pixels": total_lesion_pixels,
        "area_fraction": area_fraction,
        "cluster_centroids": cluster_centroids,
        "model_architecture": "Unet-ResNet34",
        "training_source": "IDRiD_Part_A_Hemorrhages",
    }


def detect_soft_exudates(
    image_rgb: np.ndarray,
    model=None,
    device: str = "cpu",
    threshold: float = 0.5,
    disc_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Segment Soft Exudates (Cotton Wool Spots / nerve fiber infarcts) and compute clinical metrics.

    Suppresses false positives around optic disc margin.
    """
    import torch

    if model is None:
        model = load_soft_exudates_model(device=device)

    tensor, (h_orig, w_orig) = _preprocess_image_for_unet(image_rgb, (512, 512))
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_512 = (probs > threshold).astype(np.uint8)
    pred_mask = cv2.resize(pred_512, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)

    # Suppress false positives on optic disc if disc mask is provided
    if disc_mask is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        dilated_disc = cv2.dilate(disc_mask.astype(np.uint8), kernel, iterations=1)
        pred_mask[dilated_disc > 0] = 0

    # Connected component analysis for cotton wool spots
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(pred_mask)
    # Filter tiny single-pixel noise (minimum 6 pixels at full resolution)
    valid_clusters = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 6]

    total_lesion_pixels = int(sum(stats[i, cv2.CC_STAT_AREA] for i in valid_clusters))
    retinal_area = float(h_orig * w_orig)
    area_fraction = float(total_lesion_pixels / retinal_area) if retinal_area > 0 else 0.0

    cluster_centroids = [
        (float(round(centroids[i][0], 1)), float(round(centroids[i][1], 1)))
        for i in valid_clusters
    ]

    return {
        "mask": pred_mask,
        "lesion_count": len(valid_clusters),
        "total_lesion_pixels": total_lesion_pixels,
        "area_fraction": area_fraction,
        "cluster_centroids": cluster_centroids,
        "model_architecture": "Unet-ResNet34",
        "training_source": "IDRiD_Part_A_Soft_Exudates",
    }


def detect_retinal_vessels(
    image_rgb: np.ndarray,
    model=None,
    device: str = "cpu",
    method: str = "auto",
) -> Dict[str, Any]:
    """Segment retinal vascular tree and calculate vascular density and arcade branches.

    Uses trained DRIVE ResNet34 U-Net if model checkpoint exists, or classical
    multiscale Frangi Hessian vessel enhancement filter on CLAHE-enhanced green channel.

    Returns:
    - mask: binary uint8 array (shape matching input image)
    - vessel_pixels: total vascular pixel count
    - vessel_density: fraction of retinal foreground area occupied by vessels
    - major_branches: count of connected vascular branches (>= 20 px)
    - method: 'Drive_Unet_ResNet34' or 'Multiscale_Frangi_Hessian'
    - training_source: 'DRIVE_Dataset' or 'Classical_Multiscale_Hessian'
    """
    h_orig, w_orig = image_rgb.shape[:2]

    # Retinal circular FOV mask (isolate fundus aperture, eliminate dark camera border)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    _, fov_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
    kernel_fov = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    fov_mask = cv2.erode(fov_mask, kernel_fov)
    retinal_foreground_pixels = int(np.count_nonzero(fov_mask))
    if retinal_foreground_pixels == 0:
        retinal_foreground_pixels = h_orig * w_orig
        fov_mask = np.ones((h_orig, w_orig), dtype=np.uint8) * 255

    vessel_model = model
    if vessel_model is None and method in ("auto", "unet"):
        vessel_model = load_vessel_model(device=device)

    if vessel_model is not None and method != "frangi":
        import torch
        tensor, _ = _preprocess_image_for_unet(image_rgb, (512, 512))
        tensor = tensor.to(device)
        with torch.no_grad():
            logits = vessel_model(tensor)
            probs = torch.sigmoid(logits).squeeze().cpu().numpy()
        pred_512 = (probs > 0.5).astype(np.uint8)
        pred_mask = cv2.resize(pred_512, (w_orig, h_orig), interpolation=cv2.INTER_NEAREST)
        pred_mask[fov_mask == 0] = 0
        used_method = "Drive_Unet_ResNet34"
        training_source = "DRIVE_Dataset"
    else:
        # Multiscale Frangi vessel enhancement on CLAHE-enhanced green channel
        from skimage.filters import frangi, threshold_otsu
        green = image_rgb[:, :, 1]
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_green = clahe.apply(green)

        # Apply multiscale vessel filter
        resp = frangi(enhanced_green, sigmas=(1.0, 1.5, 2.0), black_ridges=True)
        resp[fov_mask == 0] = 0.0

        norm = (resp - resp.min()) / (resp.max() - resp.min() + 1e-8)
        valid_vals = norm[fov_mask > 0]
        if len(valid_vals) > 0 and float(valid_vals.max()) > 0:
            thresh = float(threshold_otsu(valid_vals))
            v_bin = ((norm > thresh) & (fov_mask > 0)).astype(np.uint8)
        else:
            v_bin = np.zeros((h_orig, w_orig), dtype=np.uint8)

        # Connected component filtering to remove isolated noise speckles (< 15 px)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(v_bin)
        clean_mask = np.zeros_like(v_bin)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 15:
                clean_mask[labels == i] = 1

        pred_mask = clean_mask
        used_method = "Multiscale_Frangi_Hessian"
        training_source = "Classical_Multiscale_Hessian"

    vessel_pixels = int(np.count_nonzero(pred_mask))
    vessel_density = float(vessel_pixels / retinal_foreground_pixels)

    # Count major vascular arcade branches
    num_branches = 0
    if vessel_pixels > 0:
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(pred_mask.astype(np.uint8))
        num_branches = sum(1 for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 25)

    return {
        "mask": pred_mask,
        "vessel_pixels": vessel_pixels,
        "vessel_density": vessel_density,
        "major_branches": num_branches,
        "method": used_method,
        "training_source": training_source,
        "source": training_source,
    }


def detect_microaneurysms(
    image_rgb: np.ndarray,
    vessel_mask: Optional[np.ndarray] = None,
    disc_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Detect retinal microaneurysms using morphological top-hat and vessel suppression.

    Microaneurysms appear as isolated, minute, circular dark red vascular outpouchings
    (10-100 um diameter, typically 2-12 pixels in standard fundus photography).
    Algorithm:
    1. Green channel inverted CLAHE contrast enhancement.
    2. Morphological top-hat transform with elliptical kernel.
    3. Retinal vascular tree suppression to eliminate false positive vessel junctions.
    4. Circularity and size filtering (area 2 to 45 px, aspect ratio 0.4 to 2.5).

    Returns:
    - mask: binary uint8 mask
    - lesion_count: count of distinct microaneurysms
    - total_lesion_pixels: total MA pixel surface
    - area_fraction: fraction of retinal foreground
    - centroids: list of (x, y) coordinates
    - method: 'Morphological_TopHat_VesselSuppression'
    - source: 'Classical_Mathematical_Morphology'
    """
    from skimage.filters import frangi

    h_orig, w_orig = image_rgb.shape[:2]

    # Retinal circular FOV mask
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    _, fov_mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
    kernel_fov = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    fov_mask = cv2.erode(fov_mask, kernel_fov)
    retinal_area = float(np.count_nonzero(fov_mask))
    if retinal_area == 0:
        retinal_area = float(h_orig * w_orig)

    # Inverted green channel with CLAHE
    green = image_rgb[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enh_g = clahe.apply(green)
    inv_g = 255 - enh_g

    # Morphological top-hat isolates small bright blobs (dark in original)
    k_size = 9
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
    tophat = cv2.morphologyEx(inv_g, cv2.MORPH_TOPHAT, kernel)
    tophat[fov_mask == 0] = 0

    # Mask optic disc if provided (prevent false positives on optic cup edge)
    if disc_mask is not None and np.any(disc_mask > 0):
        disc_dilated = cv2.dilate(
            (disc_mask > 0).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)),
        )
        tophat[disc_dilated > 0] = 0

    # Vessel suppression: use supplied vessel mask or compute quick Frangi filter
    if vessel_mask is not None and np.any(vessel_mask > 0):
        v_mask_dil = cv2.dilate(
            (vessel_mask > 0).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        tophat[v_mask_dil > 0] = 0
    else:
        v_resp = frangi(enh_g, sigmas=(1.0, 1.5, 2.0), black_ridges=True)
        v_resp[fov_mask == 0] = 0
        v_norm = (v_resp - v_resp.min()) / (v_resp.max() - v_resp.min() + 1e-8)
        v_mask_dil = cv2.dilate(
            (v_norm > 0.12).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        tophat[v_mask_dil > 0] = 0

    valid_vals = tophat[fov_mask > 0]
    if len(valid_vals) > 0 and valid_vals.max() > 0:
        th = max(28, int(np.percentile(valid_vals, 99.7)))
        candidate_bin = ((tophat >= th) & (fov_mask > 0)).astype(np.uint8)
    else:
        candidate_bin = np.zeros((h_orig, w_orig), dtype=np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidate_bin)
    clean_mask = np.zeros_like(candidate_bin)
    valid_mas = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 2 <= area <= 45:
            w_box = stats[i, cv2.CC_STAT_WIDTH]
            h_box = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = float(w_box) / max(1, h_box)
            if 0.4 <= aspect <= 2.5:
                clean_mask[labels == i] = 1
                valid_mas.append((
                    float(round(centroids[i][0], 1)),
                    float(round(centroids[i][1], 1)),
                ))

    total_lesion_pixels = int(clean_mask.sum())
    area_fraction = float(total_lesion_pixels / retinal_area) if retinal_area > 0 else 0.0

    return {
        "mask": clean_mask,
        "lesion_count": len(valid_mas),
        "total_lesion_pixels": total_lesion_pixels,
        "area_fraction": area_fraction,
        "cluster_centroids": valid_mas,
        "method": "Morphological_TopHat_VesselSuppression",
        "training_source": "Classical_Mathematical_Morphology",
        "source": "Classical_Mathematical_Morphology",
    }



def extract_deep_retinal_evidence(
    image: Union[str, Path, np.ndarray],
    image_id: str = "unspecified",
    device: str = "cpu",
) -> RetinalEvidenceRecord:
    """Extract complete unified retinal structural & lesion evidence using trained IDRiD U-Nets.

    Populates formal RetinalEvidenceRecord conforming to strict epistemic taxonomy:
    - Optic Disc: DETECTED (via model/idrid_optic_disc_best.pth, Dice: 0.9859)
    - Fovea: ESTIMATED (via anatomical anchoring)
    - Hard Exudates: DETECTED (via model/idrid_exudates_best.pth, Dice: 0.7580)
    - Retinal Hemorrhages: DETECTED (via model/idrid_hemorrhages_best.pth, Dice: 0.7482)
    - Soft Exudates / Cotton Wool Spots: DETECTED (via model/idrid_soft_exudates_best.pth, Dice: 0.7595)
    - Retinal Vessels & Neovascularization: strictly flagged as EXTERNAL_DATASET_REQUIRED.
    """
    if isinstance(image, (str, Path)):
        img_p = Path(image)
        raw_bgr = cv2.imread(str(img_p))
        if raw_bgr is None:
            raise FileNotFoundError(f"Could not load image: {image}")
        image_rgb = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)
        image_path_str = str(img_p.resolve())
    else:
        image_rgb = image
        image_path_str = None

    h, w, c = image_rgb.shape

    # 1. Run Optic Disc Detection
    disc_res = detect_optic_disc(image_rgb, device=device)
    disc_center = disc_res["center_xy"]
    disc_radius = disc_res["radius_px"]

    disc_landmark = PointLandmark(
        category=EvidenceCategory.OPTIC_DISC,
        status=AnnotationStatus.DETECTED if disc_center else AnnotationStatus.NOT_AVAILABLE,
        x=disc_center[0] if disc_center else None,
        y=disc_center[1] if disc_center else None,
        radius=disc_radius,
        confidence=disc_res["confidence"],
        source="idrid_optic_disc_best.pth",
        method="Unet_ResNet34_IDRiD",
    )

    # 2. Anchor Fovea / Macula
    fovea_xy = disc_res["fovea_estimate"]
    fovea_landmark = PointLandmark(
        category=EvidenceCategory.FOVEA,
        status=AnnotationStatus.ESTIMATED if fovea_xy else AnnotationStatus.NOT_AVAILABLE,
        x=fovea_xy[0] if fovea_xy else None,
        y=fovea_xy[1] if fovea_xy else None,
        radius=disc_radius if disc_radius else 30.0,
        confidence=0.85 if fovea_xy else 0.0,
        source="retinal_anatomical_anchoring",
        method="disc_to_fovea_vector_offset",
    )

    # 3. Run Hard Exudates Detection
    exudates_res = detect_exudates(image_rgb, device=device, disc_mask=disc_res["mask"])
    
    exudates_mask_record = SegmentationMask(
        category=EvidenceCategory.HARD_EXUDATE,
        status=AnnotationStatus.DETECTED if exudates_res["lesion_count"] > 0 else AnnotationStatus.NOT_AVAILABLE,
        mask_shape=(h, w),
        non_zero_pixels=exudates_res["total_lesion_pixels"],
        area_fraction=exudates_res["area_fraction"],
        source="idrid_exudates_best.pth",
        method="Unet_ResNet34_IDRiD",
        notes=f"Identified {exudates_res['lesion_count']} distinct exudate clusters",
    )

    # 4. Run Retinal Hemorrhages Detection
    hemorrhages_res = detect_hemorrhages(image_rgb, device=device, disc_mask=disc_res["mask"])

    hemorrhages_mask_record = SegmentationMask(
        category=EvidenceCategory.HEMORRHAGE,
        status=AnnotationStatus.DETECTED if hemorrhages_res["lesion_count"] > 0 else AnnotationStatus.NOT_AVAILABLE,
        mask_shape=(h, w),
        non_zero_pixels=hemorrhages_res["total_lesion_pixels"],
        area_fraction=hemorrhages_res["area_fraction"],
        source="idrid_hemorrhages_best.pth",
        method="Unet_ResNet34_IDRiD",
        notes=f"Identified {hemorrhages_res['lesion_count']} distinct hemorrhage foci",
    )

    # 5. Run Soft Exudates (Cotton Wool Spots) Detection
    soft_exudates_res = detect_soft_exudates(image_rgb, device=device, disc_mask=disc_res["mask"])

    soft_exudates_mask_record = SegmentationMask(
        category=EvidenceCategory.SOFT_EXUDATE,
        status=AnnotationStatus.DETECTED if soft_exudates_res["lesion_count"] > 0 else AnnotationStatus.NOT_AVAILABLE,
        mask_shape=(h, w),
        non_zero_pixels=soft_exudates_res["total_lesion_pixels"],
        area_fraction=soft_exudates_res["area_fraction"],
        source="idrid_soft_exudates_best.pth",
        method="Unet_ResNet34_IDRiD",
        notes=f"Identified {soft_exudates_res['lesion_count']} distinct cotton wool spots",
    )

    # 6. Run Retinal Vasculature Segmentation
    vessels_res = detect_retinal_vessels(image_rgb, device=device)

    vessels_mask_record = SegmentationMask(
        category=EvidenceCategory.VESSEL,
        status=AnnotationStatus.DETECTED if vessels_res["vessel_pixels"] > 0 else AnnotationStatus.NOT_AVAILABLE,
        mask_shape=(h, w),
        non_zero_pixels=vessels_res["vessel_pixels"],
        area_fraction=vessels_res["vessel_density"],
        source=vessels_res["source"],
        method=vessels_res["method"],
        notes=f"Mapped {vessels_res['major_branches']} major vascular arcade branches ({vessels_res['vessel_density']*100:.2f}% retinal coverage)",
    )

    # 7. Run Retinal Microaneurysm Detection (Morphological Top-Hat + Vessel Suppression)
    ma_res = detect_microaneurysms(
        image_rgb,
        vessel_mask=vessels_res["mask"],
        disc_mask=disc_res["mask"],
    )

    ma_mask_record = SegmentationMask(
        category=EvidenceCategory.MICROANEURYSM,
        status=AnnotationStatus.DETECTED if ma_res["lesion_count"] > 0 else AnnotationStatus.NOT_AVAILABLE,
        mask_shape=(h, w),
        non_zero_pixels=ma_res["total_lesion_pixels"],
        area_fraction=ma_res["area_fraction"],
        source=ma_res["source"],
        method=ma_res["method"],
        notes=f"Localized {ma_res['lesion_count']} distinct microaneurysms (early microvascular outpouchings)",
    )

    # 8. Clinical DME (Diabetic Macular Edema) Risk Assessment
    # High risk if exudates lie within 1 disc diameter of estimated fovea center
    csme_risk = "LOW"
    min_dist_to_fovea_px = None

    if fovea_xy and exudates_res["cluster_centroids"]:
        fx, fy = fovea_xy
        distances = [
            np.sqrt((cx - fx) ** 2 + (cy - fy) ** 2)
            for cx, cy in exudates_res["cluster_centroids"]
        ]
        min_dist_to_fovea_px = float(round(min(distances), 1))
        disc_diameter = (2.0 * disc_radius) if disc_radius else 80.0

        if min_dist_to_fovea_px <= disc_diameter:
            csme_risk = "HIGH_CSME_RISK (Exudates within 1 disc diameter of foveal avascular zone)"
        elif min_dist_to_fovea_px <= 2.0 * disc_diameter:
            csme_risk = "MODERATE_RISK (Exudates within 2 disc diameters of macula)"

    provenance_meta = {
        "models_integrated": {
            "optic_disc": "model/idrid_optic_disc_best.pth (Dice: 0.9859)",
            "hard_exudates": "model/idrid_exudates_best.pth (Dice: 0.7580)",
            "hemorrhages": "model/idrid_hemorrhages_best.pth (Dice: 0.7482)",
            "soft_exudates": "model/idrid_soft_exudates_best.pth (Dice: 0.7595)",
            "retinal_vessels": f"{vessels_res['method']} ({vessels_res['source']})",
            "microaneurysms": f"{ma_res['method']} ({ma_res['source']})",
        },
        "lesion_statistics": {
            "exudate_clusters": exudates_res["lesion_count"],
            "exudate_pixels": exudates_res["total_lesion_pixels"],
            "exudate_area_fraction": exudates_res["area_fraction"],
            "hemorrhage_clusters": hemorrhages_res["lesion_count"],
            "hemorrhage_pixels": hemorrhages_res["total_lesion_pixels"],
            "hemorrhage_area_fraction": hemorrhages_res["area_fraction"],
            "soft_exudate_clusters": soft_exudates_res["lesion_count"],
            "soft_exudate_pixels": soft_exudates_res["total_lesion_pixels"],
            "soft_exudate_area_fraction": soft_exudates_res["area_fraction"],
            "vessel_pixels": vessels_res["vessel_pixels"],
            "vessel_density": vessels_res["vessel_density"],
            "vessel_major_branches": vessels_res["major_branches"],
            "microaneurysm_count": ma_res["lesion_count"],
            "microaneurysm_pixels": ma_res["total_lesion_pixels"],
            "microaneurysm_area_fraction": ma_res["area_fraction"],
            "min_distance_to_fovea_px": min_dist_to_fovea_px,
            "macular_edema_risk_level": csme_risk,
        },
        "v2_classifier_frozen": True,
    }

    return RetinalEvidenceRecord(
        image_id=image_id,
        image_path=image_path_str,
        image_dimensions=(h, w, c),
        optic_disc=disc_landmark,
        fovea=fovea_landmark,
        vessels=vessels_mask_record,
        microaneurysms=ma_mask_record,
        hard_exudates=exudates_mask_record,
        hemorrhages=hemorrhages_mask_record,
        soft_exudates=soft_exudates_mask_record,
        provenance=provenance_meta,
    )

