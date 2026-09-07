"""IDRiD Dataset Discovery, Manifest Management, and Specification Audit.

Manages dataset discovery, provenance, partition schemas, and annotation
alignment for the Indian Diabetic Retinopathy Image Dataset (IDRiD).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import hashlib
import os

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IDRID_DIR = WORKSPACE_ROOT / "data" / "idrid"
MANIFEST_PATH = WORKSPACE_ROOT / "evidence" / "data" / "idrid_manifest.json"

OFFICIAL_IDRID_PROVENANCE = {
    "dataset_name": "Indian Diabetic Retinopathy Image Dataset (IDRiD)",
    "official_url": "https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid",
    "challenge_url": "https://idrid.grand-challenge.org/",
    "camera": "Kowa VX-10alpha digital fundus camera",
    "field_of_view_deg": 50,
    "native_resolution": [4288, 2848, 3],
    "file_format": "JPG (Images), TIF (Lesion/Structure Masks), CSV (Coordinates & Grades)",
    "parts": {
        "Part_A_Segmentation": {
            "title": "A. Segmentation",
            "archive_name": "A. Segmentation.zip",
            "archive_size_bytes": 584318976,
            "archive_size_mb": 557.25,
            "subsets": {
                "train_images": 54,
                "test_images": 27,
                "total_images": 81,
            },
            "annotation_classes": [
                "1. Microaneurysms",
                "2. Haemorrhages",
                "3. Hard Exudates",
                "4. Soft Exudates",
                "5. Optic Disc",
            ],
            "mask_format": "Binary TIF (0=Background, 255=Lesion/Structure)",
        },
        "Part_B_Disease_Grading": {
            "title": "B. Disease Grading",
            "archive_name": "B. Disease Grading.zip",
            "archive_size_bytes": 212415283,
            "archive_size_mb": 202.57,
            "subsets": {
                "train_images": 413,
                "test_images": 103,
                "total_images": 516,
            },
            "labels": ["Retinopathy Grade (0-4)", "Diabetic Macular Edema Risk Grade (0-2)"],
        },
        "Part_C_Localization": {
            "title": "C. Localization",
            "archive_name": "C. Localization.zip",
            "archive_size_bytes": 212520140,
            "archive_size_mb": 202.67,
            "subsets": {
                "train_images": 413,
                "test_images": 103,
                "total_images": 516,
            },
            "landmarks": [
                "Optic Disc Center (X, Y in pixels)",
                "Fovea Center (X, Y in pixels)",
            ],
        },
    },
}


def check_idrid_availability(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Audit environment for presence of genuine IDRiD dataset archives or directories."""
    target_dir = Path(base_dir) if base_dir is not None else DEFAULT_IDRID_DIR

    candidate_locations = [
        target_dir,
        WORKSPACE_ROOT / "data" / "IDRiD",
        Path("/Users/dakshsrivastava/data/idrid"),
        Path("/Users/dakshsrivastava/Downloads/idrid"),
        Path("/Users/dakshsrivastava/Desktop/idrid"),
    ]

    found_dir: Optional[Path] = None
    for cand in candidate_locations:
        if cand.exists() and cand.is_dir():
            # Check if contains image files or subdirectories
            files = list(cand.glob("**/*.jpg")) + list(cand.glob("**/*.tif")) + list(cand.glob("**/*.csv"))
            if len(files) > 0:
                found_dir = cand
                break

    if found_dir is not None:
        images = sorted(list(found_dir.glob("**/*.jpg")))
        masks = sorted(list(found_dir.glob("**/*.tif")))
        csvs = sorted(list(found_dir.glob("**/*.csv")))
        return {
            "available": True,
            "status": "AVAILABLE",
            "root_path": str(found_dir),
            "image_count": len(images),
            "mask_count": len(masks),
            "csv_count": len(csvs),
            "notes": f"Real IDRiD assets discovered at {found_dir}",
        }

    return {
        "available": False,
        "status": "NOT_AVAILABLE_IN_CURRENT_ENVIRONMENT",
        "root_path": None,
        "image_count": 0,
        "mask_count": 0,
        "csv_count": 0,
        "provenance": OFFICIAL_IDRID_PROVENANCE,
        "reason": (
            "IDRiD dataset is not available locally. Official IEEE DataPort distribution "
            "(https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid) "
            "requires authenticated user credentials to download files ('LOGIN TO ACCESS DATASET FILES'). "
            "Automated unauthenticated retrieval is blocked by the portal. Furthermore, Part A Segmentation "
            "(557.25 MB) exceeds the workspace hard download limit of 500 MB."
        ),
        "guidance": (
            "To evaluate on real IDRiD ground-truth masks: manually download Part A, B, or C "
            "from IEEE DataPort with an authenticated account, and extract to 'data/idrid/'."
        ),
    }


def get_ground_truth_taxonomy_status() -> Dict[str, Dict[str, Any]]:
    """Return verified ground-truth annotation availability in official IDRiD dataset."""
    return {
        "OPTIC_DISC": {
            "category": EvidenceCategory.OPTIC_DISC.value,
            "idrid_status": "AVAILABLE",
            "representation": ["PointLandmark (Part C center X, Y)", "SegmentationMask (Part A OD mask)"],
            "annotation_source": "IDRiD Part A (81 masks) & Part C (516 coordinates)",
            "unit": "pixels (native 4288x2848)",
        },
        "FOVEA": {
            "category": EvidenceCategory.FOVEA.value,
            "idrid_status": "AVAILABLE",
            "representation": ["PointLandmark (Part C fovea center X, Y)"],
            "annotation_source": "IDRiD Part C (516 coordinates)",
            "unit": "pixels (native 4288x2848)",
        },
        "VESSEL": {
            "category": EvidenceCategory.VESSEL.value,
            "idrid_status": "NOT_AVAILABLE_IN_IDRID",
            "representation": ["SegmentationMask"],
            "annotation_source": "Not annotated in IDRiD; external benchmarks (DRIVE, STARE, CHASE_DB1) required",
            "unit": "binary mask",
        },
        "MICROANEURYSM": {
            "category": EvidenceCategory.MICROANEURYSM.value,
            "idrid_status": "AVAILABLE",
            "representation": ["SegmentationMask (Part A binary TIF)"],
            "annotation_source": "IDRiD Part A (81 images: 54 train, 27 test)",
            "unit": "binary pixel mask (native 4288x2848)",
        },
        "EXUDATE": {
            "category": EvidenceCategory.EXUDATE.value,
            "idrid_status": "AVAILABLE",
            "representation": ["SegmentationMask (Hard Exudates TIF + Soft Exudates TIF)"],
            "annotation_source": "IDRiD Part A (81 images: 54 train, 27 test)",
            "unit": "binary pixel mask (native 4288x2848)",
        },
        "HEMORRHAGE": {
            "category": EvidenceCategory.HEMORRHAGE.value,
            "idrid_status": "AVAILABLE",
            "representation": ["SegmentationMask (Haemorrhages TIF)"],
            "annotation_source": "IDRiD Part A (81 images: 54 train, 27 test)",
            "unit": "binary pixel mask (native 4288x2848)",
        },
        "NEOVASCULARIZATION": {
            "category": EvidenceCategory.NEOVASCULARIZATION.value,
            "idrid_status": "NOT_AVAILABLE_IN_IDRID",
            "representation": ["SegmentationMask / BoundingBox"],
            "annotation_source": "Not annotated in IDRiD; specialized Proliferative DR cohort (e.g. DDR) required",
            "unit": "unsupported in current dataset",
        },
    }


def analyze_microaneurysm_spatial_resolution() -> Dict[str, Any]:
    """Technical spatial analysis of microaneurysm annotations and sub-pixel claims (Task 13)."""
    return {
        "native_resolution": [4288, 2848, 3],
        "field_of_view_deg": 50.0,
        "approx_retinal_diameter_mm": 15.0,
        "microns_per_native_pixel": round(15000.0 / 4288.0, 2),  # ~3.5 microns/pixel
        "physiological_microaneurysm_size_microns": [10.0, 100.0],
        "microaneurysm_native_pixel_span": [3, 29],  # 10 um / 3.5 um -> ~3 px; 100 um -> ~29 px
        "annotation_format": "Discrete binary pixel grid (.tif), 0 or 255",
        "sub_pixel_ground_truth_present": False,
        "downsampled_resolution": [384, 384, 3],
        "microns_per_downsampled_pixel": round(15000.0 / 384.0, 2),  # ~39.1 microns/pixel
        "downsampling_implication": (
            "Downsampling native fundus images from 4288x2848 to 384x384 (11.2x reduction) "
            "causes 1 pixel to represent ~39 microns. Microaneurysms under 39 microns "
            "physically collapse into sub-pixel dimensions (< 1 pixel). A standard 384x384 "
            "convolutional network cannot detect sub-pixel lesions without severe aliasing. "
            "Genuine microaneurysm localization requires native-resolution patch extraction (e.g. 512x512 patches "
            "at full 3.5 um/pixel resolution), NOT downsampled whole-image inference."
        ),
        "sub_pixel_claim_verdict": (
            "The phrase 'sub-pixel microaneurysm detection' cannot be claimed on 384x384 models. "
            "The IDRiD ground truth itself is pixel-quantized (integer grid), not continuous sub-pixel splines. "
            "Any future microaneurysm model must be evaluated on full-resolution patch crops and evaluated "
            "against discrete pixel masks."
        ),
    }


def generate_idrid_manifest(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generate reproducible IDRiD dataset audit manifest (Task 3)."""
    avail = check_idrid_availability()
    taxonomy = get_ground_truth_taxonomy_status()
    ma_analysis = analyze_microaneurysm_spatial_resolution()

    manifest = {
        "manifest_version": "1.0.0",
        "dataset_name": "Indian Diabetic Retinopathy Image Dataset (IDRiD)",
        "availability_status": avail["status"],
        "available_locally": avail["available"],
        "availability_details": avail,
        "provenance": OFFICIAL_IDRID_PROVENANCE,
        "annotation_taxonomy": taxonomy,
        "microaneurysm_resolution_analysis": ma_analysis,
        "neovascularization_status": {
            "status": "NOT_AVAILABLE_IN_IDRID",
            "recommendation": "Do not train or claim neovascularization detector until specialized NV dataset is acquired.",
        },
        "vessel_segmentation_status": {
            "status": "NOT_AVAILABLE_IN_IDRID",
            "recommendation": "Use DRIVE or CHASE_DB1 benchmark for retinal vessel segmentation.",
        },
        "engineering_invariants": {
            "classifier_v2_frozen": True,
            "no_synthetic_data": True,
            "no_fabricated_annotations": True,
            "training_stage": "AUDIT_ONLY_NO_TRAINING",
        },
    }

    out_file = Path(output_path) if output_path is not None else MANIFEST_PATH
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
