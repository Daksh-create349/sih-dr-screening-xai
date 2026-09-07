"""Evidence aggregation and clinical context reporting module.

Synthesizes model predictions, Grad-CAM feature attributions, anatomical
landmark localizations, and anatomical region statistics into structured
clinical evidence reports.

STRICT CLINICAL SAFETY NOTICE:
Grad-CAM heatmaps provide model feature attribution only. They do NOT detect,
segment, or prove the physical presence of microaneurysms, hemorrhages,
exudates, or neovascularization, and do NOT constitute medical diagnosis.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np

from image_quality.io import load_raw_image
from classifier.referable import get_dr_grade_name
from explainability.anatomy import (
    localize_retinal_anatomy,
    define_anatomical_regions,
    compute_attention_region_statistics,
    extract_top_attention_bounding_box,
)
from explainability.gradcam import compute_full_retinal_gradcam

CLINICAL_SAFETY_DISCLAIMER: str = (
    "Grad-CAM heatmaps represent neural network mathematical feature "
    "attribution indicating image regions that influenced the model's "
    "classification score. They do NOT identify, segment, or prove the "
    "presence of clinical lesions (e.g., microaneurysms, hemorrhages, "
    "hard exudates) and do NOT constitute medical diagnosis or replace "
    "ophthalmological evaluation."
)


def synthesize_evidence_narrative(
    predicted_grade: int,
    predicted_name: str,
    target_score: float,
    top_region_name: str,
    top_region_mass_pct: float,
    macular_overlap_pct: float,
    optic_disc_overlap_pct: float,
    bbox_info: Dict[str, Any],
) -> str:
    """Generate concise, neutral natural language clinical evidence narrative.

    Uses neutral terminology strictly avoiding lesion claims.
    """
    bx = bbox_info.get("x", 0)
    by = bbox_info.get("y", 0)
    bw = bbox_info.get("width", 0)
    bh = bbox_info.get("height", 0)

    clean_region = top_region_name.replace("_", " ").title()

    narrative = (
        f"Model classified retinal image as Grade {predicted_grade} "
        f"({predicted_name}) with {target_score * 100.0:.1f}% confidence. "
        f"Model feature attribution is concentrated predominantly in the "
        f"{clean_region} ({top_region_mass_pct:.1f}% of total retinal "
        f"attention mass). "
        f"Attention overlap with macular context is "
        f"{macular_overlap_pct:.1f}%, and optic disc overlap is "
        f"{optic_disc_overlap_pct:.1f}%. "
        f"Primary attention cluster bounded at [x={bx}, y={by}, "
        f"w={bw}, h={bh}]. "
        f"Evidence status: feature attribution only."
    )
    return narrative


def generate_retinal_evidence(
    image_or_path: Union[str, Path, Any],
    model: Optional[Any] = None,
    target_class: Optional[int] = None,
    attention_threshold: float = 0.5,
) -> Dict[str, Any]:
    """Execute end-to-end retinal explainability and evidence extraction.

    Workflow:
    1. Compute classifier prediction and full retinal Grad-CAM heatmap.
    2. Localize retinal anatomical landmarks (retinal disk, OD, macula).
    3. Partition retina into standard anatomical context regions.
    4. Compute regional attention mass, mean, max, and threshold overlap.
    5. Extract compact peak attention bounding box.
    6. Construct structured clinical evidence report.

    Args:
        image_or_path: Path to retinal image or loaded image array.
        model: Loaded Keras classifier model (optional).
        target_class: Target class index {0..4} (optional).
        attention_threshold: Value in [0, 1] for high attention overlap.

    Returns:
        dict: Complete structured clinical evidence payload.
    """
    # 1. Compute complete retinal Grad-CAM
    cam_data = compute_full_retinal_gradcam(
        image_or_path=image_or_path,
        model=model,
        target_class=target_class,
    )

    warped_cam = cam_data["warped_retinal_heatmap"]
    h_img, w_img = warped_cam.shape[:2]

    # 2. Localize anatomical landmarks
    if isinstance(image_or_path, np.ndarray):
        raw_img = image_or_path
    else:
        raw_img = load_raw_image(image_or_path)

    anatomy = localize_retinal_anatomy(image=raw_img)

    retina_field = anatomy["retinal_field"]
    retina_center = (retina_field["center_x"], retina_field["center_y"])
    retina_radius = retina_field["radius"]
    retina_mask = anatomy["retina_mask"]
    od_meta = anatomy["optic_disc"]
    macula_meta = anatomy["macula"]

    # 3. Define context regions
    regions = define_anatomical_regions(
        image_shape=(h_img, w_img),
        retina_mask=retina_mask,
        retina_center=retina_center,
        retina_radius=retina_radius,
        optic_disc=od_meta,
        macula=macula_meta,
    )

    # 4. Attention statistics across regions
    stats_data = compute_attention_region_statistics(
        warped_cam=warped_cam,
        anatomical_regions=regions,
        attention_threshold=attention_threshold,
    )
    reg_stats = stats_data["region_statistics"]

    # 5. Extract top attention bounding box
    bbox_meta = extract_top_attention_bounding_box(
        warped_cam=warped_cam,
        retinal_mask=retina_mask,
        threshold_ratio=0.65,
    )

    # 6. Identify top anatomical region (excluding whole foreground)
    sub_regions = {
        k: v for k, v in reg_stats.items()
        if k != "retinal_foreground"
    }
    if sub_regions:
        top_region = max(
            sub_regions.keys(),
            key=lambda k: sub_regions[k]["attention_fraction"],
        )
        top_region_mass_pct = (
            sub_regions[top_region]["attention_fraction"] * 100.0
        )
    else:
        top_region = "retinal_foreground"
        top_region_mass_pct = 100.0

    mac_overlap = (
        reg_stats.get("macular_region", {}).get("overlap_fraction", 0.0)
    )
    mac_overlap_pct = mac_overlap * 100.0
    od_overlap_pct = (
        reg_stats.get("optic_disc_region", {}).get("overlap_fraction", 0.0)
        * 100.0
    )

    pred_cls = int(cam_data["predicted_class"])
    pred_name = get_dr_grade_name(pred_cls)
    target_score = float(cam_data["target_score"])

    narrative = synthesize_evidence_narrative(
        predicted_grade=pred_cls,
        predicted_name=pred_name,
        target_score=target_score,
        top_region_name=top_region,
        top_region_mass_pct=top_region_mass_pct,
        macular_overlap_pct=mac_overlap_pct,
        optic_disc_overlap_pct=od_overlap_pct,
        bbox_info=bbox_meta,
    )

    # Clean non-serializable mask arrays for output dictionary
    clean_regions_meta = {}
    for r_name, r_dict in reg_stats.items():
        clean_regions_meta[r_name] = r_dict

    return {
        "predicted_class": pred_cls,
        "predicted_class_name": pred_name,
        "predicted_probabilities": cam_data["predicted_probabilities"],
        "target_class": int(cam_data["target_class"]),
        "target_score": target_score,
        "evidence_status": "feature_attribution_only",
        "top_attention_region": top_region,
        "top_attention_mass_pct": round(top_region_mass_pct, 2),
        "macular_overlap_pct": round(mac_overlap_pct, 2),
        "optic_disc_overlap_pct": round(od_overlap_pct, 2),
        "attention_bounding_box": bbox_meta,
        "attention_statistics": clean_regions_meta,
        "anatomical_landmarks": {
            "retinal_field": retina_field,
            "optic_disc": od_meta,
            "macula": macula_meta,
        },
        "coordinate_mapping": cam_data["coordinate_mapping"],
        "narrative_summary": narrative,
        "safety_disclaimer": CLINICAL_SAFETY_DISCLAIMER,
        "native_heatmap": cam_data["native_heatmap"],
        "heatmap_384": cam_data["heatmap_384"],
        "warped_retinal_heatmap": warped_cam,
    }
