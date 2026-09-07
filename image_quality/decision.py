"""Quality classification and screening decision module.

Categorizes retinal fundus images into:
- GOOD: Ready for immediate DR classifier inference.
- BORDERLINE: Suitable for automated enhancement prior to inference.
- UNGRADEABLE: Rejected with actionable recapture feedback.

Implements hard quality gates ensuring images with severe defects in any
critical dimension are never misclassified as GOOD simply due to high
scores in other dimensions.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List, Tuple
import numpy as np

from image_quality.scoring import score_image_quality, compute_composite_score


# Engineering quality gate thresholds (baseline heuristics, not clinically validated)
DEFAULT_UNGRADEABLE_THRESHOLDS: Dict[str, float] = {
    "focus_min": 15.0,        # Severe optical defocus / unusable blur
    "illumination_min": 35.0, # Severe under/over-exposure
    "fov_min": 40.0,          # Insufficient retinal field visible (<40% expected field)
    "centering_min": 30.0,     # Severe off-center / disk outside field
    "composite_min": 45.0,    # Aggregate failure across multiple dimensions
    "dark_clip_max": 50.0,    # Greater than 50% dark clipping inside retinal mask
    "glare_clip_max": 30.0,   # Greater than 30% glare clipping inside retinal mask
}

DEFAULT_BORDERLINE_THRESHOLDS: Dict[str, float] = {
    "focus_min": 50.0,        # Sub-optimal sharpness (soft focus or borderline)
    "illumination_min": 65.0, # Sub-optimal exposure or spatial uniformity
    "fov_min": 75.0,          # Marginal retinal coverage
    "centering_min": 70.0,    # Off-center retinal disc
    "composite_min": 70.0,    # Composite score threshold for GOOD status
}

# Standard recommended action strings
ACTION_PROCEED: str = "Proceed to DR classification."
ACTION_ENHANCE: str = "Enhancement recommended before DR classification."
ACTION_RECAPTURE: str = "Reject image and request recapture."


def evaluate_quality_gates(
    composite_result: Dict[str, Any],
    ungradeable_thresholds: Optional[Dict[str, float]] = None,
    borderline_thresholds: Optional[Dict[str, float]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Evaluate hard quality gates against composite assessment results.

    Args:
        composite_result: Dictionary output from compute_composite_score or score_image_quality.
        ungradeable_thresholds: Optional custom thresholds for UNGRADEABLE gates.
        borderline_thresholds: Optional custom thresholds for BORDERLINE gates.

    Returns:
        tuple: (ungradeable_gates, borderline_gates)
            Each element is a list of dictionaries detailing triggered gates:
            {"gate": str, "dimension": str, "value": float, "threshold": float, "reason": str}
    """
    u_thresh = ungradeable_thresholds if ungradeable_thresholds is not None else DEFAULT_UNGRADEABLE_THRESHOLDS
    b_thresh = borderline_thresholds if borderline_thresholds is not None else DEFAULT_BORDERLINE_THRESHOLDS

    component_scores = composite_result.get("component_scores", {})
    focus_score = float(component_scores.get("focus_score", 0.0))
    illum_score = float(component_scores.get("illumination_score", 0.0))
    fov_score = float(component_scores.get("fov_score", 0.0))
    centering_score = float(component_scores.get("centering_score", 0.0))
    composite_score = float(composite_result.get("composite_score", 0.0))

    # Optional deep diagnostics from assessments if present
    illum_assessment = composite_result.get("illumination_assessment", {})
    dark_clip = float(illum_assessment.get("dark_pixel_percentage", 0.0)) if isinstance(illum_assessment, dict) else 0.0
    glare_clip = float(illum_assessment.get("bright_pixel_percentage", 0.0)) if isinstance(illum_assessment, dict) else 0.0

    ungradeable_gates: List[Dict[str, Any]] = []
    borderline_gates: List[Dict[str, Any]] = []

    # --- UNGRADEABLE GATES (Critical optical/acquisition failures) ---
    if focus_score < u_thresh.get("focus_min", 15.0):
        ungradeable_gates.append({
            "gate": "severe_blur",
            "dimension": "focus",
            "value": round(focus_score, 2),
            "threshold": u_thresh.get("focus_min", 15.0),
            "reason": f"Severe blur detected (focus score {focus_score:.2f} < {u_thresh.get('focus_min', 15.0):.1f}).",
        })

    if illum_score < u_thresh.get("illumination_min", 35.0):
        ungradeable_gates.append({
            "gate": "severe_illumination_defect",
            "dimension": "illumination",
            "value": round(illum_score, 2),
            "threshold": u_thresh.get("illumination_min", 35.0),
            "reason": f"Severe illumination defect (illumination score {illum_score:.2f} < {u_thresh.get('illumination_min', 35.0):.1f}).",
        })

    if dark_clip > u_thresh.get("dark_clip_max", 50.0):
        ungradeable_gates.append({
            "gate": "severe_dark_clipping",
            "dimension": "illumination",
            "value": round(dark_clip, 2),
            "threshold": u_thresh.get("dark_clip_max", 50.0),
            "reason": f"Severe underexposure clipping ({dark_clip:.1f}% > {u_thresh.get('dark_clip_max', 50.0):.1f}%).",
        })

    if glare_clip > u_thresh.get("glare_clip_max", 30.0):
        ungradeable_gates.append({
            "gate": "severe_glare_clipping",
            "dimension": "illumination",
            "value": round(glare_clip, 2),
            "threshold": u_thresh.get("glare_clip_max", 30.0),
            "reason": f"Severe glare clipping ({glare_clip:.1f}% > {u_thresh.get('glare_clip_max', 30.0):.1f}%).",
        })

    if fov_score < u_thresh.get("fov_min", 40.0):
        ungradeable_gates.append({
            "gate": "severe_fov_truncation",
            "dimension": "fov",
            "value": round(fov_score, 2),
            "threshold": u_thresh.get("fov_min", 40.0),
            "reason": f"Severe field of view truncation (FOV score {fov_score:.2f} < {u_thresh.get('fov_min', 40.0):.1f}).",
        })

    if centering_score < u_thresh.get("centering_min", 30.0):
        ungradeable_gates.append({
            "gate": "severe_off_center",
            "dimension": "centering",
            "value": round(centering_score, 2),
            "threshold": u_thresh.get("centering_min", 30.0),
            "reason": f"Severe centering displacement (centering score {centering_score:.2f} < {u_thresh.get('centering_min', 30.0):.1f}).",
        })

    if composite_score < u_thresh.get("composite_min", 45.0):
        ungradeable_gates.append({
            "gate": "composite_unusable",
            "dimension": "composite",
            "value": round(composite_score, 2),
            "threshold": u_thresh.get("composite_min", 45.0),
            "reason": f"Aggregate quality below ungradeable floor ({composite_score:.2f} < {u_thresh.get('composite_min', 45.0):.1f}).",
        })

    # --- BORDERLINE GATES (Moderate defects suitable for enhancement) ---
    if focus_score < b_thresh.get("focus_min", 50.0):
        borderline_gates.append({
            "gate": "suboptimal_focus",
            "dimension": "focus",
            "value": round(focus_score, 2),
            "threshold": b_thresh.get("focus_min", 50.0),
            "reason": f"Sub-optimal focus (score {focus_score:.2f} < {b_thresh.get('focus_min', 50.0):.1f}).",
        })

    if illum_score < b_thresh.get("illumination_min", 65.0):
        borderline_gates.append({
            "gate": "suboptimal_illumination",
            "dimension": "illumination",
            "value": round(illum_score, 2),
            "threshold": b_thresh.get("illumination_min", 65.0),
            "reason": f"Sub-optimal illumination (score {illum_score:.2f} < {b_thresh.get('illumination_min', 65.0):.1f}).",
        })

    if fov_score < b_thresh.get("fov_min", 75.0):
        borderline_gates.append({
            "gate": "suboptimal_fov",
            "dimension": "fov",
            "value": round(fov_score, 2),
            "threshold": b_thresh.get("fov_min", 75.0),
            "reason": f"Sub-optimal field of view (score {fov_score:.2f} < {b_thresh.get('fov_min', 75.0):.1f}).",
        })

    if centering_score < b_thresh.get("centering_min", 70.0):
        borderline_gates.append({
            "gate": "suboptimal_centering",
            "dimension": "centering",
            "value": round(centering_score, 2),
            "threshold": b_thresh.get("centering_min", 70.0),
            "reason": f"Sub-optimal retinal centering (score {centering_score:.2f} < {b_thresh.get('centering_min', 70.0):.1f}).",
        })

    return ungradeable_gates, borderline_gates


def classify_quality_decision(
    composite_result: Dict[str, Any],
    ungradeable_thresholds: Optional[Dict[str, float]] = None,
    borderline_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Classify image quality into GOOD, BORDERLINE, or UNGRADEABLE.

    Args:
        composite_result: Output dict from compute_composite_score or score_image_quality.
        ungradeable_thresholds: Optional custom thresholds for UNGRADEABLE gates.
        borderline_thresholds: Optional custom thresholds for BORDERLINE gates.

    Returns:
        dict: Final decision structure containing:
            - final_class: 'GOOD', 'BORDERLINE', or 'UNGRADEABLE'
            - composite_score: float
            - component_scores: dict of component scores
            - triggered_quality_gates: list of all triggered gate objects
            - diagnostic_reasons: list of human-readable diagnostic strings
            - recommended_action: recommended workflow step
            - sub_decisions: per-dimension classifications
    """
    if not isinstance(composite_result, dict):
        raise TypeError(f"composite_result must be a dict, got {type(composite_result)}")

    if "composite_score" not in composite_result or "component_scores" not in composite_result:
        raise ValueError("composite_result missing 'composite_score' or 'component_scores' key")

    composite_score = float(composite_result["composite_score"])
    component_scores = composite_result["component_scores"]

    # Evaluate gates
    u_gates, b_gates = evaluate_quality_gates(
        composite_result,
        ungradeable_thresholds=ungradeable_thresholds,
        borderline_thresholds=borderline_thresholds,
    )

    b_thresh = borderline_thresholds if borderline_thresholds is not None else DEFAULT_BORDERLINE_THRESHOLDS
    composite_good_threshold = b_thresh.get("composite_min", 70.0)

    # Decision classification hierarchy:
    # 1. Hard UNGRADEABLE gates trigger UNGRADEABLE regardless of other scores
    # 2. Hard BORDERLINE gates trigger BORDERLINE regardless of composite average
    # 3. If composite score < 70.0, classify as BORDERLINE (if >= 45.0) or UNGRADEABLE (if < 45.0)
    # 4. If composite score >= 70.0 and no gates triggered, classify as GOOD

    diagnostic_reasons: List[str] = []
    triggered_gates: List[Dict[str, Any]] = []

    if u_gates:
        final_class = "UNGRADEABLE"
        recommended_action = ACTION_RECAPTURE
        triggered_gates = u_gates
        diagnostic_reasons = [g["reason"] for g in u_gates]
    elif b_gates or composite_score < composite_good_threshold:
        final_class = "BORDERLINE"
        recommended_action = ACTION_ENHANCE
        triggered_gates = b_gates.copy()
        diagnostic_reasons = [g["reason"] for g in b_gates]
        if composite_score < composite_good_threshold and not any(g["gate"] == "composite_borderline" for g in b_gates):
            reason_str = f"Composite quality score ({composite_score:.2f}) below standard threshold ({composite_good_threshold:.1f})."
            diagnostic_reasons.append(reason_str)
            triggered_gates.append({
                "gate": "composite_below_good",
                "dimension": "composite",
                "value": round(composite_score, 2),
                "threshold": composite_good_threshold,
                "reason": reason_str,
            })
    else:
        final_class = "GOOD"
        recommended_action = ACTION_PROCEED
        diagnostic_reasons = [
            f"All quality dimensions meet or exceed acceptance criteria (Composite score: {composite_score:.2f})."
        ]

    return {
        "final_class": final_class,
        "composite_score": composite_score,
        "component_scores": component_scores,
        "triggered_quality_gates": triggered_gates,
        "diagnostic_reasons": diagnostic_reasons,
        "recommended_action": recommended_action,
        "sub_decisions": composite_result.get("sub_decisions", {}),
        "weights": composite_result.get("weights", {}),
        "diagnostics": composite_result.get("diagnostics", {}),
    }


def classify_image_quality(
    image_or_path: Union[str, Path, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (384, 384),
    weights: Optional[Dict[str, float]] = None,
    ungradeable_thresholds: Optional[Dict[str, float]] = None,
    borderline_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """End-to-end IQA pipeline: load/inspect image, compute composite score, and classify decision.

    Args:
        image_or_path: File path or RGB NumPy array.
        target_size: Normalization resolution (default: (384, 384)).
        weights: Optional custom component weights.
        ungradeable_thresholds: Optional custom UNGRADEABLE gate thresholds.
        borderline_thresholds: Optional custom BORDERLINE gate thresholds.

    Returns:
        dict: Full assessment and final screening decision dictionary.
    """
    # 1. Run all sub-module assessments and composite scoring
    composite_res = score_image_quality(
        image_or_path=image_or_path,
        target_size=target_size,
        weights=weights,
    )

    # 2. Apply quality gates and final decision classification
    decision_res = classify_quality_decision(
        composite_result=composite_res,
        ungradeable_thresholds=ungradeable_thresholds,
        borderline_thresholds=borderline_thresholds,
    )

    # 3. Merge full assessment context for complete traceability
    decision_res["image_path"] = composite_res.get("image_path", "")
    decision_res["focus_assessment"] = composite_res.get("focus_assessment", {})
    decision_res["illumination_assessment"] = composite_res.get("illumination_assessment", {})
    decision_res["fov_assessment"] = composite_res.get("fov_assessment", {})

    return decision_res
