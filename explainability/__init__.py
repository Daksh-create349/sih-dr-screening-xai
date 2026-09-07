"""Explainability package for Diabetic Retinopathy screening system.

Milestone 11:
- Step 1: Programmatic Grad-CAM layer discovery and verification.
- Step 2: Grad-CAM heatmap computation and retinal coordinate warping.
- Step 3: Anatomical retinal localization and evidence annotation layer.
"""

from explainability.gradcam import (
    list_all_candidate_layers,
    discover_gradcam_layer,
    validate_gradcam_connectivity,
    extract_feature_tensor,
    compute_gradcam,
    resize_gradcam_to_input,
    warp_gradcam_to_retinal_coordinates,
    compute_full_retinal_gradcam,
)
from explainability.anatomy import (
    localize_retinal_anatomy,
    define_anatomical_regions,
    compute_attention_region_statistics,
    extract_top_attention_bounding_box,
)
from explainability.evidence import (
    generate_retinal_evidence,
    synthesize_evidence_narrative,
    CLINICAL_SAFETY_DISCLAIMER,
)

__all__ = [
    "list_all_candidate_layers",
    "discover_gradcam_layer",
    "validate_gradcam_connectivity",
    "extract_feature_tensor",
    "compute_gradcam",
    "resize_gradcam_to_input",
    "warp_gradcam_to_retinal_coordinates",
    "compute_full_retinal_gradcam",
    "localize_retinal_anatomy",
    "define_anatomical_regions",
    "compute_attention_region_statistics",
    "extract_top_attention_bounding_box",
    "generate_retinal_evidence",
    "synthesize_evidence_narrative",
    "CLINICAL_SAFETY_DISCLAIMER",
]
