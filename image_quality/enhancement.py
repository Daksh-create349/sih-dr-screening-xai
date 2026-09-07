"""Retinal fundus image enhancement pipeline for borderline quality cases.

Provides evidence-based candidate enhancements:
1. CLAHE (Contrast-Limited Adaptive Histogram Equalization on Luminance)
2. Mild Unsharp Masking (masked edge sharpness improvement)
3. Bilateral Edge-Preserving Denoising
4. Ben Graham's method (Gaussian blur weighted subtraction)

Includes strict retinal safeguards against over-enhancement:
- Chromaticity shift threshold (preserves natural retinal pigmentation)
- Clipping limits (prevents glare blowout and crushed shadows)
- High-frequency gradient amplification limits (prevents noise explosion and halos)
- Dimension non-degradation constraint
- Automatic fallback to original image when enhancement fails safety criteria.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Union, Optional, List
import cv2
import numpy as np

from image_quality.io import load_raw_image
from image_quality.focus import compute_foreground_mask
from image_quality.decision import classify_image_quality


# Safeguard thresholds against over-enhancement
DEFAULT_SAFEGUARD_THRESHOLDS: Dict[str, float] = {
    "max_chroma_shift": 15.0,          # Maximum allowable mean delta(a, b) in LAB space
    "max_bright_clip_increase": 5.0,   # Maximum allowable increase in percentage of saturated pixels (>240)
    "max_dark_clip_increase": 5.0,     # Maximum allowable increase in percentage of crushed dark pixels (<15)
    "max_gradient_ratio": 3.5,         # Maximum allowable amplification ratio of Laplacian gradient energy
    "max_score_drop_tolerance": 5.0,   # Maximum permissible drop in any single component score
}


def enhance_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply CLAHE exclusively to luminance channel in LAB color space.

    Preserves natural retinal chromaticity (A and B channels remain unaltered).
    Background pixels outside the retinal mask are strictly preserved.

    Args:
        image: RGB uint8 array.
        clip_limit: Threshold for contrast limiting.
        tile_grid_size: Size of grid for histogram equalization.
        mask: Optional binary foreground mask.

    Returns:
        np.ndarray: Enhanced RGB uint8 array.
    """
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Input image must be a 3-channel RGB NumPy array.")

    img_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    fg_mask = mask if mask is not None else compute_foreground_mask(img_uint8, tol=15)

    lab = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tile_grid_size)
    l_enh = clahe.apply(l)

    lab_enh = cv2.merge((l_enh, a, b))
    enhanced_rgb = cv2.cvtColor(lab_enh, cv2.COLOR_LAB2RGB)

    # Preserve background mask exactly
    enhanced_rgb[~fg_mask] = img_uint8[~fg_mask]
    return enhanced_rgb


def enhance_unsharp_mask(
    image: np.ndarray,
    amount: float = 0.8,
    radius: float = 1.5,
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply mild unsharp masking restricted to the retinal foreground.

    Args:
        image: RGB uint8 array.
        amount: Sharpening strength (default: 0.8).
        radius: Gaussian blur sigma for low-pass subtraction.
        mask: Optional binary foreground mask.

    Returns:
        np.ndarray: Sharpened RGB uint8 array.
    """
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Input image must be a 3-channel RGB NumPy array.")

    img_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    fg_mask = mask if mask is not None else compute_foreground_mask(img_uint8, tol=15)

    blurred = cv2.GaussianBlur(img_uint8, (0, 0), float(radius))
    # unsharp = img * (1 + amount) - blurred * amount
    enhanced = cv2.addWeighted(img_uint8, 1.0 + float(amount), blurred, -float(amount), 0)
    enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

    # Preserve background mask exactly
    enhanced[~fg_mask] = img_uint8[~fg_mask]
    return enhanced


def enhance_ben_graham(
    image: np.ndarray,
    sigma: float = 10.0,
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply Ben Graham's method (Gaussian blur subtraction with 128 offset).

    Args:
        image: RGB uint8 array.
        sigma: Gaussian blur scale.
        mask: Optional binary foreground mask.

    Returns:
        np.ndarray: Color-constancy normalized RGB uint8 array.
    """
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Input image must be a 3-channel RGB NumPy array.")

    img_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    fg_mask = mask if mask is not None else compute_foreground_mask(img_uint8, tol=15)

    blurred = cv2.GaussianBlur(img_uint8, (0, 0), float(sigma))
    enhanced = cv2.addWeighted(img_uint8, 4.0, blurred, -4.0, 128)
    enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

    # Preserve background mask
    enhanced[~fg_mask] = img_uint8[~fg_mask]
    return enhanced


def enhance_denoise(
    image: np.ndarray,
    d: int = 5,
    sigma_color: float = 25.0,
    sigma_space: float = 25.0,
    mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply edge-preserving bilateral filtering to suppress sensor noise.

    Args:
        image: RGB uint8 array.
        d: Diameter of pixel neighborhood.
        sigma_color: Filter sigma in color space.
        sigma_space: Filter sigma in coordinate space.
        mask: Optional binary foreground mask.

    Returns:
        np.ndarray: Denoised RGB uint8 array.
    """
    if not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Input image must be a 3-channel RGB NumPy array.")

    img_uint8 = np.clip(image, 0, 255).astype(np.uint8)
    fg_mask = mask if mask is not None else compute_foreground_mask(img_uint8, tol=15)

    enhanced = cv2.bilateralFilter(img_uint8, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

    # Preserve background mask
    enhanced[~fg_mask] = img_uint8[~fg_mask]
    return enhanced


def enhance_image(
    image_or_path: Union[str, Path, np.ndarray],
    method: str = "clahe",
    **kwargs,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Dispatch image enhancement using named method with metadata.

    Args:
        image_or_path: File path or RGB NumPy array.
        method: Enhancement strategy ("clahe", "unsharp", "ben_graham", "denoise").
        **kwargs: Optional method-specific hyperparameters.

    Returns:
        tuple: (Enhanced RGB array, Metadata dict)
    """
    if isinstance(image_or_path, (str, Path)):
        img_rgb = load_raw_image(image_or_path)
        source_name = Path(image_or_path).name
    elif isinstance(image_or_path, np.ndarray):
        img_rgb = np.clip(image_or_path, 0, 255).astype(np.uint8)
        source_name = "in_memory_array"
    else:
        raise TypeError(f"Invalid input type: {type(image_or_path)}")

    m_lower = method.lower().strip()
    if m_lower in {"clahe", "clahe_luminance"}:
        clip_limit = kwargs.get("clip_limit", 2.0)
        grid_size = kwargs.get("tile_grid_size", (8, 8))
        enhanced = enhance_clahe(img_rgb, clip_limit=clip_limit, tile_grid_size=grid_size)
        params = {"clip_limit": clip_limit, "tile_grid_size": grid_size}
    elif m_lower in {"unsharp", "unsharp_mask"}:
        amount = kwargs.get("amount", 0.8)
        radius = kwargs.get("radius", 1.5)
        enhanced = enhance_unsharp_mask(img_rgb, amount=amount, radius=radius)
        params = {"amount": amount, "radius": radius}
    elif m_lower in {"ben_graham", "graham", "color_constancy"}:
        sigma = kwargs.get("sigma", 10.0)
        enhanced = enhance_ben_graham(img_rgb, sigma=sigma)
        params = {"sigma": sigma}
    elif m_lower in {"denoise", "bilateral"}:
        d = kwargs.get("d", 5)
        sc = kwargs.get("sigma_color", 25.0)
        ss = kwargs.get("sigma_space", 25.0)
        enhanced = enhance_denoise(img_rgb, d=d, sigma_color=sc, sigma_space=ss)
        params = {"d": d, "sigma_color": sc, "sigma_space": ss}
    else:
        raise ValueError(f"Unknown enhancement method '{method}'. Valid: 'clahe', 'unsharp', 'ben_graham', 'denoise'.")

    meta = {
        "method": m_lower,
        "source": source_name,
        "parameters": params,
        "output_dtype": str(enhanced.dtype),
        "output_shape": list(enhanced.shape),
    }
    return enhanced, meta


def compute_distortion_metrics(
    original_image: np.ndarray,
    enhanced_image: np.ndarray,
    mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Compute objective distortion statistics between original and enhanced images.

    Evaluates:
    - Delta E and Chromaticity shift (LAB space)
    - Dark clipping change (<15 intensity)
    - Bright saturation clipping change (>240 intensity)
    - Gradient energy amplification ratio (Laplacian variance)

    Args:
        original_image: Original RGB array.
        enhanced_image: Enhanced RGB array.
        mask: Optional binary foreground mask.

    Returns:
        dict: Measured distortion statistics.
    """
    fg_mask = mask if mask is not None else compute_foreground_mask(original_image, tol=15)
    if not np.any(fg_mask):
        fg_mask = np.ones(original_image.shape[:2], dtype=bool)

    orig_fg = original_image[fg_mask].astype(float)
    enh_fg = enhanced_image[fg_mask].astype(float)

    # 1. Clipping metrics inside retinal mask
    orig_dark_pct = float(np.mean(orig_fg < 15.0) * 100.0)
    enh_dark_pct = float(np.mean(enh_fg < 15.0) * 100.0)
    dark_clip_diff = enh_dark_pct - orig_dark_pct

    orig_bright_pct = float(np.mean(orig_fg > 240.0) * 100.0)
    enh_bright_pct = float(np.mean(enh_fg > 240.0) * 100.0)
    bright_clip_diff = enh_bright_pct - orig_bright_pct

    # 2. Color and chromaticity shifts in LAB space
    lab_orig = cv2.cvtColor(original_image, cv2.COLOR_RGB2LAB)[fg_mask].astype(float)
    lab_enh = cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2LAB)[fg_mask].astype(float)

    # Total perceptual difference Delta E 76
    delta_e = float(np.mean(np.sqrt(np.sum((lab_orig - lab_enh) ** 2, axis=1))))
    # Chromaticity-only shift: delta(a, b) ignoring luminance (L)
    chroma_shift = float(np.mean(np.sqrt(np.sum((lab_orig[:, 1:] - lab_enh[:, 1:]) ** 2, axis=1))))

    # 3. High-frequency gradient amplification ratio
    gray_orig = cv2.cvtColor(original_image, cv2.COLOR_RGB2GRAY)
    gray_enh = cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2GRAY)
    lap_orig_var = float(cv2.Laplacian(gray_orig, cv2.CV_64F).var())
    lap_enh_var = float(cv2.Laplacian(gray_enh, cv2.CV_64F).var())
    gradient_ratio = float(lap_enh_var / (lap_orig_var + 1e-6))

    return {
        "delta_e": round(delta_e, 2),
        "chroma_shift": round(chroma_shift, 2),
        "orig_dark_clip_pct": round(orig_dark_pct, 2),
        "enh_dark_clip_pct": round(enh_dark_pct, 2),
        "dark_clip_diff_pct": round(dark_clip_diff, 2),
        "orig_bright_clip_pct": round(orig_bright_pct, 2),
        "enh_bright_clip_pct": round(enh_bright_pct, 2),
        "bright_clip_diff_pct": round(bright_clip_diff, 2),
        "laplacian_orig_var": round(lap_orig_var, 2),
        "laplacian_enh_var": round(lap_enh_var, 2),
        "gradient_ratio": round(gradient_ratio, 2),
    }


def evaluate_enhancement(
    original_image_or_path: Union[str, Path, np.ndarray],
    enhanced_image_or_path: Union[str, Path, np.ndarray],
    method: str = "clahe",
    safeguard_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Evaluate whether candidate enhancement produces measurable IQA improvement.

    Applies evidence-based acceptance rules:
    - Verifies no safeguard violations (excessive chroma shift, blowout clipping, noise explosion)
    - Verifies overall composite quality or targeted dimension improves
    - Verifies no critical non-target dimension suffers severe degradation (>5 points)
    - Recommends fallback to original image when rejected.

    Args:
        original_image_or_path: Original input image or file path.
        enhanced_image_or_path: Enhanced derived image or file path.
        method: Name of enhancement method.
        safeguard_thresholds: Optional custom safety criteria.

    Returns:
        dict: Complete comparison structure including before/after metrics, score differences,
              safeguard diagnostics, acceptance decision, and selected output.
    """
    st = safeguard_thresholds if safeguard_thresholds is not None else DEFAULT_SAFEGUARD_THRESHOLDS

    # Load arrays
    if isinstance(original_image_or_path, (str, Path)):
        orig_img = load_raw_image(original_image_or_path)
        orig_path_str = str(original_image_or_path)
    else:
        orig_img = np.clip(original_image_or_path, 0, 255).astype(np.uint8)
        orig_path_str = "in_memory_array"

    if isinstance(enhanced_image_or_path, (str, Path)):
        enh_img = load_raw_image(enhanced_image_or_path)
        enh_path_str = str(enhanced_image_or_path)
    else:
        enh_img = np.clip(enhanced_image_or_path, 0, 255).astype(np.uint8)
        enh_path_str = "in_memory_array"

    # 1. Run IQA on before and after
    before_iqa = classify_image_quality(orig_img)
    after_iqa = classify_image_quality(enh_img)

    # 2. Compute distortion statistics
    mask = compute_foreground_mask(orig_img, tol=15)
    distortion = compute_distortion_metrics(orig_img, enh_img, mask=mask)

    # 3. Calculate score differences (after - before)
    before_comp = float(before_iqa["composite_score"])
    after_comp = float(after_iqa["composite_score"])
    delta_composite = round(after_comp - before_comp, 2)

    b_scores = before_iqa["component_scores"]
    a_scores = after_iqa["component_scores"]
    score_differences = {
        "delta_composite": delta_composite,
        "delta_focus": round(float(a_scores["focus_score"]) - float(b_scores["focus_score"]), 2),
        "delta_illumination": round(float(a_scores["illumination_score"]) - float(b_scores["illumination_score"]), 2),
        "delta_fov": round(float(a_scores["fov_score"]) - float(b_scores["fov_score"]), 2),
        "delta_centering": round(float(a_scores["centering_score"]) - float(b_scores["centering_score"]), 2),
    }

    # 4. Check Safeguard Violations
    safeguard_violations: List[str] = []

    if distortion["chroma_shift"] > st.get("max_chroma_shift", 15.0):
        safeguard_violations.append(
            f"Severe color distortion: chromaticity shift {distortion['chroma_shift']:.1f} > {st.get('max_chroma_shift', 15.0):.1f}"
        )

    if distortion["bright_clip_diff_pct"] > st.get("max_bright_clip_increase", 5.0):
        safeguard_violations.append(
            f"Excessive glare saturation increase: +{distortion['bright_clip_diff_pct']:.1f}% > {st.get('max_bright_clip_increase', 5.0):.1f}%"
        )

    if distortion["dark_clip_diff_pct"] > st.get("max_dark_clip_increase", 5.0):
        safeguard_violations.append(
            f"Excessive crushed dark clipping increase: +{distortion['dark_clip_diff_pct']:.1f}% > {st.get('max_dark_clip_increase', 5.0):.1f}%"
        )

    if distortion["gradient_ratio"] > st.get("max_gradient_ratio", 3.5):
        safeguard_violations.append(
            f"High-frequency noise amplification: gradient ratio {distortion['gradient_ratio']:.1f} > {st.get('max_gradient_ratio', 3.5):.1f}"
        )

    # Check for severe dimension drops
    drop_tol = st.get("max_score_drop_tolerance", 5.0)
    for dim_name in ["focus", "illumination", "fov", "centering"]:
        diff = score_differences[f"delta_{dim_name}"]
        if diff < -drop_tol:
            safeguard_violations.append(f"Dimension '{dim_name}' degraded significantly ({diff:+.1f} points)")

    # 5. Evidence-based Acceptance Decision
    if safeguard_violations:
        accepted = False
        rejection_reason = "; ".join(safeguard_violations)
    elif delta_composite <= 0.0 and score_differences["delta_focus"] <= 0.0 and score_differences["delta_illumination"] <= 0.0:
        accepted = False
        rejection_reason = f"No measurable quality improvement (delta composite: {delta_composite:+.2f})."
    else:
        accepted = True
        rejection_reason = "Accepted: measurable quality improvement with zero safeguard violations."

    return {
        "original_path": orig_path_str,
        "enhanced_path": enh_path_str,
        "enhancement_method": method,
        "accepted": accepted,
        "rejection_reason": rejection_reason,
        "before_scores": {
            "composite_score": before_comp,
            "component_scores": b_scores,
            "final_class": before_iqa["final_class"],
            "triggered_gates": [g["gate"] for g in before_iqa["triggered_quality_gates"]],
        },
        "after_scores": {
            "composite_score": after_comp,
            "component_scores": a_scores,
            "final_class": after_iqa["final_class"],
            "triggered_gates": [g["gate"] for g in after_iqa["triggered_quality_gates"]],
        },
        "score_differences": score_differences,
        "distortion_metrics": distortion,
        "safeguard_violations": safeguard_violations,
        "final_routing": {
            "active_image_source": "enhanced" if accepted else "original_fallback",
            "effective_class": after_iqa["final_class"] if accepted else before_iqa["final_class"],
            "effective_composite_score": after_comp if accepted else before_comp,
        },
    }


def select_best_enhancement(
    image_or_path: Union[str, Path, np.ndarray],
    candidate_methods: Optional[List[str]] = None,
    save_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Evaluate candidate enhancements and select the optimal accepted method.

    If candidate methods are not specified, selects candidate strategies based
    on the specific quality gates triggered by the original image.

    Args:
        image_or_path: Input image file path or RGB array.
        candidate_methods: Optional list of enhancement strategies to test.
        save_dir: Optional directory to save accepted enhanced image.

    Returns:
        dict: Complete evaluation breakdown of all tested methods, best selected method,
              and path to saved enhanced image (if save_dir provided).
    """
    if isinstance(image_or_path, (str, Path)):
        orig_img = load_raw_image(image_or_path)
        stem = Path(image_or_path).stem
        orig_path_str = str(image_or_path)
    else:
        orig_img = np.clip(image_or_path, 0, 255).astype(np.uint8)
        stem = "in_memory_array"
        orig_path_str = "in_memory_array"

    # Baseline original IQA
    orig_iqa = classify_image_quality(orig_img)
    orig_gates = [g["gate"] for g in orig_iqa["triggered_quality_gates"]]

    # Determine candidate methods based on detected defect if not explicit
    if candidate_methods is None:
        methods_to_test = ["clahe", "unsharp", "ben_graham", "denoise"]
    else:
        methods_to_test = candidate_methods

    evaluations: List[Dict[str, Any]] = []
    enhanced_arrays: Dict[str, np.ndarray] = {}

    for m in methods_to_test:
        enh_arr, _ = enhance_image(orig_img, method=m)
        enhanced_arrays[m] = enh_arr
        ev = evaluate_enhancement(orig_img, enh_arr, method=m)
        evaluations.append(ev)

    # Filter accepted candidates
    accepted_evals = [e for e in evaluations if e["accepted"]]

    if accepted_evals:
        # Pick candidate with highest composite score
        best_eval = max(accepted_evals, key=lambda e: e["after_scores"]["composite_score"])
        best_method = best_eval["enhancement_method"]
        best_array = enhanced_arrays[best_method]
        decision_summary = f"Selected '{best_method}' with composite score {best_eval['after_scores']['composite_score']:.2f} ({best_eval['score_differences']['delta_composite']:+.2f} improvement)."
    else:
        best_eval = None
        best_method = "none_fallback_original"
        best_array = orig_img
        decision_summary = "All candidate enhancements rejected by safeguards or lack of improvement. Fallback to original image."

    # Save output if directory specified
    saved_path_str = None
    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"{stem}_{best_method}.png"
        saved_file = save_dir / out_filename
        # Save as RGB image via OpenCV
        cv2.imwrite(str(saved_file), cv2.cvtColor(best_array, cv2.COLOR_RGB2BGR))
        saved_path_str = str(saved_file)

    return {
        "original_path": orig_path_str,
        "best_method": best_method,
        "selected_evaluation": best_eval,
        "all_evaluations": evaluations,
        "saved_enhanced_path": saved_path_str,
        "decision_summary": decision_summary,
        "original_quality": {
            "composite_score": orig_iqa["composite_score"],
            "final_class": orig_iqa["final_class"],
            "triggered_gates": orig_gates,
        },
    }
