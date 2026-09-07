"""Focus and blur assessment module for retinal fundus images.

Provides deterministic sharpness measurements using:
1. Masked Variance of Laplacian (VoL) on the retinal foreground (Green channel).
2. Masked Tenengrad gradient energy (Sobel gradient magnitude).
3. Log-logistic normalization to a calibrated 0-100 scale.
4. Categorization into Sharp, Borderline, or Blurry based on engineering baselines.

NOTE: Baseline thresholds are initial heuristic engineering baselines derived from observed
retinal fundus distributions in this project, pending formal clinical ophthalmology validation.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from image_quality.io import load_raw_image, preprocess_image

# Engineering baseline thresholds (unvalidated clinically)
ENGINEERING_BLURRY_THRESHOLD = 25.0    # Normalized score below which image is flagged Blurry
ENGINEERING_SHARP_THRESHOLD = 50.0     # Normalized score at/above which image is flagged Sharp
DEFAULT_LOG_MIDPOINT = 100.0           # Midpoint parameter for log-logistic normalization (LapVar ~ 100)
DEFAULT_LOG_SLOPE = 2.0                # Logistic slope parameter


def extract_analysis_channel(image: np.ndarray, channel: str = "green") -> np.ndarray:
    """Extract single-channel intensity array for focus analysis.

    The Green channel is preferred for retinal imaging because hemoglobin absorption
    provides maximum contrast for blood vessels and retinal nerve fiber layers.

    Args:
        image: RGB image array of shape (H, W, 3).
        channel: One of 'green', 'gray', 'red', 'blue'.

    Returns:
        np.ndarray: 2D float64 array.
    """
    if image.ndim == 2:
        return image.astype(np.float64)

    ch = channel.lower()
    if ch == "green":
        return image[:, :, 1].astype(np.float64)
    elif ch == "red":
        return image[:, :, 0].astype(np.float64)
    elif ch == "blue":
        return image[:, :, 2].astype(np.float64)
    elif ch in ("gray", "grayscale"):
        if cv2 is not None:
            gray = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
            return gray.astype(np.float64)
        return np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.float64)
    else:
        raise ValueError(f"Unsupported channel '{channel}'. Choose from 'green', 'gray', 'red', 'blue'.")


def compute_foreground_mask(image: np.ndarray, tol: int = 15) -> np.ndarray:
    """Segment retinal foreground from outer unilluminated black camera border.

    Prevents the sharp artificial step edge at the boundary of the camera aperture
    from falsely inflating Laplacian variance.

    Args:
        image: RGB image array.
        tol: Threshold intensity above which pixels belong to the retina.

    Returns:
        np.ndarray: 2D boolean mask where True indicates retinal foreground.
    """
    if image.ndim == 3:
        if cv2 is not None:
            gray = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        else:
            gray = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
    else:
        gray = image.astype(np.uint8)

    mask = gray > tol
    if not np.any(mask):
        # Fallback to full field if image is entirely dark
        return np.ones_like(gray, dtype=bool)

    return mask


def compute_laplacian_map(channel_2d: np.ndarray) -> np.ndarray:
    """Calculate the 2D Laplacian operator response across the image.

    Args:
        channel_2d: 2D float64 channel array.

    Returns:
        np.ndarray: 2D float64 Laplacian response.
    """
    arr = channel_2d.astype(np.float64)
    if cv2 is not None:
        return cv2.Laplacian(arr, cv2.CV_64F)

    # Scipy / pure convolution fallback
    from scipy.ndimage import laplace
    return laplace(arr)


def compute_sobel_gradients(channel_2d: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate horizontal and vertical Sobel gradient components.

    Args:
        channel_2d: 2D float64 channel array.

    Returns:
        tuple[np.ndarray, np.ndarray]: (Gx, Gy) gradient components.
    """
    arr = channel_2d.astype(np.float64)
    if cv2 is not None:
        gx = cv2.Sobel(arr, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(arr, cv2.CV_64F, 0, 1, ksize=3)
        return gx, gy

    from scipy.ndimage import sobel
    gx = sobel(arr, axis=1)
    gy = sobel(arr, axis=0)
    return gx, gy


def normalize_focus_score(
    raw_metric: float,
    midpoint: float = DEFAULT_LOG_MIDPOINT,
    slope: float = DEFAULT_LOG_SLOPE,
) -> float:
    """Normalize raw Laplacian variance into a continuous [0.0, 100.0] score.

    Applies a monotonic log-logistic transformation:
        score = 100 / (1 + exp(-slope * (log10(val) - log10(midpoint))))

    Args:
        raw_metric: Positive variance value.
        midpoint: Metric value mapping to exactly 50.0.
        slope: Steepness parameter controlling compression.

    Returns:
        float: Normalized score bounded in [0.0, 100.0].
    """
    val = float(raw_metric)
    if val <= 0.0 or not np.isfinite(val):
        return 0.0

    log_val = np.log10(val)
    log_mid = np.log10(midpoint)
    z = slope * (log_val - log_mid)
    # Clip z to prevent numerical overflow in exp
    z_clipped = np.clip(z, -60.0, 60.0)
    score = 100.0 / (1.0 + np.exp(-z_clipped))
    return round(float(score), 2)


def classify_focus(
    normalized_score: float,
    blurry_threshold: float = ENGINEERING_BLURRY_THRESHOLD,
    sharp_threshold: float = ENGINEERING_SHARP_THRESHOLD,
) -> str:
    """Classify focus quality into discrete diagnostic tiers.

    Args:
        normalized_score: Normalized focus score in [0.0, 100.0].
        blurry_threshold: Threshold below which image is classified 'Blurry'.
        sharp_threshold: Threshold at or above which image is classified 'Sharp'.

    Returns:
        str: 'Sharp', 'Borderline', or 'Blurry'.
    """
    if normalized_score >= sharp_threshold:
        return "Sharp"
    elif normalized_score >= blurry_threshold:
        return "Borderline"
    else:
        return "Blurry"


def assess_focus(
    image_or_path: Union[str, Path, np.ndarray],
    channel: str = "green",
    target_size: Optional[Tuple[int, int]] = (384, 384),
    blurry_threshold: float = ENGINEERING_BLURRY_THRESHOLD,
    sharp_threshold: float = ENGINEERING_SHARP_THRESHOLD,
) -> Dict[str, Any]:
    """Evaluate retinal fundus image sharpness and focus quality.

    Args:
        image_or_path: File path or RGB NumPy array.
        channel: Color channel for edge detection (default: 'green').
        target_size: Optional resolution to standardize to (default: (384, 384) matching classifier).
        blurry_threshold: Engineering threshold for 'Blurry' classification.
        sharp_threshold: Engineering threshold for 'Sharp' classification.

    Returns:
        dict: Structured assessment containing:
            - image_path: Path string or 'in_memory_array'
            - raw_metric: Raw Laplacian variance on foreground
            - tenengrad_energy: Mean squared Sobel gradient on foreground
            - normalized_score: Focus score scaled to [0.0, 100.0]
            - decision: 'Sharp', 'Borderline', or 'Blurry'
            - diagnostics: Detailed sub-measurements and spatial parameters
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

    # 2. Preprocess / Standardize resolution if requested
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

    # 4. Extract analysis channel
    analysis_channel = extract_analysis_channel(eval_img_u8, channel=channel)

    # 5. Compute Laplacian Variance
    lap_map = compute_laplacian_map(analysis_channel)
    if fg_pixels > 0:
        raw_lap_var = float(np.var(lap_map[mask]))
    else:
        raw_lap_var = float(np.var(lap_map))

    # 6. Compute Tenengrad Gradient Energy (Complementary 1st-derivative metric)
    gx, gy = compute_sobel_gradients(analysis_channel)
    grad_sq = gx**2 + gy**2
    if fg_pixels > 0:
        tenengrad_energy = float(np.mean(grad_sq[mask]))
    else:
        tenengrad_energy = float(np.mean(grad_sq))

    # 7. Normalize score and classify
    norm_score = normalize_focus_score(raw_lap_var, midpoint=DEFAULT_LOG_MIDPOINT, slope=DEFAULT_LOG_SLOPE)
    decision = classify_focus(norm_score, blurry_threshold=blurry_threshold, sharp_threshold=sharp_threshold)

    return {
        "image_path": image_path_str,
        "raw_metric": round(raw_lap_var, 4),
        "tenengrad_energy": round(tenengrad_energy, 4),
        "normalized_score": norm_score,
        "decision": decision,
        "diagnostics": {
            "channel_used": channel,
            "resolution_evaluated": [int(eval_img_u8.shape[1]), int(eval_img_u8.shape[0])],
            "foreground_pixels": fg_pixels,
            "total_pixels": total_pixels,
            "foreground_fraction": round(fg_fraction, 4),
            "laplacian_min": round(float(np.min(lap_map)), 2),
            "laplacian_max": round(float(np.max(lap_map)), 2),
            "tenengrad_mean": round(tenengrad_energy, 2),
        },
        "thresholds": {
            "blurry_threshold": blurry_threshold,
            "sharp_threshold": sharp_threshold,
            "log_midpoint": DEFAULT_LOG_MIDPOINT,
            "log_slope": DEFAULT_LOG_SLOPE,
            "status": "engineering_baseline_not_clinically_validated",
            "clinical_validation": False,
        },
    }
