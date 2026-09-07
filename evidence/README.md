# Retinal Structure + Lesion Evidence Engine — Step 1 Architecture

## 1. Objective & Scope

This module establishes the foundational infrastructure for transforming generic Grad-CAM mathematical attribution into a genuine clinical retinal evidence layer.

### Core Integrity Invariants:
1. **Existing V2 Classifier Frozen**: `model/MODEL_V2_80pct_backup.keras` remains strictly frozen and untouched. Zero fine-tuning, zero weight modifications, no V3.
2. **Zero Synthetic / Mock Data**: No fabricated lesion masks, no synthetic retinal images, no fake metrics.
3. **Strict Epistemic Taxonomy**: Absolute runtime distinction between:
   - `GROUND_TRUTH`: Expert clinical annotations from certified benchmarks.
   - `DETECTED`: Candidate regions output by dedicated algorithmic detectors.
   - `ESTIMATED`: Heuristic or geometric anatomical approximations.
   - `NOT_AVAILABLE`: Channels missing from benchmark or unannotated.
   - `EXTERNAL_DATASET_REQUIRED`: Channels absent in IDRiD requiring external reference datasets.
4. **No Premature Training**: Model training (vessels, lesions, optic disc segmentation) is deferred to Google Colab GPU instances. Zero local retraining.

---

## 2. Target Evidence Categories & Ground-Truth Availability

| Evidence Channel | IDRiD Status | Annotation Type | Representation in Schema | Ground-Truth Dataset Strategy |
| :--- | :---: | :--- | :--- | :--- |
| **Optic Disc** | **AVAILABLE** | Part A (81 masks) & Part C (516 centers) | `PointLandmark` (center) & `SegmentationMask` | IDRiD Part C localization + Part A segmentation |
| **Fovea / Macula** | **AVAILABLE** | Part C (516 center coordinates) | `PointLandmark` (center, estimated radius) | IDRiD Part C localization |
| **Microaneurysms** | **AVAILABLE** | Part A (81 binary TIF masks) | `SegmentationMask` (discrete pixel mask) | IDRiD Part A segmentation (54 train, 27 test) |
| **Hard Exudates** | **AVAILABLE** | Part A (81 binary TIF masks) | `SegmentationMask` (discrete pixel mask) | IDRiD Part A segmentation |
| **Soft Exudates** | **AVAILABLE** | Part A (81 binary TIF masks) | `SegmentationMask` (discrete pixel mask) | IDRiD Part A segmentation |
| **Hemorrhages** | **AVAILABLE** | Part A (81 binary TIF masks) | `SegmentationMask` (discrete pixel mask) | IDRiD Part A segmentation |
| **Retinal Vessels** | **EXTERNAL_DATASET_REQUIRED** | Not annotated in IDRiD | `SegmentationMask` | External benchmark required (DRIVE, STARE, CHASE_DB1) |
| **Neovascularization** | **EXTERNAL_DATASET_REQUIRED** | Not annotated in IDRiD | `SegmentationMask` (status = `EXTERNAL_DATASET_REQUIRED`) | Specialized Proliferative DR cohort (e.g. DDR) required |

---

## 3. IDRiD Dataset Purpose & Provenance

- **Purpose**: High-resolution clinical benchmark for Diabetic Retinopathy lesion segmentation, disease grading, and optic disc/fovea localization from rural Indian clinical cohorts.
- **Official Source**: [IEEE DataPort - Indian Diabetic Retinopathy Image Dataset](https://ieee-dataport.org/open-access/indian-diabetic-retinopathy-image-dataset-idrid)
- **Official Challenge**: [IDRiD Grand Challenge](https://idrid.grand-challenge.org/)
- **Camera**: Kowa VX-10alpha digital fundus camera (50° field of view)
- **Native Resolution**: 4288 × 2848 pixels, 24-bit RGB JPEG

### Partition Breakdown:
- **Part A: Segmentation** (`557.25 MB`):
  - 81 images (54 training, 27 testing)
  - 5 ground-truth binary TIF mask categories: Microaneurysms, Haemorrhages, Hard Exudates, Soft Exudates, Optic Disc.
- **Part B: Disease Grading** (`202.57 MB`):
  - 516 images (413 training, 103 testing)
  - DR grades (0..4) and DME risk grades (0..2).
- **Part C: Localization** (`202.67 MB`):
  - 516 images (413 training, 103 testing)
  - Optic disc and fovea center coordinates $(X, Y)$ in pixel space.

---

## 4. Expected Dataset Locations & Mount Contracts

### Local Staging Path (Documented Default):
```
data/external/IDRiD/
data/external/DRIVE/
data/external/MESSIDOR2/
```
These directories remain completely empty when datasets are not locally mounted.

### Configurable Root Hierarchy:
The dataset root is dynamically resolved using the following strict priority:
1. **CLI Argument**: `--root /path/to/IDRiD` or `--idrid-root /path/to/IDRiD`
2. **Environment Variable**: `export IDRID_ROOT=/path/to/IDRiD`
3. **Configuration File**: `dataset_config.json` containing `{"IDRID_ROOT": "..."}`
4. **Google Colab Mount**: `/content/IDRiD` (auto-detected if present)
5. **Documented Default**: `data/external/IDRiD`

### Real-Data Safety & Missing-Data Behavior:
If the dataset root does not exist or contains no valid IDRiD images:
- Any dataset loader call raises `IDRiDNotFoundError`:
  ```
  IDRiD DATASET NOT FOUND
  ```
- **Safety Guarantee**: The loader will NEVER generate mock masks, fake annotations, or substitute APTOS data.

---

## 5. Google Colab Mounting Instructions

Colab handles GPU-accelerated training. The exact same dataset loader works seamlessly in both local and Colab environments.

### Step 1: Mount Google Drive or Extract Dataset
In a Google Colab notebook:
```python
# Option A: From Google Drive
from google.colab import drive
drive.mount('/content/drive')
!mkdir -p /content/IDRiD
!unzip -q "/content/drive/MyDrive/IDRiD/A. Segmentation.zip" -d /content/IDRiD/

# Option B: Set Environment Variable
import os
os.environ["IDRID_ROOT"] = "/content/IDRiD"
```

### Step 2: Audit Staged Data in Colab
```bash
python scripts/audit_idrid.py --root /content/IDRiD
```

---

## 6. Audit & Manifest Generation Commands

Run the automated manifest generator and integrity audit:

```bash
# Standard run (uses priority resolution)
python scripts/audit_idrid.py

# Explicit root run
python scripts/audit_idrid.py --root /path/to/IDRiD

# Output manifest location
# evidence/data/idrid_manifest.json
```

The manifest records:
- Image ID (e.g. `IDRiD_01`)
- Absolute file path
- Dataset split (`train` / `test`)
- Native image dimensions (`image_width`, `image_height`)
- Available annotations list
- Annotation paths dictionary
- SHA-256 cryptographic checksum
- Missing annotation flags per taxonomy category

---

## 7. Next Step: Google Colab Training Workflow

1. **Staging Verification**: Confirm `python scripts/audit_idrid.py --root /content/IDRiD` outputs `STATUS: IDRiD DATASET FOUND`.
2. **Patch Extraction**: Extract high-resolution $512 \times 512$ patches at native $3.5\ \mu\text{m}/\text{pixel}$ resolution for microaneurysms.
3. **Colab GPU Training**: Train U-Net / Attention U-Net models for:
   - Optic disc segmentation (Part A + Part C)
   - Exudate segmentation (Hard + Soft exudates)
   - Hemorrhage segmentation
4. **Checkpoint Export**: Transfer trained model checkpoints back to project repository for integration and evaluation against frozen V2 baseline.
