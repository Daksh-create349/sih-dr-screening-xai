"""Retinal Structure and Lesion Evidence Package.

Exposes core schema, dataset manifest utilities, anatomical bridges, and audit routines.
"""

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    BoundingBox,
    SegmentationMask,
    RetinalEvidenceRecord,
)
from evidence.dataset import (
    check_idrid_availability,
    get_ground_truth_taxonomy_status,
    analyze_microaneurysm_spatial_resolution,
    generate_idrid_manifest,
    OFFICIAL_IDRID_PROVENANCE,
)
from evidence.annotations import (
    compare_landmark_localization,
    compute_segmentation_metrics,
    extract_evidence_from_existing_anatomy,
)
from evidence.visualization import render_evidence_inspection_card
from evidence.audit import audit_image_directory, run_evidence_data_audit
from evidence.idrid import (
    IDRiDDataset,
    IDRiDNotFoundError,
    resolve_idrid_root,
    GROUND_TRUTH,
    DETECTED,
    ESTIMATED,
    NOT_AVAILABLE,
    EXTERNAL_DATASET_REQUIRED,
    OPTIC_DISC,
    FOVEA,
    MICROANEURYSM,
    HARD_EXUDATE,
    SOFT_EXUDATE,
    HEMORRHAGE,
    VESSEL,
    NEOVASCULARIZATION,
    IDRID_SUPPORTED_CATEGORIES,
    EXTERNAL_REQUIRED_CATEGORIES,
)

__all__ = [
    "AnnotationStatus",
    "EvidenceCategory",
    "PointLandmark",
    "BoundingBox",
    "SegmentationMask",
    "RetinalEvidenceRecord",
    "check_idrid_availability",
    "get_ground_truth_taxonomy_status",
    "analyze_microaneurysm_spatial_resolution",
    "generate_idrid_manifest",
    "OFFICIAL_IDRID_PROVENANCE",
    "compare_landmark_localization",
    "compute_segmentation_metrics",
    "extract_evidence_from_existing_anatomy",
    "render_evidence_inspection_card",
    "audit_image_directory",
    "run_evidence_data_audit",
    "IDRiDDataset",
    "IDRiDNotFoundError",
    "resolve_idrid_root",
    "GROUND_TRUTH",
    "DETECTED",
    "ESTIMATED",
    "NOT_AVAILABLE",
    "EXTERNAL_DATASET_REQUIRED",
    "OPTIC_DISC",
    "FOVEA",
    "MICROANEURYSM",
    "HARD_EXUDATE",
    "SOFT_EXUDATE",
    "HEMORRHAGE",
    "VESSEL",
    "NEOVASCULARIZATION",
    "IDRID_SUPPORTED_CATEGORIES",
    "EXTERNAL_REQUIRED_CATEGORIES",
]
