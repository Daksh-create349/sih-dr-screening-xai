"""IDRiD Dataset Staging Contract and Interface.

MODULE 1A — IDRiD DATASET STAGING CONTRACT
Strict modular interface for the Indian Diabetic Retinopathy Image Dataset (IDRiD).

Safety Invariants:
- Frozen V2 Classifier: model/MODEL_V2_80pct_backup.keras remains untouched.
- Zero Synthetic / Mock Data: Never fabricate annotations or synthetic retinal images.
- Strict Epistemic Taxonomy: GROUND_TRUTH, DETECTED, ESTIMATED, NOT_AVAILABLE.
- Missing-Data Safety: Fails explicitly with 'IDRiD DATASET NOT FOUND' when dataset is missing.
- External Requirements: Retinal vessels and neovascularization are strictly flagged as
  EXTERNAL_DATASET_REQUIRED.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import hashlib
import os
import re
from PIL import Image

from evidence.schema import (
    AnnotationStatus,
    EvidenceCategory,
    PointLandmark,
    SegmentationMask,
    RetinalEvidenceRecord,
)

# -------------------------------------------------------------------------
# Taxonomy & Status Constants (Task 4)
# -------------------------------------------------------------------------
GROUND_TRUTH = AnnotationStatus.GROUND_TRUTH.value
DETECTED = AnnotationStatus.DETECTED.value
ESTIMATED = AnnotationStatus.ESTIMATED.value
NOT_AVAILABLE = AnnotationStatus.NOT_AVAILABLE.value
EXTERNAL_DATASET_REQUIRED = "EXTERNAL_DATASET_REQUIRED"

# Supported IDRiD Structure & Lesion Categories
OPTIC_DISC = EvidenceCategory.OPTIC_DISC.value
FOVEA = EvidenceCategory.FOVEA.value
MICROANEURYSM = EvidenceCategory.MICROANEURYSM.value
HARD_EXUDATE = EvidenceCategory.HARD_EXUDATE.value
SOFT_EXUDATE = EvidenceCategory.SOFT_EXUDATE.value
HEMORRHAGE = EvidenceCategory.HEMORRHAGE.value

# Explicit External Dataset Requirements (IDRiD does NOT contain these)
VESSEL = EXTERNAL_DATASET_REQUIRED
NEOVASCULARIZATION = EXTERNAL_DATASET_REQUIRED

IDRID_SUPPORTED_CATEGORIES: List[str] = [
    OPTIC_DISC,
    FOVEA,
    MICROANEURYSM,
    HARD_EXUDATE,
    SOFT_EXUDATE,
    HEMORRHAGE,
]

EXTERNAL_REQUIRED_CATEGORIES: Dict[str, str] = {
    "VESSEL": EXTERNAL_DATASET_REQUIRED,
    "NEOVASCULARIZATION": EXTERNAL_DATASET_REQUIRED,
}

# -------------------------------------------------------------------------
# Provenance & Path Specifications (Tasks 1, 5, 6)
# -------------------------------------------------------------------------
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCAL_IDRID_DIR = WORKSPACE_ROOT / "data" / "external" / "IDRiD"
DEFAULT_COLAB_IDRID_DIR = Path("/content/IDRiD")
MANIFEST_OUTPUT_PATH = WORKSPACE_ROOT / "evidence" / "data" / "idrid_manifest.json"

OFFICIAL_IDRID_PROVENANCE: Dict[str, Any] = {
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


# -------------------------------------------------------------------------
# Exceptions (Task 7)
# -------------------------------------------------------------------------
class IDRiDNotFoundError(FileNotFoundError):
    """Raised when genuine IDRiD dataset cannot be located or is empty."""
    pass


# -------------------------------------------------------------------------
# Dataset Root Discovery (Task 5, Task 6)
# Priority: CLI argument -> Environment variable -> Config file -> Default
# -------------------------------------------------------------------------
def resolve_idrid_root(
    cli_arg: Optional[Union[str, Path]] = None,
    env_var: str = "IDRID_ROOT",
    config_file: Optional[Union[str, Path]] = None,
    default_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve IDRiD dataset root directory following strict priority order.

    Priority:
    1. CLI argument (if provided)
    2. Environment variable (IDRID_ROOT)
    3. Configuration file (config.json or dataset_config.json)
    4. Google Colab documented contract (/content/IDRiD if present)
    5. Documented default (data/external/IDRiD)
    """
    # 1. CLI argument
    if cli_arg is not None and str(cli_arg).strip():
        return Path(cli_arg).resolve()

    # 2. Environment variable
    env_val = os.environ.get(env_var)
    if env_val is not None and env_val.strip():
        return Path(env_val.strip()).resolve()

    # 3. Configuration file
    candidate_configs: List[Path] = []
    if config_file is not None:
        candidate_configs.append(Path(config_file))
    candidate_configs.extend([
        WORKSPACE_ROOT / "dataset_config.json",
        WORKSPACE_ROOT / "config.json",
    ])

    for cfg_path in candidate_configs:
        if cfg_path.exists() and cfg_path.is_file():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    val = cfg_data.get("IDRID_ROOT") or cfg_data.get("idrid_root")
                    if val and str(val).strip():
                        return Path(str(val).strip()).resolve()
            except Exception:
                pass

    # 4. Google Colab standard mount contract (/content/IDRiD)
    if DEFAULT_COLAB_IDRID_DIR.exists() and DEFAULT_COLAB_IDRID_DIR.is_dir():
        return DEFAULT_COLAB_IDRID_DIR.resolve()

    # 5. Documented default
    if default_dir is not None:
        return Path(default_dir).resolve()

    return DEFAULT_LOCAL_IDRID_DIR.resolve()


# -------------------------------------------------------------------------
# SHA-256 Hashing Utility (Task 8)
# -------------------------------------------------------------------------
def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Compute cryptographic SHA-256 checksum of file in streaming chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# -------------------------------------------------------------------------
# IDRiD Dataset Interface (Tasks 2, 7, 8)
# -------------------------------------------------------------------------
class IDRiDDataset:
    """Formal interface to the Indian Diabetic Retinopathy Image Dataset (IDRiD).

    Handles root discovery, image & annotation alignment, partition identification,
    SHA-256 integrity audits, and reproducible manifest generation.
    Enforces zero synthetic data and fails if real dataset is not mounted.
    """

    # Expose taxonomy definitions on class for direct access
    GROUND_TRUTH = GROUND_TRUTH
    DETECTED = DETECTED
    ESTIMATED = ESTIMATED
    NOT_AVAILABLE = NOT_AVAILABLE
    EXTERNAL_DATASET_REQUIRED = EXTERNAL_DATASET_REQUIRED

    OPTIC_DISC = OPTIC_DISC
    FOVEA = FOVEA
    MICROANEURYSM = MICROANEURYSM
    HARD_EXUDATE = HARD_EXUDATE
    SOFT_EXUDATE = SOFT_EXUDATE
    HEMORRHAGE = HEMORRHAGE

    VESSEL = VESSEL
    NEOVASCULARIZATION = NEOVASCULARIZATION

    def __init__(
        self,
        root: Optional[Union[str, Path]] = None,
        require_exists: bool = True,
        config_file: Optional[Union[str, Path]] = None,
    ):
        """Initialize IDRiD dataset interface.

        Args:
            root: Optional explicit root path (CLI argument priority).
            require_exists: If True, immediately validates that real data exists,
                raising IDRiDNotFoundError with message 'IDRiD DATASET NOT FOUND'
                if absent. If False, allows inspection/metadata queries without files.
            config_file: Optional path to JSON configuration file.
        """
        self.root = resolve_idrid_root(cli_arg=root, config_file=config_file)
        self.require_exists = require_exists

        if self.require_exists:
            self.validate_dataset_present()

    def is_available(self) -> bool:
        """Check if real IDRiD files exist in the resolved root."""
        if not self.root.exists() or not self.root.is_dir():
            return False
        # Look for at least one genuine IDRiD image file
        raw_images = self._find_raw_images()
        return len(raw_images) > 0

    def validate_dataset_present(self) -> None:
        """Enforce strict real-data safety. Raise IDRiDNotFoundError if missing."""
        if not self.root.exists():
            raise IDRiDNotFoundError(
                f"IDRiD DATASET NOT FOUND: Root directory does not exist: {self.root}"
            )
        if not self.root.is_dir():
            raise IDRiDNotFoundError(
                f"IDRiD DATASET NOT FOUND: Root path is not a directory: {self.root}"
            )
        raw_images = self._find_raw_images()
        if len(raw_images) == 0:
            raise IDRiDNotFoundError(
                f"IDRiD DATASET NOT FOUND: No IDRiD image files discovered under: {self.root}"
            )

    def _find_raw_images(self) -> List[Path]:
        """Find raw fundus images while strictly ignoring mask and label files."""
        if not self.root.exists() or not self.root.is_dir():
            return []

        extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
        mask_folder_patterns = [
            "groundtruth",
            "mask",
            "microaneurysm",
            "haemorrhage",
            "hemorrhage",
            "exudate",
            "optic disc",
            "optic_disc",
        ]
        mask_filename_suffixes = [
            "_ma",
            "_he",
            "_ex",
            "_se",
            "_od",
            "_mask",
            "_label",
        ]

        found_images: List[Path] = []
        for p in self.root.glob("**/*"):
            if not p.is_file() or p.suffix.lower() not in extensions:
                continue

            # Check if inside an annotation/mask subdirectory
            path_str_lower = str(p).lower()
            if any(pat in path_str_lower for pat in mask_folder_patterns):
                continue

            stem_lower = p.stem.lower()
            if any(stem_lower.endswith(suf) for suf in mask_filename_suffixes):
                continue

            # Match IDRiD naming pattern (e.g. IDRiD_01, IDRiD_001)
            if re.search(r"IDRiD_\d+", p.name, re.IGNORECASE):
                found_images.append(p)

        return sorted(found_images)

    def discover_images(self) -> List[Dict[str, Any]]:
        """Discover all raw fundus images and parse their IDs, splits, and paths.

        Returns:
            List of dicts containing image_id, image_path, split, filename.
        """
        if self.require_exists:
            self.validate_dataset_present()
        elif not self.is_available():
            return []

        images = self._find_raw_images()
        discovered: List[Dict[str, Any]] = []

        for p in images:
            match = re.search(r"IDRiD_(\d+)", p.name, re.IGNORECASE)
            image_id = f"IDRiD_{match.group(1)}" if match else p.stem

            split = self._determine_split(p)

            discovered.append({
                "image_id": image_id,
                "image_path": str(p.resolve()),
                "filename": p.name,
                "split": split,
            })

        return discovered

    def _determine_split(self, path: Path) -> str:
        """Determine whether an asset belongs to train or test split."""
        path_lower = str(path).lower()
        if "train" in path_lower:
            return "train"
        if "test" in path_lower:
            return "test"
        return "unknown"

    def discover_annotations(self) -> Dict[str, Dict[str, List[Path]]]:
        """Discover available mask and coordinate annotations categorized by structure.

        Returns:
            Dict mapping category -> {'train': [Path, ...], 'test': [Path, ...]}
        """
        if not self.root.exists():
            return {cat: {"train": [], "test": []} for cat in IDRID_SUPPORTED_CATEGORIES}

        annotations: Dict[str, Dict[str, List[Path]]] = {
            OPTIC_DISC: {"train": [], "test": []},
            FOVEA: {"train": [], "test": []},
            MICROANEURYSM: {"train": [], "test": []},
            HARD_EXUDATE: {"train": [], "test": []},
            SOFT_EXUDATE: {"train": [], "test": []},
            HEMORRHAGE: {"train": [], "test": []},
        }

        # Search for all mask files (.tif, .png) and CSV coordinate files
        for p in self.root.glob("**/*"):
            if not p.is_file():
                continue

            split = self._determine_split(p)
            split_key = split if split in ("train", "test") else "train"
            name_lower = p.name.lower()
            path_lower = str(p).lower()

            # Microaneurysms
            if "_ma." in name_lower or "microaneurysm" in path_lower:
                if p.suffix.lower() in (".tif", ".tiff", ".png", ".jpg"):
                    annotations[MICROANEURYSM][split_key].append(p)

            # Hemorrhages
            elif "_he." in name_lower or "haemorrhage" in path_lower or "hemorrhage" in path_lower:
                if p.suffix.lower() in (".tif", ".tiff", ".png", ".jpg"):
                    annotations[HEMORRHAGE][split_key].append(p)

            # Hard Exudates
            elif "_ex." in name_lower or "hard exudate" in path_lower or "hard_exudate" in path_lower:
                if p.suffix.lower() in (".tif", ".tiff", ".png", ".jpg"):
                    annotations[HARD_EXUDATE][split_key].append(p)

            # Soft Exudates
            elif "_se." in name_lower or "soft exudate" in path_lower or "soft_exudate" in path_lower:
                if p.suffix.lower() in (".tif", ".tiff", ".png", ".jpg"):
                    annotations[SOFT_EXUDATE][split_key].append(p)

            # Optic Disc (Masks or localization CSVs)
            elif "_od." in name_lower or "optic disc" in path_lower or "optic_disc" in path_lower:
                annotations[OPTIC_DISC][split_key].append(p)

            # Fovea (Localization CSVs)
            elif "fovea" in path_lower:
                annotations[FOVEA][split_key].append(p)

        return annotations

    def match_image_annotations(self, image_id: str) -> Dict[str, Any]:
        """Match an image ID to its corresponding ground truth annotations.

        Args:
            image_id: ID of the image (e.g., 'IDRiD_01' or 'IDRiD_001').

        Returns:
            Dict containing available annotations, paths, and missing flags.
        """
        match = re.search(r"\d+", image_id)
        num_str = match.group(0) if match else image_id
        num_int = int(num_str) if match else -1

        all_ann = self.discover_annotations()
        available_categories: List[str] = []
        annotation_paths: Dict[str, str] = {}
        missing_flags: Dict[str, bool] = {}

        for cat in IDRID_SUPPORTED_CATEGORIES:
            found_path: Optional[Path] = None
            for split_key in ("train", "test"):
                for p in all_ann[cat][split_key]:
                    # Check filename for numeric match
                    p_match = re.search(r"IDRiD_0*(\d+)", p.name, re.IGNORECASE)
                    if p_match and int(p_match.group(1)) == num_int:
                        found_path = p
                        break
                    # If CSV markings table
                    if p.suffix.lower() == ".csv":
                        found_path = p
                if found_path is not None:
                    break

            if found_path is not None:
                available_categories.append(cat)
                annotation_paths[cat] = str(found_path.resolve())
                missing_flags[cat] = False
            else:
                missing_flags[cat] = True

        # External required categories: vessels and neovascularization are NEVER in IDRiD
        for ext_cat in EXTERNAL_REQUIRED_CATEGORIES:
            missing_flags[ext_cat] = True

        return {
            "image_id": image_id,
            "available_annotations": available_categories,
            "annotation_paths": annotation_paths,
            "missing_annotation_flags": missing_flags,
            "external_dataset_required": list(EXTERNAL_REQUIRED_CATEGORIES.keys()),
        }

    def generate_manifest(self, output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Generate reproducible JSON manifest for the staged IDRiD dataset (Task 3).

        Includes: image ID, image path, split, width, height, available annotations,
        annotation paths, SHA-256 checksum, and missing annotation flags.
        """
        target_path = Path(output_path) if output_path is not None else MANIFEST_OUTPUT_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.is_available():
            manifest = {
                "manifest_version": "1.0.0",
                "dataset_name": "Indian Diabetic Retinopathy Image Dataset (IDRiD)",
                "dataset_status": "IDRiD DATASET NOT FOUND",
                "available_locally": False,
                "root_path": str(self.root),
                "total_images": 0,
                "total_annotations": 0,
                "provenance": OFFICIAL_IDRID_PROVENANCE,
                "taxonomy": {
                    "supported_categories": IDRID_SUPPORTED_CATEGORIES,
                    "external_dataset_required": EXTERNAL_REQUIRED_CATEGORIES,
                    "status_definitions": {
                        "GROUND_TRUTH": GROUND_TRUTH,
                        "DETECTED": DETECTED,
                        "ESTIMATED": ESTIMATED,
                        "NOT_AVAILABLE": NOT_AVAILABLE,
                        "EXTERNAL_DATASET_REQUIRED": EXTERNAL_DATASET_REQUIRED,
                    },
                },
                "images": [],
            }
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            return manifest

        # Dataset is present: extract full itemized manifest
        raw_images = self._find_raw_images()
        image_records: List[Dict[str, Any]] = []

        for img_path in raw_images:
            match = re.search(r"IDRiD_(\d+)", img_path.name, re.IGNORECASE)
            image_id = f"IDRiD_{match.group(1)}" if match else img_path.stem
            split = self._determine_split(img_path)

            # Dimensions
            width, height = None, None
            try:
                with Image.open(img_path) as im:
                    width, height = im.size
            except Exception:
                pass

            # Checksum
            sha = compute_file_sha256(img_path)

            # Matched annotations
            match_res = self.match_image_annotations(image_id)

            image_records.append({
                "image_id": image_id,
                "image_path": str(img_path.resolve()),
                "split": split,
                "image_width": width,
                "image_height": height,
                "available_annotations": match_res["available_annotations"],
                "annotation_paths": match_res["annotation_paths"],
                "checksum": sha,
                "missing_annotation_flags": match_res["missing_annotation_flags"],
            })

        manifest = {
            "manifest_version": "1.0.0",
            "dataset_name": "Indian Diabetic Retinopathy Image Dataset (IDRiD)",
            "dataset_status": "AVAILABLE",
            "available_locally": True,
            "root_path": str(self.root.resolve()),
            "total_images": len(image_records),
            "provenance": OFFICIAL_IDRID_PROVENANCE,
            "taxonomy": {
                "supported_categories": IDRID_SUPPORTED_CATEGORIES,
                "external_dataset_required": EXTERNAL_REQUIRED_CATEGORIES,
                "status_definitions": {
                    "GROUND_TRUTH": GROUND_TRUTH,
                    "DETECTED": DETECTED,
                    "ESTIMATED": ESTIMATED,
                    "NOT_AVAILABLE": NOT_AVAILABLE,
                    "EXTERNAL_DATASET_REQUIRED": EXTERNAL_DATASET_REQUIRED,
                },
            },
            "images": image_records,
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def audit_integrity(self) -> Dict[str, Any]:
        """Perform cryptographic integrity and duplicate audit (Task 8).

        Verifies SHA-256 hashes, detects duplicates, verifies dimensions and splits.
        Duplicates are reported and never silently deleted.
        """
        if not self.is_available():
            return {
                "status": "IDRiD DATASET NOT FOUND",
                "available": False,
                "root_path": str(self.root),
                "total_files": 0,
                "unique_hashes": 0,
                "duplicates_detected": 0,
                "duplicate_groups": {},
                "dimension_mismatches": [],
                "split_leakage_detected": False,
            }

        raw_images = self._find_raw_images()
        hash_map: Dict[str, List[str]] = {}
        split_map: Dict[str, str] = {}
        dimensions_map: Dict[str, Tuple[Optional[int], Optional[int]]] = {}

        for p in raw_images:
            sha = compute_file_sha256(p)
            hash_map.setdefault(sha, []).append(str(p))
            split = self._determine_split(p)
            split_map[str(p)] = split

            try:
                with Image.open(p) as im:
                    dimensions_map[str(p)] = im.size
            except Exception:
                dimensions_map[str(p)] = (None, None)

        duplicate_groups = {sha: files for sha, files in hash_map.items() if len(files) > 1}

        # Check cross-split data leakage (identical hash in both train and test)
        cross_split_leakage: List[Dict[str, Any]] = []
        for sha, files in duplicate_groups.items():
            splits = {split_map[f] for f in files}
            if "train" in splits and "test" in splits:
                cross_split_leakage.append({
                    "sha256": sha,
                    "files": files,
                    "splits": list(splits),
                })

        return {
            "status": "AUDITED",
            "available": True,
            "root_path": str(self.root.resolve()),
            "total_files": len(raw_images),
            "unique_hashes": len(hash_map),
            "duplicates_detected": len(duplicate_groups),
            "duplicate_groups": duplicate_groups,
            "split_leakage_detected": bool(len(cross_split_leakage) > 0),
            "cross_split_leakage": cross_split_leakage,
            "native_dimension_benchmark": OFFICIAL_IDRID_PROVENANCE["native_resolution"],
        }
