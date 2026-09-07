"""Composite image-quality scoring module for retinal fundus screening.

Aggregates independent dimensional measurements:
1. Focus / sharpness (weight: 0.40)
2. Illumination & exposure (weight: 0.30)
3. Field of View coverage (weight: 0.20)
4. Retinal field centering (weight: 0.10)

NOTE: Optic disc candidate confidence is tracked in diagnostics for anatomical context,
but excluded from the primary optical acquisition score to avoid penalizing valid
macula-centered fundus photography.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, Tuple
import numpy as np

from image_quality.focus import assess_focus
from image_quality.illumination import assess_illumination
from image_quality.field_of_view import assess_field_of_view

# Standard clinical engineering weights (sum to 1.0)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "focus": 0.40,
    "illumination": 0.30,
    "fov": 0.20,
    "centering": 0.10,
}


def compute_composite_score(
    focus_metrics: Dict[str, Any],
    illumination_metrics: Dict[str, Any],
    fov_metrics: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate weighted composite quality score from sub-module evaluations.

    Args:
        focus_metrics: Output dict from assess_focus().
        illumination_metrics: Output dict from assess_illumination().
        fov_metrics: Output dict from assess_field_of_view().
        weights: Optional dictionary of weights for 'focus', 'illumination', 'fov', 'centering'.

    Returns:
        dict: Composite score, component breakdown, normalized weights, and supporting diagnostics.

    Raises:
        ValueError: If weights do not sum to 1.0 or contains invalid keys.
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS.copy()

    required_keys = {"focus", "illumination", "fov", "centering"}
    if not required_keys.issubset(w.keys()):
        missing = required_keys - set(w.keys())
        raise ValueError(f"Missing required weight keys: {missing}")

    weight_sum = sum(w[k] for k in required_keys)
    if abs(weight_sum - 1.0) > 1e-4:
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum:.4f}")

    # Extract component scores [0.0, 100.0]
    focus_score = float(focus_metrics.get("normalized_score", 0.0))
    illum_score = float(illumination_metrics.get("overall_illumination_score", 0.0))
    fov_score = float(fov_metrics.get("fov_score", 0.0))
    centering_score = float(fov_metrics.get("centering_score", 0.0))

    # Validate finite bounds
    for name, s in [
        ("focus", focus_score),
        ("illumination", illum_score),
        ("fov", fov_score),
        ("centering", centering_score),
    ]:
        if not (0.0 <= s <= 100.0) or not np.isfinite(s):
            raise ValueError(f"Component score '{name}' must be finite and within [0, 100], got {s}")

    composite = (
        w["focus"] * focus_score
        + w["illumination"] * illum_score
        + w["fov"] * fov_score
        + w["centering"] * centering_score
    )
    composite_score = round(float(np.clip(composite, 0.0, 100.0)), 2)

    component_scores = {
        "focus_score": round(focus_score, 2),
        "illumination_score": round(illum_score, 2),
        "fov_score": round(fov_score, 2),
        "centering_score": round(centering_score, 2),
    }

    # Anatomical context (tracked, not penalized in primary score)
    optic_disc_info = fov_metrics.get("optic_disc", {})
    disc_conf = optic_disc_info.get("confidence", 0.0) if isinstance(optic_disc_info, dict) else 0.0

    return {
        "composite_score": composite_score,
        "component_scores": component_scores,
        "weights": {k: round(w[k], 4) for k in required_keys},
        "sub_decisions": {
            "focus_decision": focus_metrics.get("decision", "Unknown"),
            "illumination_decision": illumination_metrics.get("decision", "Unknown"),
            "fov_decision": fov_metrics.get("fov_decision", "Unknown"),
            "centering_decision": fov_metrics.get("centering_decision", "Unknown"),
        },
        "diagnostics": {
            "focus_raw_metric": focus_metrics.get("raw_metric"),
            "illumination_mean_brightness": illumination_metrics.get("mean_brightness"),
            "retinal_coverage_pct": fov_metrics.get("coverage_pct"),
            "radial_center_offset": fov_metrics.get("radial_center_offset"),
            "optic_disc_confidence": disc_conf,
            "optic_disc_detected": optic_disc_info.get("detected", False) if isinstance(optic_disc_info, dict) else False,
        },
    }


def score_image_quality(
    image_or_path: Union[str, Path, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (384, 384),
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Evaluate all sub-modules and compute composite quality score.

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Standardization size (default: (384, 384)).
        weights: Optional custom component weights.

    Returns:
        dict: Full assessment results with composite score and sub-module outputs.
    """
    image_path_str = str(image_or_path) if isinstance(image_or_path, (str, Path)) else "in_memory_array"

    # Run independent assessments
    focus_res = assess_focus(image_or_path, target_size=target_size)
    illum_res = assess_illumination(image_or_path, target_size=target_size)
    fov_res = assess_field_of_view(image_or_path, target_size=target_size)

    # Compute composite score
    scoring_res = compute_composite_score(focus_res, illum_res, fov_res, weights=weights)

    scoring_res["image_path"] = image_path_str
    scoring_res["focus_assessment"] = focus_res
    scoring_res["illumination_assessment"] = illum_res
    scoring_res["fov_assessment"] = fov_res

    return scoring_res
