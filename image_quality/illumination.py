"""Illumination and Exposure Assessment module for retinal fundus images.

Evaluates:
1. Global foreground brightness (mean, median, 5th/95th percentiles, std).
2. Exposure adequacy (detecting underexposure and overexposure/saturation).
3. Illumination uniformity (coefficient of variation, quadrant imbalance, center-to-periphery ratio).
4. Composite illumination quality score [0.0, 100.0].
5. Engineering classification into 'Well Illuminated', 'Borderline Illumination', or 'Poor Illumination'.

NOTE: All thresholds are engineering baseline heuristics established from real retinal fundus
distributions, pending formal clinical ophthalmology validation.
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
ENGINEERING_POOR_THRESHOLD = 45.0          # Below this: Poor Illumination
ENGINEERING_WELL_THRESHOLD = 65.0          # At or above this: Well Illuminated
OPTIMAL_MEAN_LUMINANCE = 115.0             # Optimal target mean brightness in [0, 255]
LUMINANCE_TOLERANCE_SIGMA = 45.0           # Gaussian width parameter for exposure penalty
DARK_PIXEL_INTENSITY_CUTOFF = 30.0         # Pixels below this within foreground are dark
BRIGHT_PIXEL_INTENSITY_CUTOFF = 220.0      # Pixels above this within foreground are saturated/glare
EXCESSIVE_DARK_PCT_CUTOFF = 20.0           # Percentage of dark pixels incurring severe penalty
EXCESSIVE_BRIGHT_PCT_CUTOFF = 15.0         # Percentage of bright pixels incurring severe penalty


def extract_luminance(image: np.ndarray) -> np.ndarray:
    """Extract 2D perceptual luminance array (Y component) from RGB image.

    L = 0.299*R + 0.587*G + 0.114*B (ITU-R BT.601 standard).

    Args:
        image: RGB image array of shape (H, W, 3).

    Returns:
        np.ndarray: 2D float64 luminance array.
    """
    if image.ndim == 2:
        return image.astype(np.float64)

    if cv2 is not None:
        return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64)

    return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.float64)


def compute_brightness_statistics(
    luminance: np.ndarray,
    mask: np.ndarray,
    dark_cutoff: float = DARK_PIXEL_INTENSITY_CUTOFF,
    bright_cutoff: float = BRIGHT_PIXEL_INTENSITY_CUTOFF,
) -> Dict[str, float]:
    """Calculate statistical distribution of luminance within retinal foreground.

    Args:
        luminance: 2D float64 luminance array.
        mask: Boolean mask of retinal foreground.
        dark_cutoff: Pixel intensity threshold below which a pixel is considered dark.
        bright_cutoff: Pixel intensity threshold above which a pixel is considered saturated.

    Returns:
        dict: Brightness statistics within foreground.
    """
    fg_pixels = luminance[mask]
    if fg_pixels.size == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "p5": 0.0,
            "p95": 0.0,
            "dark_pixel_pct": 0.0,
            "bright_pixel_pct": 0.0,
        }

    mean_val = float(np.mean(fg_pixels))
    med_val = float(np.median(fg_pixels))
    std_val = float(np.std(fg_pixels))
    p5 = float(np.percentile(fg_pixels, 5))
    p95 = float(np.percentile(fg_pixels, 95))

    dark_pct = float(np.mean(fg_pixels < dark_cutoff) * 100.0)
    bright_pct = float(np.mean(fg_pixels > bright_cutoff) * 100.0)

    return {
        "mean": round(mean_val, 2),
        "median": round(med_val, 2),
        "std": round(std_val, 2),
        "p5": round(p5, 2),
        "p95": round(p95, 2),
        "dark_pixel_pct": round(dark_pct, 2),
        "bright_pixel_pct": round(bright_pct, 2),
    }


def compute_regional_illumination(
    luminance: np.ndarray,
    mask: np.ndarray,
) -> Dict[str, Any]:
    """Compute spatial illumination uniformity across quadrants and center vs periphery.

    Args:
        luminance: 2D float64 luminance array.
        mask: Boolean mask of retinal foreground.

    Returns:
        dict: Quadrant means, quadrant imbalance, center mean, periphery mean, and C/P ratio.
    """
    h, w = luminance.shape
    cy, cx = h / 2.0, w / 2.0
    fg_pixels = luminance[mask]
    global_mean = float(np.mean(fg_pixels)) if fg_pixels.size > 0 else 1.0

    # 4 Quadrants: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    y_idx, x_idx = np.ogrid[:h, :w]
    tl_m = mask & (y_idx < cy) & (x_idx < cx)
    tr_m = mask & (y_idx < cy) & (x_idx >= cx)
    bl_m = mask & (y_idx >= cy) & (x_idx < cx)
    br_m = mask & (y_idx >= cy) & (x_idx >= cx)

    q_means = {
        "top_left": round(float(np.mean(luminance[tl_m])), 2) if np.any(tl_m) else global_mean,
        "top_right": round(float(np.mean(luminance[tr_m])), 2) if np.any(tr_m) else global_mean,
        "bottom_left": round(float(np.mean(luminance[bl_m])), 2) if np.any(bl_m) else global_mean,
        "bottom_right": round(float(np.mean(luminance[br_m])), 2) if np.any(br_m) else global_mean,
    }

    q_vals = list(q_means.values())
    quadrant_imbalance = round(float((max(q_vals) - min(q_vals)) / global_mean), 4) if global_mean > 0 else 0.0

    # Center vs Periphery analysis
    y_coords, x_coords = np.where(mask)
    if len(y_coords) > 0:
        centroid_y, centroid_x = np.mean(y_coords), np.mean(x_coords)
        dists = np.sqrt((y_idx - centroid_y) ** 2 + (x_idx - centroid_x) ** 2)
        r_max = np.max(dists[mask])
        center_m = mask & (dists <= 0.5 * r_max)
        periph_m = mask & (dists > 0.5 * r_max)

        c_mean = float(np.mean(luminance[center_m])) if np.any(center_m) else global_mean
        p_mean = float(np.mean(luminance[periph_m])) if np.any(periph_m) else global_mean
        cp_ratio = round(float(c_mean / p_mean), 3) if p_mean > 0 else 1.0
    else:
        c_mean, p_mean, cp_ratio = global_mean, global_mean, 1.0

    return {
        "quadrant_means": q_means,
        "quadrant_imbalance": quadrant_imbalance,
        "center_mean": round(c_mean, 2),
        "periphery_mean": round(p_mean, 2),
        "center_periphery_ratio": cp_ratio,
    }


def compute_uniformity_score(
    std_val: float,
    mean_val: float,
    quadrant_imbalance: float,
) -> float:
    """Compute normalized spatial illumination uniformity score in [0.0, 100.0].

    Higher score means more uniform, balanced lighting across the retinal disc.

    Args:
        std_val: Standard deviation of foreground luminance.
        mean_val: Mean foreground luminance.
        quadrant_imbalance: Fractional difference between brightest and darkest quadrants.

    Returns:
        float: Uniformity score bounded in [0.0, 100.0].
    """
    if mean_val <= 0.0:
        return 0.0

    cv = std_val / mean_val
    # Penalty based on coefficient of variation (spatial dispersion) and regional imbalance
    penalty = 0.8 * cv + 0.6 * quadrant_imbalance
    score = 100.0 * max(0.0, 1.0 - penalty)
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def compute_exposure_score(
    mean_val: float,
    dark_pct: float,
    bright_pct: float,
    optimal_mean: float = OPTIMAL_MEAN_LUMINANCE,
    sigma_mean: float = LUMINANCE_TOLERANCE_SIGMA,
) -> float:
    """Compute normalized exposure adequacy score in [0.0, 100.0].

    Penalizes images whose mean intensity deviates from optimal retinal fundus
    luminance (~115), or that suffer from dark/bright clipping.

    Args:
        mean_val: Mean foreground luminance.
        dark_pct: Percentage of dark pixels in foreground (< 30).
        bright_pct: Percentage of bright/saturated pixels in foreground (> 220).
        optimal_mean: Target mean brightness.
        sigma_mean: Gaussian width parameter.

    Returns:
        float: Exposure score bounded in [0.0, 100.0].
    """
    if mean_val <= 0.0:
        return 0.0

    # Gaussian distance factor from optimal brightness
    mean_factor = np.exp(-0.5 * ((mean_val - optimal_mean) / sigma_mean) ** 2)

    # Clipping penalty
    dark_penalty = dark_pct / EXCESSIVE_DARK_PCT_CUTOFF
    bright_penalty = bright_pct / EXCESSIVE_BRIGHT_PCT_CUTOFF
    clip_factor = max(0.0, 1.0 - dark_penalty - bright_penalty)

    score = 100.0 * mean_factor * clip_factor
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def classify_illumination(
    overall_score: float,
    dark_pct: float,
    bright_pct: float,
    poor_thresh: float = ENGINEERING_POOR_THRESHOLD,
    well_thresh: float = ENGINEERING_WELL_THRESHOLD,
) -> str:
    """Classify illumination quality based on overall score and clipping sanity.

    Args:
        overall_score: Combined illumination score in [0.0, 100.0].
        dark_pct: Percentage of dark pixels.
        bright_pct: Percentage of bright pixels.
        poor_thresh: Cutoff below which illumination is Poor.
        well_thresh: Cutoff at or above which illumination is Well Illuminated.

    Returns:
        str: 'Well Illuminated', 'Borderline Illumination', or 'Poor Illumination'.
    """
    # Force Poor if severe underexposure or overexposure clipping is present
    if dark_pct >= EXCESSIVE_DARK_PCT_CUTOFF or bright_pct >= EXCESSIVE_BRIGHT_PCT_CUTOFF:
        return "Poor Illumination"

    if overall_score >= well_thresh:
        return "Well Illuminated"
    elif overall_score >= poor_thresh:
        return "Borderline Illumination"
    else:
        return "Poor Illumination"


def assess_illumination(
    image_or_path: Union[str, Path, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (384, 384),
    poor_threshold: float = ENGINEERING_POOR_THRESHOLD,
    well_threshold: float = ENGINEERING_WELL_THRESHOLD,
) -> Dict[str, Any]:
    """Assess illumination, brightness, and exposure quality of a retinal fundus image.

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Optional resolution for standardization (default: (384, 384)).
        poor_threshold: Threshold below which image is Poor Illumination.
        well_threshold: Threshold at/above which image is Well Illuminated.

    Returns:
        dict: Complete structured illumination evaluation containing:
            - image_path: Path string or 'in_memory_array'
            - exposure_score: Float in [0.0, 100.0]
            - uniformity_score: Float in [0.0, 100.0]
            - overall_illumination_score: Composite score in [0.0, 100.0]
            - dark_pixel_pct: Percentage of dark pixels (< 30) within foreground
            - bright_pixel_pct: Percentage of saturated pixels (> 220) within foreground
            - mean_brightness: Mean foreground luminance
            - median_brightness: Median foreground luminance
            - regional_statistics: Quadrant means, quadrant imbalance, center-periphery ratio
            - decision: 'Well Illuminated', 'Borderline Illumination', or 'Poor Illumination'
            - diagnostics: Full foreground pixel counts, std, percentiles
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

    # 3. Segment foreground mask (exclude black background aperture)
    mask = compute_foreground_mask(eval_img_u8, tol=15)
    fg_pixels = int(np.sum(mask))
    total_pixels = int(mask.size)
    fg_fraction = float(fg_pixels / total_pixels) if total_pixels > 0 else 1.0

    # 4. Extract luminance
    lum = extract_luminance(eval_img_u8)

    # 5. Compute global brightness statistics
    stats = compute_brightness_statistics(lum, mask)

    # 6. Compute regional uniformity statistics
    regional = compute_regional_illumination(lum, mask)

    # 7. Compute exposure and uniformity scores
    e_score = compute_exposure_score(stats["mean"], stats["dark_pixel_pct"], stats["bright_pixel_pct"])
    u_score = compute_uniformity_score(stats["std"], stats["mean"], regional["quadrant_imbalance"])

    # 8. Overall illumination composite score (55% exposure adequacy + 45% spatial uniformity)
    overall_score = round(float(np.clip(0.55 * e_score + 0.45 * u_score, 0.0, 100.0)), 2)

    # 9. Final classification
    decision = classify_illumination(
        overall_score,
        stats["dark_pixel_pct"],
        stats["bright_pixel_pct"],
        poor_thresh=poor_threshold,
        well_thresh=well_threshold,
    )

    # 10. Exposure interpretation diagnosis
    if stats["mean"] < 75.0 or stats["dark_pixel_pct"] > 10.0:
        exposure_state = "Underexposed / Low Luminance"
    elif stats["mean"] > 160.0 or stats["bright_pixel_pct"] > 10.0:
        exposure_state = "Overexposed / High Luminance"
    else:
        exposure_state = "Acceptable Exposure"

    return {
        "image_path": image_path_str,
        "exposure_score": e_score,
        "uniformity_score": u_score,
        "overall_illumination_score": overall_score,
        "dark_pixel_pct": stats["dark_pixel_pct"],
        "bright_pixel_pct": stats["bright_pixel_pct"],
        "mean_brightness": stats["mean"],
        "median_brightness": stats["median"],
        "regional_statistics": regional,
        "decision": decision,
        "diagnostics": {
            "exposure_state": exposure_state,
            "std_brightness": stats["std"],
            "p5_brightness": stats["p5"],
            "p95_brightness": stats["p95"],
            "foreground_pixels": fg_pixels,
            "total_pixels": total_pixels,
            "foreground_fraction": round(fg_fraction, 4),
            "resolution_evaluated": [int(eval_img_u8.shape[1]), int(eval_img_u8.shape[0])],
        },
        "thresholds": {
            "poor_threshold": poor_threshold,
            "well_threshold": well_threshold,
            "optimal_mean_luminance": OPTIMAL_MEAN_LUMINANCE,
            "dark_cutoff": DARK_PIXEL_INTENSITY_CUTOFF,
            "bright_cutoff": BRIGHT_PIXEL_INTENSITY_CUTOFF,
            "status": "engineering_baseline_not_clinically_validated",
            "clinical_validation": False,
        },
    }
