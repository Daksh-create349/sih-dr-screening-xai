# APTOS 2019 Dataset Recovery & Integrity Audit Report

**Dataset Name**: APTOS 2019 Blindness Detection
**Protocol Version**: 1.1.0
**Dataset Status**: `BLOCKED`
**Full Labelled APTOS Available**: `False`
**Download Used**: `0.0 MB` (Hard limit: `500.0 MB`)
**Available Free Disk Space**: `38.83 GB` (`39759.12 MB`)

---

## 1. Executive Status

> [!WARNING]
> **BLOCKED**: Full labelled APTOS dataset unavailable and required source exceeds the 500 MB limit.
> 
> - **Local Search**: Exhaustive local search found only integration test images and model checkpoints; no labelled evaluation split (`valid.csv`/`test.csv`) was found.
> - **Authentic Source Audit**: Canonical APTOS archives exceed the strict 500 MB download limit.
> - **Safety Rule Enforced**: Downloads > 500 MB are refused.
> - **Clinical Safety Rule**: 9 local integration test images are NOT used as a substitute for the clinical benchmark.

## 2. Discovered Local Assets

| File Name | File Type | Size (MB) | Labels Present | Path |
| :--- | :--- | :--- | :--- | :--- |
| `aptos_eval_6959267_grade3.png` | `image` | 0.367 | `False` | `/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images/aptos_eval_6959267_grade3.png` |
| `aptos_train_sample_c10.png` | `image` | 0.159 | `False` | `/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images/aptos_train_sample_c10.png` |
| `Diabetic_retinopathy.ipynb` | `jupyter_notebook` | 3.509 | `False` | `/Users/dakshsrivastava/Desktop/Diabetic-Retinopathy-Trained/Diabetic_retinopathy.ipynb` |
| `best_aptos_model.keras` | `model_weights` | 50.058 | `False` | `/Users/dakshsrivastava/Downloads/best_aptos_model.keras` |

## 3. Discovered Splits Audit

| Split | CSV | Directory | Records | Resolved | Missing | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | *Not found* | *Not found* | 0 | 0 | 0 | `BLOCKED` |

## 4. Resource & Download Limit Verification

- **Cumulative Download Used**: `0.0 MB`
- **Hard Download Limit**: `500.0 MB`
- **Download Limit Respected**: `True`
- **Available Storage**: `38.83 GB`
- **Cross-Split Leakage**: `False`

## 5. Authentic Source Evaluation

| Candidate | Platform | Size | 500 MB Limit Check | Decision |
| :--- | :--- | :--- | :--- | :--- |
| `aptos2019-blindness-detection` | Kaggle | ~9.5 GB | Exceeds 500 MB | **REFUSED** |
| `mariaherrerot/aptos2019` | Hugging Face | ~6.83 GB | Exceeds 500 MB | **REFUSED** |

## 6. Historical Reference Targets

- Historical Train Count: ~2,930
- Historical Validation Count: ~366
- Historical Test Count: ~366
- Historical Total: ~3,662

---

## 7. Next Actions

1. Clinical validation benchmark remains **BLOCKED** due to dataset unavailability.
2. Integration test pipeline remains 100% operational with 9 verified retinal images.
3. If external transfer is required, dataset must be mounted locally without exceeding workstation download limits.
