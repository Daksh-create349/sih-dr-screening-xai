"""Retinal Evidence Schema and Data Structures.

Defines the formal internal data structures, taxonomy, and representation types
for anatomical landmarks and pathological lesions in retinal fundus imaging.

STRICT TAXONOMIC RULE:
Every evidence item must explicitly declare its status:
- GROUND_TRUTH: Certified expert clinical annotation from reference benchmark.
- DETECTED: Algorithmically localized by a genuine detector/segmenter.
- ESTIMATED: Geometric or photometric heuristic approximation.
- NOT_AVAILABLE: Explicitly absent from dataset or pipeline.

Mixing ground truth with predictions is strictly prohibited.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import json
import numpy as np


class AnnotationStatus(str, Enum):
    """Integrity status of an evidence annotation or measurement."""
    GROUND_TRUTH = "GROUND_TRUTH"
    DETECTED = "DETECTED"
    ESTIMATED = "ESTIMATED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    EXTERNAL_DATASET_REQUIRED = "EXTERNAL_DATASET_REQUIRED"


class EvidenceCategory(str, Enum):
    """Standardized anatomical structures and retinal lesion classes."""
    OPTIC_DISC = "OPTIC_DISC"
    FOVEA = "FOVEA"
    VESSEL = "VESSEL"
    MICROANEURYSM = "MICROANEURYSM"
    EXUDATE = "EXUDATE"
    HARD_EXUDATE = "HARD_EXUDATE"
    SOFT_EXUDATE = "SOFT_EXUDATE"
    HEMORRHAGE = "HEMORRHAGE"
    NEOVASCULARIZATION = "NEOVASCULARIZATION"


@dataclass
class PointLandmark:
    """Planar coordinate representation for focal anatomical landmarks."""
    category: EvidenceCategory
    status: AnnotationStatus
    x: Optional[float] = None
    y: Optional[float] = None
    confidence: Optional[float] = None
    radius: Optional[float] = None
    tolerance_pixels: Optional[float] = None
    source: str = "unspecified"
    method: str = "unspecified"
    notes: Optional[str] = None

    def is_available(self) -> bool:
        return self.status != AnnotationStatus.NOT_AVAILABLE and self.x is not None and self.y is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "status": self.status.value,
            "x": self.x,
            "y": self.y,
            "confidence": self.confidence,
            "radius": self.radius,
            "tolerance_pixels": self.tolerance_pixels,
            "source": self.source,
            "method": self.method,
            "notes": self.notes,
        }


@dataclass
class BoundingBox:
    """Bounding box region for attention clusters or localized lesions."""
    category: EvidenceCategory
    status: AnnotationStatus
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: Optional[float] = None
    area_fraction: Optional[float] = None
    source: str = "unspecified"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "status": self.status.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "area_fraction": self.area_fraction,
            "source": self.source,
            "notes": self.notes,
        }


@dataclass
class SegmentationMask:
    """Pixel-level spatial segmentation mask representation."""
    category: EvidenceCategory
    status: AnnotationStatus
    mask_shape: Optional[Tuple[int, int]] = None
    non_zero_pixels: int = 0
    area_fraction: float = 0.0
    mask_path: Optional[str] = None
    source: str = "unspecified"
    method: str = "unspecified"
    notes: Optional[str] = None

    def is_available(self) -> bool:
        return self.status != AnnotationStatus.NOT_AVAILABLE and self.non_zero_pixels > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "status": self.status.value,
            "mask_shape": list(self.mask_shape) if self.mask_shape else None,
            "non_zero_pixels": self.non_zero_pixels,
            "area_fraction": self.area_fraction,
            "mask_path": self.mask_path,
            "source": self.source,
            "method": self.method,
            "notes": self.notes,
        }


@dataclass
class RetinalEvidenceRecord:
    """Complete unified multi-structure evidence record for a retinal photograph."""
    image_id: str
    image_path: Optional[str] = None
    image_dimensions: Optional[Tuple[int, int, int]] = None

    # Anatomical Structures
    optic_disc: PointLandmark = field(
        default_factory=lambda: PointLandmark(
            category=EvidenceCategory.OPTIC_DISC,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    fovea: PointLandmark = field(
        default_factory=lambda: PointLandmark(
            category=EvidenceCategory.FOVEA,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    vessels: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.VESSEL,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )

    # Pathological Lesions
    microaneurysms: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.MICROANEURYSM,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    exudates: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.EXUDATE,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    hard_exudates: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.HARD_EXUDATE,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    soft_exudates: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.SOFT_EXUDATE,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    hemorrhages: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.HEMORRHAGE,
            status=AnnotationStatus.NOT_AVAILABLE,
        )
    )
    neovascularization: SegmentationMask = field(
        default_factory=lambda: SegmentationMask(
            category=EvidenceCategory.NEOVASCULARIZATION,
            status=AnnotationStatus.NOT_AVAILABLE,
            notes="Neovascularization ground truth not available in standard IDRiD benchmark",
        )
    )

    # Provenance and Metadata
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "image_path": self.image_path,
            "image_dimensions": list(self.image_dimensions) if self.image_dimensions else None,
            "structures": {
                "optic_disc": self.optic_disc.to_dict(),
                "fovea": self.fovea.to_dict(),
                "vessels": self.vessels.to_dict(),
            },
            "lesions": {
                "microaneurysms": self.microaneurysms.to_dict(),
                "exudates": self.exudates.to_dict(),
                "hard_exudates": self.hard_exudates.to_dict(),
                "soft_exudates": self.soft_exudates.to_dict(),
                "hemorrhages": self.hemorrhages.to_dict(),
                "neovascularization": self.neovascularization.to_dict(),
            },
            "provenance": self.provenance,
        }
