"""Operator reporting and recapture feedback generation module.

Translates technical quality measurements, quality gate triggers, and enhancement
outcomes into clear, structured, and actionable operator-facing clinical reports.

Key capabilities:
1. Actionable recapture feedback for UNGRADEABLE images based on specific failure gates.
2. Screening messages for GOOD images routing directly to DR classification.
3. Diagnostic messages for BORDERLINE images detailing enhancement outcomes.
4. Typed structured report API for machine-readable JSON export and Markdown generation.
5. Strict adherence to clinical safety language (distinguishing technical image
   quality from medical diagnosis).
"""

from pathlib import Path
from typing import Dict, Any, List, Union, Optional
import numpy as np

from image_quality.decision import classify_image_quality
from image_quality.enhancement import select_best_enhancement


# Clinical language safety disclaimer
CLINICAL_SAFETY_DISCLAIMER: str = (
    "Image quality assessment provides technical screening and optical verification only; "
    "it does not constitute an independent medical diagnosis. Diagnostic certainty requires "
    "clinical evaluation by a qualified eye care professional."
)

# Recommended actions
ACTION_PROCEED_DR: str = "Proceed to DR classification."
ACTION_PROCEED_ENHANCED: str = "Enhanced image may proceed to downstream analysis."
ACTION_RECONSIDER_BORDERLINE: str = "Image remains borderline. Consider recapturing the image."
ACTION_REJECT_RECAPTURE: str = "Reject image and request recapture."

# Specific actionable recapture instructions mapped to triggered quality gates
RECAPTURE_GUIDANCE_MAP: Dict[str, str] = {
    "severe_blur": "Image is too blurry. Please keep the fundus camera steady and refocus before recapturing.",
    "severe_illumination_defect": "Image illumination is inadequate. Please adjust the camera illumination and recapture.",
    "severe_dark_clipping": "Severe underexposure detected with excessive dark clipping. Increase flash intensity or check pupil dilation before recapturing.",
    "severe_glare_clipping": "Excessive corneal glare or reflection detected. Re-align illumination angle and ask patient to blink before recapturing.",
    "severe_fov_truncation": "Insufficient retinal field of view. Reposition the camera and ensure the retinal field is fully visible.",
    "severe_off_center": "Retinal field severely off-center. Center the patient's gaze on the fixation target and recapture.",
    "composite_unusable": "Overall composite quality score is below acceptable diagnostic thresholds. Recapture the fundus image.",
}


def generate_recapture_feedback(triggered_gates: List[Union[Dict[str, Any], str]]) -> str:
    """Generate specific, actionable recapture guidance based on triggered quality gates.

    Args:
        triggered_gates: List of triggered gate dictionaries or gate name strings.

    Returns:
        str: Concise, prioritized operator guidance for image recapture.
    """
    if not triggered_gates:
        return "Image quality insufficient for clinical grading. Recapture the fundus image."

    gate_names: List[str] = []
    for g in triggered_gates:
        if isinstance(g, dict) and "gate" in g:
            gate_names.append(g["gate"])
        elif isinstance(g, str):
            gate_names.append(g)

    advice_items: List[str] = []
    for gn in gate_names:
        if gn in RECAPTURE_GUIDANCE_MAP:
            item = RECAPTURE_GUIDANCE_MAP[gn]
            if item not in advice_items:
                advice_items.append(item)

    if not advice_items:
        return "Image quality insufficient for clinical grading. Adjust camera alignment and recapture."

    if len(advice_items) == 1:
        return advice_items[0]

    # Combine multiple specific guidance points
    combined = "Multiple acquisition defects detected:\n"
    for i, item in enumerate(advice_items, start=1):
        combined += f"{i}. {item}\n"
    return combined.strip()


def build_operator_message(
    quality_status: str,
    composite_score: float,
    triggered_gates: List[Union[Dict[str, Any], str]],
    enhancement_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Construct clear, compliant operator message matching clinical safety policy."""
    status_upper = quality_status.upper()

    if status_upper == "GOOD":
        return (
            f"Image quality acceptable for downstream analysis (Composite score: {composite_score:.1f}/100). "
            "All quality dimensions meet or exceed acceptance criteria."
        )

    if status_upper == "BORDERLINE":
        enh = enhancement_info if enhancement_info is not None else {}
        attempted = enh.get("attempted", False)
        accepted = enh.get("accepted", False)
        method = enh.get("method", "automated")

        gate_str = ", ".join([g["gate"] if isinstance(g, dict) else str(g) for g in triggered_gates]) or "suboptimal quality"

        if attempted and accepted:
            b_score = enh.get("before_composite_score", composite_score)
            a_score = enh.get("after_composite_score", composite_score)
            return (
                f"Image quality was initially borderline due to {gate_str}. "
                f"Automated enhancement ({method.upper()}) was accepted (Score: {b_score:.1f} → {a_score:.1f}). "
                "Enhanced image may proceed to downstream analysis."
            )
        elif attempted and not accepted:
            reason = enh.get("rejection_reason", "safeguard violations")
            return (
                f"Image quality remains borderline due to {gate_str}. Enhancement was attempted but rejected ({reason}). "
                "Consider recapturing the image if higher optical clarity is clinically required."
            )
        else:
            return (
                f"Image quality is borderline due to {gate_str} (Score: {composite_score:.1f}/100). "
                "Consider recapturing the image if higher optical clarity is required."
            )

    if status_upper == "UNGRADEABLE":
        feedback = generate_recapture_feedback(triggered_gates)
        return f"Image is ungradeable and rejected for screening inference. {feedback}"

    return f"Image quality status: {quality_status} (Composite score: {composite_score:.1f}/100)."


def generate_quality_report(
    image_or_path: Union[str, Path, np.ndarray],
    attempt_enhancement_if_borderline: bool = True,
    enhancement_save_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute complete end-to-end IQA pipeline and produce structured operator report.

    Pipeline:
    Image → Focus, Illumination, FOV, Centering → Composite Score →
    Quality Gates & Decision → Enhancement (if Borderline) → Final Structured Report.

    Args:
        image_or_path: Image file path or RGB NumPy array.
        attempt_enhancement_if_borderline: Whether to run enhancement when borderline.
        enhancement_save_dir: Optional path to save derived enhanced image.

    Returns:
        dict: Full structured clinical reporting payload.
    """
    if isinstance(image_or_path, (str, Path)):
        image_path_str = str(image_or_path)
        image_identifier = Path(image_or_path).name
    else:
        image_path_str = "in_memory_array"
        image_identifier = "in_memory_array"

    # 1. Base IQA assessment and decision classification
    iqa_res = classify_image_quality(image_or_path)

    initial_class = iqa_res["final_class"]
    initial_score = float(iqa_res["composite_score"])
    component_scores = iqa_res["component_scores"]
    triggered_gates = iqa_res["triggered_quality_gates"]
    diagnostic_reasons = iqa_res["diagnostic_reasons"]

    # 2. Borderline enhancement handling
    enhancement_info: Dict[str, Any] = {
        "attempted": False,
        "accepted": None,
        "method": None,
        "before_composite_score": None,
        "after_composite_score": None,
        "delta_composite": None,
        "enhanced_image_path": None,
        "rejection_reason": None,
    }

    effective_class = initial_class
    effective_score = initial_score

    if initial_class == "BORDERLINE" and attempt_enhancement_if_borderline:
        enhancement_info["attempted"] = True
        enh_res = select_best_enhancement(
            image_or_path=image_or_path,
            candidate_methods=["clahe", "unsharp", "ben_graham", "denoise"],
            save_dir=enhancement_save_dir,
        )
        selected_eval = enh_res.get("selected_evaluation")
        if selected_eval is not None and selected_eval.get("accepted", False):
            enhancement_info["accepted"] = True
            enhancement_info["method"] = enh_res.get("best_method")
            enhancement_info["before_composite_score"] = selected_eval["before_scores"]["composite_score"]
            enhancement_info["after_composite_score"] = selected_eval["after_scores"]["composite_score"]
            enhancement_info["delta_composite"] = selected_eval["score_differences"]["delta_composite"]
            enhancement_info["enhanced_image_path"] = enh_res.get("saved_enhanced_path")
            enhancement_info["rejection_reason"] = None
            # Update effective score
            effective_score = selected_eval["after_scores"]["composite_score"]
        else:
            enhancement_info["accepted"] = False
            enhancement_info["method"] = enh_res.get("best_method")
            enhancement_info["rejection_reason"] = (
                selected_eval.get("rejection_reason") if selected_eval else "All candidates rejected"
            )

    # 3. Determine recommended action and operator message
    recapture_feedback: Optional[str] = None

    if effective_class == "GOOD":
        recommended_action = ACTION_PROCEED_DR
    elif effective_class == "BORDERLINE":
        if enhancement_info["attempted"] and enhancement_info["accepted"]:
            recommended_action = ACTION_PROCEED_ENHANCED
        else:
            recommended_action = ACTION_RECONSIDER_BORDERLINE
    elif effective_class == "UNGRADEABLE":
        recommended_action = ACTION_REJECT_RECAPTURE
        recapture_feedback = generate_recapture_feedback(triggered_gates)
    else:
        recommended_action = "Review image quality."

    operator_message = build_operator_message(
        quality_status=effective_class,
        composite_score=effective_score,
        triggered_gates=triggered_gates,
        enhancement_info=enhancement_info,
    )

    return {
        "image_identifier": image_identifier,
        "image_path": image_path_str,
        "quality_status": effective_class,
        "composite_score": effective_score,
        "initial_quality_status": initial_class,
        "initial_composite_score": initial_score,
        "component_scores": component_scores,
        "sub_decisions": iqa_res.get("sub_decisions", {}),
        "triggered_quality_gates": triggered_gates,
        "diagnostic_reasons": diagnostic_reasons,
        "enhancement": enhancement_info,
        "recommended_action": recommended_action,
        "operator_message": operator_message,
        "recapture_feedback": recapture_feedback,
        "clinical_safety_disclaimer": CLINICAL_SAFETY_DISCLAIMER,
        "diagnostics": iqa_res.get("diagnostics", {}),
    }


def format_report_markdown(report: Dict[str, Any]) -> str:
    """Format an individual quality report into clean GitHub Markdown."""
    status = report["quality_status"]
    comp_score = report["composite_score"]
    c = report["component_scores"]
    action = report["recommended_action"]
    msg = report["operator_message"]
    gates = report["triggered_quality_gates"]
    enh = report["enhancement"]

    gate_str = ", ".join([g["gate"] if isinstance(g, dict) else str(g) for g in gates]) if gates else "None (Clean)"

    md = f"### Quality Report: `{report['image_identifier']}`\n\n"
    md += f"- **Status**: **{status}**\n"
    md += f"- **Composite Score**: **{comp_score:.2f} / 100**\n"
    md += f"- **Component Scores**: Focus: {c.get('focus_score', 0):.1f} | Illum: {c.get('illumination_score', 0):.1f} | FOV: {c.get('fov_score', 0):.1f} | Centering: {c.get('centering_score', 0):.1f}\n"
    md += f"- **Triggered Gates**: {gate_str}\n"

    if enh.get("attempted"):
        if enh.get("accepted"):
            md += f"- **Enhancement**: Accepted (`{enh.get('method')}`, {enh.get('before_composite_score'):.1f} → {enh.get('after_composite_score'):.1f})\n"
        else:
            md += f"- **Enhancement**: Rejected ({enh.get('rejection_reason', 'safeguards')})\n"
    else:
        md += "- **Enhancement**: Not applicable\n"

    md += f"- **Recommended Action**: `{action}`\n"
    md += f"- **Operator Guidance**: {msg}\n"

    if report.get("recapture_feedback"):
        md += f"- **Recapture Protocol**:\n```text\n{report['recapture_feedback']}\n```\n"

    return md
