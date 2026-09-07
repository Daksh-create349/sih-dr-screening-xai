"""Retinal Structure and Lesion Metric Definitions and Anatomy Bridges.

Implements Task 11 and Task 12:
- Bridge between existing anatomy detector/heuristics and ground truth annotations.
- Standardized ophthalmic evaluation metrics for landmarks and binary segmentations.
- Preserves absolute distinction between DETECTED, ESTIMATED, and GROUND_TRUTH.
"""

from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
from pathlib import Path

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)
from explainability.anatomy import (
    localize_retinal_anatomy,
    define_anatomical_regions,
    compute_attention_region_statistics,
)
from image_quality.io import load_raw_image


def compute_euclidean_distance(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
) -> float:
    """Calculate Euclidean distance between two planar coordinates."""
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2))


def compare_landmark_localization(
    predicted: PointLandmark,
    ground_truth: PointLandmark,
    normalization_scale: Optional[float] = None,
    tolerance_threshold: float = 1.0,
) -> Dict[str, Any]:
    """Compare a predicted/estimated landmark against ground truth.

    Args:
        predicted: PointLandmark with status DETECTED or ESTIMATED.
        ground_truth: PointLandmark with status GROUND_TRUTH.
        normalization_scale: Typically the optic disc radius in pixels.
        tolerance_threshold: Maximum normalized error for success (default: 1.0 radius).

    Returns:
        dict: Absolute pixel error, normalized error, and binary localization success.
    """
    if not predicted.is_available():
        return {
            "status": "PREDICTED_UNAVAILABLE",
            "pixel_distance": None,
            "normalized_distance": None,
            "success": False,
        }

    if not ground_truth.is_available():
        return {
            "status": "GROUND_TRUTH_UNAVAILABLE",
            "pixel_distance": None,
            "normalized_distance": None,
            "success": False,
        }

    dist = compute_euclidean_distance((predicted.x, predicted.y), (ground_truth.x, ground_truth.y))

    norm_dist = None
    success = False
    scale = normalization_scale or ground_truth.radius or predicted.radius

    if scale is not None and scale > 0:
        norm_dist = dist / scale
        success = bool(norm_dist <= tolerance_threshold)
    else:
        # If no radius provided, default to tolerance in pixels
        tol_px = ground_truth.tolerance_pixels or predicted.tolerance_pixels or 50.0
        success = bool(dist <= tol_px)

    return {
        "status": "COMPARED",
        "category": ground_truth.category.value,
        "predicted_method": predicted.method,
        "predicted_status": predicted.status.value,
        "ground_truth_status": ground_truth.status.value,
        "pixel_distance": round(dist, 2),
        "normalization_scale": round(scale, 2) if scale else None,
        "normalized_distance": round(norm_dist, 3) if norm_dist is not None else None,
        "tolerance_threshold": tolerance_threshold,
        "success": success,
    }


def compute_segmentation_metrics(
    pred_mask: np.ndarray,
    gt_mask: np.ndarray,
) -> Dict[str, Any]:
    """Calculate standard spatial overlap metrics for binary segmentations.

    Metrics:
    - Dice Similarity Coefficient (F1 score): 2 * |P ∩ G| / (|P| + |G|)
    - Intersection over Union (IoU / Jaccard): |P ∩ G| / |P ∪ G|
    - Sensitivity (True Positive Rate / Recall): TP / (TP + FN)
    - Specificity (True Negative Rate): TN / (TN + FP)
    - Precision (Positive Predictive Value): TP / (TP + FP)
    """
    p = (np.asarray(pred_mask) > 0).astype(bool)
    g = (np.asarray(gt_mask) > 0).astype(bool)

    if p.shape != g.shape:
        raise ValueError(f"Shape mismatch between prediction {p.shape} and ground truth {g.shape}")

    tp = int(np.sum(p & g))
    fp = int(np.sum(p & (~g)))
    fn = int(np.sum((~p) & g))
    tn = int(np.sum((~p) & (~g)))

    intersection = tp
    sum_areas = int(np.sum(p)) + int(np.sum(g))
    union = tp + fp + fn

    dice = float((2.0 * intersection) / sum_areas) if sum_areas > 0 else 1.0
    iou = float(intersection / union) if union > 0 else 1.0
    sens = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 1.0
    prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0

    return {
        "dice": round(dice, 4),
        "iou": round(iou, 4),
        "sensitivity": round(sens, 4),
        "specificity": round(spec, 4),
        "precision": round(prec, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
    }


def extract_evidence_from_existing_anatomy(
    image_or_path: Union[str, Path, np.ndarray],
    image_id: str = "local_image",
) -> RetinalEvidenceRecord:
    """Execute current engineering anatomy detectors and package as RetinalEvidenceRecord.

    Explicitly labels:
    - Optic disc candidate as DETECTED (via interior morphology)
    - Macula center as ESTIMATED (via geometric displacement and photometric minimum)
    - Lesions as NOT_AVAILABLE (until genuine segmenters are trained)
    """
    img = load_raw_image(image_or_path) if isinstance(image_or_path, (str, Path)) else image_or_path
    h, w = img.shape[:2]

    # Run existing anatomical landmark detector
    landmarks = localize_retinal_anatomy(img)
    od_res = landmarks.get("optic_disc", {})
    od_center = od_res.get("center")
    od_radius = od_res.get("radius", 25.0)
    od_conf = od_res.get("confidence", 0.0)

    od_landmark = PointLandmark(
        category=EvidenceCategory.OPTIC_DISC,
        status=AnnotationStatus.DETECTED if od_res.get("detected") else AnnotationStatus.NOT_AVAILABLE,
        x=float(od_center[0]) if od_center else None,
        y=float(od_center[1]) if od_center else None,
        radius=float(od_radius) if od_radius else None,
        confidence=float(od_conf) if od_conf else None,
        source="internal_engineering_detector",
        method=od_res.get("method", "interior_morphology_candidate_scoring"),
        notes=od_res.get("notes"),
    )

    mac_res = landmarks.get("macula", {})
    mac_center = mac_res.get("center")
    mac_radius = mac_res.get("radius", 30.0)
    mac_conf = mac_res.get("confidence", 0.0)

    mac_landmark = PointLandmark(
        category=EvidenceCategory.FOVEA,
        status=AnnotationStatus.ESTIMATED if mac_res.get("detected") else AnnotationStatus.NOT_AVAILABLE,
        x=float(mac_center[0]) if mac_center else None,
        y=float(mac_center[1]) if mac_center else None,
        radius=float(mac_radius) if mac_radius else None,
        confidence=float(mac_conf) if mac_conf else None,
        source="internal_engineering_heuristic",
        method=mac_res.get("method", "geometric_displacement_and_photometric_minimum"),
        notes=mac_res.get("notes"),
    )

    return RetinalEvidenceRecord(
        image_id=image_id,
        image_path=str(image_or_path) if isinstance(image_or_path, (str, Path)) else None,
        image_dimensions=(h, w, 3),
        optic_disc=od_landmark,
        fovea=mac_landmark,
        provenance={
            "extractor": "extract_evidence_from_existing_anatomy",
            "classifier_model_modified": False,
            "v2_model_frozen": True,
        },
    )
