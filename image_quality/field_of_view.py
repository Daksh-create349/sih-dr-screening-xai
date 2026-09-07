"""Field of View (FOV) and Retinal Centering Assessment module for retinal fundus images.

Evaluates:
1. Retinal field coverage percentage relative to frame and maximum inscribable circular field.
2. Geometric retinal field centering (radial offset, horizontal/vertical offset from image center).
3. Classical computer vision optic disc localization candidate scoring and confidence estimation.
4. Engineering classifications:
   - FOV: 'Adequate FOV', 'Borderline FOV', 'Poor FOV'
   - Centering: 'Well Centered', 'Borderline Centering', 'Poor Centering'

NOTE: Thresholds and optic disc localization are engineering prototypes derived from observed
retinal fundus geometry, pending formal clinical validation. Retinal field centering (framing)
is distinctly separated from anatomical optic-disc localization.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, Tuple, List
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from image_quality.io import load_raw_image, preprocess_image
from image_quality.focus import compute_foreground_mask

# Engineering baseline thresholds (unvalidated clinically)
ENGINEERING_POOR_FOV_THRESHOLD = 50.0        # Below this: Poor FOV
ENGINEERING_ADEQUATE_FOV_THRESHOLD = 75.0    # At or above this: Adequate FOV

ENGINEERING_WELL_CENTERED_MAX_OFFSET = 0.08  # Normalized radial offset <= 0.08: Well Centered
ENGINEERING_POOR_CENTERED_MIN_OFFSET = 0.20  # Normalized radial offset > 0.20: Poor Centering


def detect_retinal_field(
    image: Any,
    tol: int = 15,
) -> Dict[str, Any]:
    """Segment retinal foreground and compute geometric coverage metrics.

    Args:
        image: RGB image array.
        tol: Grayscale intensity threshold for background separation.

    Returns:
        dict: Retinal area, coverage percentage, bounding box, aspect ratio, and binary mask.
    """
    h, w = image.shape[:2]
    mask = compute_foreground_mask(image, tol=tol)

    # Connected components to isolate the primary retinal disc
    if cv2 is not None:
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
        if num_labels > 1:
            largest_idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            retina_mask = (labels == largest_idx)
            area = int(stats[largest_idx, cv2.CC_STAT_AREA])
            bx = int(stats[largest_idx, cv2.CC_STAT_LEFT])
            by = int(stats[largest_idx, cv2.CC_STAT_TOP])
            bw = int(stats[largest_idx, cv2.CC_STAT_WIDTH])
            bh = int(stats[largest_idx, cv2.CC_STAT_HEIGHT])
        else:
            retina_mask = mask
            area = int(np.sum(mask))
            bx, by, bw, bh = 0, 0, w, h
    else:
        from scipy.ndimage import label
        labels, num_labels = label(mask)
        if num_labels > 0:
            counts = np.bincount(labels.ravel())[1:]
            largest_idx = 1 + int(np.argmax(counts))
            retina_mask = (labels == largest_idx)
            area = int(np.sum(retina_mask))
            y_idx, x_idx = np.where(retina_mask)
            bx, by = int(x_idx.min()), int(y_idx.min())
            bw, bh = int(x_idx.max() - bx + 1), int(y_idx.max() - by + 1)
        else:
            retina_mask = mask
            area = int(np.sum(mask))
            bx, by, bw, bh = 0, 0, w, h

    total_image_pixels = h * w
    coverage_pct = round(float((area / total_image_pixels) * 100.0), 2) if total_image_pixels > 0 else 0.0

    # Maximum possible circular field that can fit within image frame
    r_fit = min(w, h) / 2.0
    a_max_fit = np.pi * (r_fit ** 2)
    fov_score = round(float(np.clip((area / a_max_fit) * 100.0, 0.0, 100.0)), 2) if a_max_fit > 0 else 0.0

    aspect_ratio = round(float(bw / bh), 3) if bh > 0 else 1.0

    return {
        "retinal_area_pixels": area,
        "total_image_pixels": total_image_pixels,
        "coverage_pct": coverage_pct,
        "fov_score": fov_score,
        "bounding_box": [bx, by, bw, bh],
        "aspect_ratio": aspect_ratio,
        "mask": retina_mask,
    }


def estimate_retinal_center(
    mask: Any,
    image_shape: Tuple[int, int],
) -> Dict[str, Any]:
    """Calculate geometric center of detected retinal field and normalized offsets.

    Args:
        mask: Boolean mask of retinal foreground.
        image_shape: (height, width) of image.

    Returns:
        dict: Coordinates of retinal center, image center, horizontal/vertical/radial offsets, and centering score.
    """
    h, w = image_shape
    img_cx, img_cy = w / 2.0, h / 2.0

    y_idx, x_idx = np.where(mask)
    if len(y_idx) > 0:
        rc_x = float(np.mean(x_idx))
        rc_y = float(np.mean(y_idx))
    else:
        rc_x, rc_y = img_cx, img_cy

    dx_norm = abs(rc_x - img_cx) / img_cx if img_cx > 0 else 0.0
    dy_norm = abs(rc_y - img_cy) / img_cy if img_cy > 0 else 0.0
    radial_offset = float(np.sqrt(dx_norm ** 2 + dy_norm ** 2))

    # Centering score bounded in [0.0, 100.0]
    # Linear penalty: 0 offset -> 100.0; 0.20 offset -> 50.0; > 0.40 offset -> 0.0
    centering_score = round(float(np.clip(100.0 * (1.0 - 2.5 * radial_offset), 0.0, 100.0)), 2)

    return {
        "retinal_center": [round(rc_x, 2), round(rc_y, 2)],
        "image_center": [round(img_cx, 2), round(img_cy, 2)],
        "normalized_horizontal_offset": round(float(dx_norm), 4),
        "normalized_vertical_offset": round(float(dy_norm), 4),
        "radial_center_offset": round(float(radial_offset), 4),
        "centering_score": centering_score,
    }


def locate_optic_disc_candidate(
    image: Any,
    mask: Any,
) -> Dict[str, Any]:
    """Candidate localization for the anatomical optic disc using classical computer vision.

    NOTE: Classical intensity/morphology methods are heuristic prototypes and may be confounded
    by bright pathology (cotton wool spots, dense hard exudates, or peripheral camera reflections).
    Returns an explicit confidence score and reliability flag.

    Args:
        image: RGB image array of shape (H, W, 3).
        mask: Boolean mask of retinal foreground.

    Returns:
        dict: Optic disc detection metadata, estimated center, radius, and confidence.
    """
    h, w = image.shape[:2]

    # Interior distance transform to suppress false peripheral camera rim artifacts
    if cv2 is not None:
        dist_map = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    else:
        from scipy.ndimage import distance_transform_edt
        dist_map = distance_transform_edt(mask)

    max_dist = float(np.max(dist_map)) if np.max(dist_map) > 0 else 1.0
    interior_mask = dist_map > (0.15 * max_dist)

    if not np.any(interior_mask):
        return {
            "detected": False,
            "center": None,
            "radius": None,
            "confidence": 0.0,
            "is_reliable": False,
            "method": "interior_morphology_candidate_scoring",
            "notes": "Insufficient interior retinal foreground.",
        }

    red = image[:, :, 0].astype(np.float64)
    if cv2 is not None:
        gray = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64)
    else:
        gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.float64)

    # Optic disc has high red intensity and high luminance
    bright = (0.7 * red + 0.3 * gray) * interior_mask

    # Morphological opening to suppress thin vessels and tiny punctate exudates
    k_size = max(9, int(min(w, h) * 0.04))
    if cv2 is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        opened = cv2.morphologyEx(bright.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    else:
        from scipy.ndimage import grey_opening
        opened = grey_opening(bright.astype(np.uint8), size=(k_size, k_size))

    fg_vals = opened[interior_mask]
    if len(fg_vals) == 0:
        return {
            "detected": False,
            "center": None,
            "radius": None,
            "confidence": 0.0,
            "is_reliable": False,
            "method": "interior_morphology_candidate_scoring",
            "notes": "No bright interior candidates found.",
        }

    p97 = float(np.percentile(fg_vals, 97.0))
    cand_mask = (opened >= p97) & interior_mask

    if cv2 is not None:
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cand_mask.astype(np.uint8))
    else:
        from scipy.ndimage import label
        labels, num_labels = label(cand_mask)

    # Expected physiological disc radius is ~5-8% of retinal diameter
    expected_area = np.pi * ((min(w, h) * 0.065) ** 2)
    best_cand = None
    best_score = -1.0

    if cv2 is not None:
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if 0.1 * expected_area < area < 4.0 * expected_area:
                cx_c, cy_c = centroids[i]
                bw_c = stats[i, cv2.CC_STAT_WIDTH]
                bh_c = stats[i, cv2.CC_STAT_HEIGHT]
                aspect = min(bw_c, bh_c) / max(bw_c, bh_c) if max(bw_c, bh_c) > 0 else 0.0
                area_ratio = min(area / expected_area, expected_area / area) if area > 0 else 0.0
                mean_int = float(np.mean(opened[labels == i])) / 255.0

                score = 0.5 * mean_int + 0.3 * aspect + 0.2 * area_ratio
                if score > best_score:
                    best_score = score
                    radius = int(round(np.sqrt(area / np.pi)))
                    best_cand = {
                        "detected": True,
                        "center": [round(float(cx_c), 1), round(float(cy_c), 1)],
                        "radius": radius,
                        "confidence": round(float(min(1.0, score)), 2),
                        "is_reliable": bool(score >= 0.65),
                        "method": "interior_morphology_candidate_scoring",
                        "notes": "Optic disc candidate localized within expected physiological dimensions.",
                    }
    else:
        for i in range(1, num_labels + 1):
            comp_mask = (labels == i)
            area = int(np.sum(comp_mask))
            if 0.1 * expected_area < area < 4.0 * expected_area:
                y_c, x_c = np.where(comp_mask)
                cx_c, cy_c = float(np.mean(x_c)), float(np.mean(y_c))
                bw_c = float(x_c.max() - x_c.min() + 1)
                bh_c = float(y_c.max() - y_c.min() + 1)
                aspect = min(bw_c, bh_c) / max(bw_c, bh_c) if max(bw_c, bh_c) > 0 else 0.0
                area_ratio = min(area / expected_area, expected_area / area) if area > 0 else 0.0
                mean_int = float(np.mean(opened[comp_mask])) / 255.0

                score = 0.5 * mean_int + 0.3 * aspect + 0.2 * area_ratio
                if score > best_score:
                    best_score = score
                    radius = int(round(np.sqrt(area / np.pi)))
                    best_cand = {
                        "detected": True,
                        "center": [round(float(cx_c), 1), round(float(cy_c), 1)],
                        "radius": radius,
                        "confidence": round(float(min(1.0, score)), 2),
                        "is_reliable": bool(score >= 0.65),
                        "method": "interior_morphology_candidate_scoring",
                        "notes": "Optic disc candidate localized within expected physiological dimensions.",
                    }

    if best_cand is None:
        return {
            "detected": False,
            "center": None,
            "radius": None,
            "confidence": 0.0,
            "is_reliable": False,
            "method": "interior_morphology_candidate_scoring",
            "notes": "No candidate matched expected optic disc geometry or brightness contrast.",
        }

    return best_cand


def classify_fov_and_centering(
    fov_score: float,
    radial_offset: float,
    poor_fov_thresh: float = ENGINEERING_POOR_FOV_THRESHOLD,
    adequate_fov_thresh: float = ENGINEERING_ADEQUATE_FOV_THRESHOLD,
    well_centered_max_offset: float = ENGINEERING_WELL_CENTERED_MAX_OFFSET,
    poor_centered_min_offset: float = ENGINEERING_POOR_CENTERED_MIN_OFFSET,
) -> Tuple[str, str]:
    """Classify FOV completeness and retinal centering into engineering categories.

    Args:
        fov_score: Normalized FOV score in [0.0, 100.0].
        radial_offset: Normalized radial offset from image center.
        poor_fov_thresh: FOV score below which is Poor FOV.
        adequate_fov_thresh: FOV score at/above which is Adequate FOV.
        well_centered_max_offset: Maximum radial offset for Well Centered.
        poor_centered_min_offset: Minimum radial offset for Poor Centering.

    Returns:
        tuple[str, str]: (fov_decision, centering_decision)
    """
    if fov_score >= adequate_fov_thresh:
        fov_decision = "Adequate FOV"
    elif fov_score >= poor_fov_thresh:
        fov_decision = "Borderline FOV"
    else:
        fov_decision = "Poor FOV"

    if radial_offset <= well_centered_max_offset:
        centering_decision = "Well Centered"
    elif radial_offset <= poor_centered_min_offset:
        centering_decision = "Borderline Centering"
    else:
        centering_decision = "Poor Centering"

    return fov_decision, centering_decision


def assess_field_of_view(
    image_or_path: Union[str, Path, Any],
    target_size: Optional[Tuple[int, int]] = (384, 384),
    poor_fov_threshold: float = ENGINEERING_POOR_FOV_THRESHOLD,
    adequate_fov_threshold: float = ENGINEERING_ADEQUATE_FOV_THRESHOLD,
    well_centered_max_offset: float = ENGINEERING_WELL_CENTERED_MAX_OFFSET,
    poor_centered_min_offset: float = ENGINEERING_POOR_CENTERED_MIN_OFFSET,
) -> Dict[str, Any]:
    """Complete evaluation of retinal Field of View, field centering, and optic disc localization.

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Optional resolution for standardization (default: (384, 384)).
        poor_fov_threshold: Cutoff for Poor FOV.
        adequate_fov_threshold: Cutoff for Adequate FOV.
        well_centered_max_offset: Cutoff for Well Centered.
        poor_centered_min_offset: Cutoff for Poor Centering.

    Returns:
        dict: Complete structured FOV evaluation containing:
            - image_path: Path string or 'in_memory_array'
            - image_dimensions: [width, height]
            - retinal_foreground_area: Total foreground pixels
            - coverage_pct: Percentage of image frame covered by retina
            - bounding_box: [x, y, w, h] of retinal disc
            - aspect_ratio: Width / Height of bounding box
            - retinal_center: [cx, cy]
            - image_center: [cx, cy]
            - normalized_horizontal_offset: dx / (w/2)
            - normalized_vertical_offset: dy / (h/2)
            - radial_center_offset: Euclidean distance of normalized offsets
            - fov_score: Normalized FOV score [0.0, 100.0]
            - centering_score: Normalized centering score [0.0, 100.0]
            - optic_disc: Candidate localization dict
            - fov_decision: 'Adequate FOV', 'Borderline FOV', 'Poor FOV'
            - centering_decision: 'Well Centered', 'Borderline Centering', 'Poor Centering'
            - diagnostics: Supporting metadata
            - thresholds: Documented baseline thresholds and validation status
    """
    image_path_str = str(image_or_path) if isinstance(image_or_path, (str, Path)) else "in_memory_array"

    # 1. Load image
    if isinstance(image_or_path, (str, Path)):
        raw_img = load_raw_image(image_or_path)
    else:
        raw_img = image_or_path.copy()

    if raw_img.ndim != 3 or raw_img.shape[2] != 3:
        raise ValueError(f"Expected 3-channel RGB image, got shape {raw_img.shape}")

    # 2. Standardize resolution if requested
    if target_size is not None:
        eval_img = preprocess_image(raw_img, target_size=target_size, crop_borders=True)
        eval_img_u8 = eval_img.astype(np.uint8)
    else:
        eval_img_u8 = raw_img

    h, w = eval_img_u8.shape[:2]

    # 3. Detect retinal field & coverage
    fov_res = detect_retinal_field(eval_img_u8, tol=15)
    retina_mask = fov_res["mask"]

    # 4. Estimate retinal field center & offsets
    center_res = estimate_retinal_center(retina_mask, (h, w))

    # 5. Locate optic disc candidate
    disc_res = locate_optic_disc_candidate(eval_img_u8, retina_mask)

    # 6. Classify FOV and centering
    fov_dec, center_dec = classify_fov_and_centering(
        fov_res["fov_score"],
        center_res["radial_center_offset"],
        poor_fov_thresh=poor_fov_threshold,
        adequate_fov_thresh=adequate_fov_threshold,
        well_centered_max_offset=well_centered_max_offset,
        poor_centered_min_offset=poor_centered_min_offset,
    )

    return {
        "image_path": image_path_str,
        "image_dimensions": [w, h],
        "retinal_foreground_area": fov_res["retinal_area_pixels"],
        "coverage_pct": fov_res["coverage_pct"],
        "bounding_box": fov_res["bounding_box"],
        "aspect_ratio": fov_res["aspect_ratio"],
        "retinal_center": center_res["retinal_center"],
        "image_center": center_res["image_center"],
        "normalized_horizontal_offset": center_res["normalized_horizontal_offset"],
        "normalized_vertical_offset": center_res["normalized_vertical_offset"],
        "radial_center_offset": center_res["radial_center_offset"],
        "fov_score": fov_res["fov_score"],
        "centering_score": center_res["centering_score"],
        "optic_disc": disc_res,
        "fov_decision": fov_dec,
        "centering_decision": center_dec,
        "diagnostics": {
            "resolution_evaluated": [w, h],
            "total_pixels": fov_res["total_image_pixels"],
            "centering_vs_disc_distinction": "Retinal center measures camera field framing. Optic disc candidate measures anatomical landmark.",
        },
        "thresholds": {
            "poor_fov_threshold": poor_fov_threshold,
            "adequate_fov_threshold": adequate_fov_threshold,
            "well_centered_max_offset": well_centered_max_offset,
            "poor_centered_min_offset": poor_centered_min_offset,
            "status": "engineering_baseline_not_clinically_validated",
            "clinical_validation": False,
        },
    }
