# Retinal Fundus Image Focus / Blur Assessment Report

## 1. Overview
- **Total Real Images Evaluated**: 9
- **Dataset Path**: `/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images`
- **Score Range**: [21.63, 88.87]
- **Median Score**: 57.21
- **Mean Score (Std)**: 49.72 (±24.05)
- **Decision Breakdown**: 5 Sharp, 2 Borderline, 2 Blurry

## 2. Engineering Baseline Thresholds
> [!IMPORTANT]
> Thresholds below are **engineering baseline heuristics** derived from observed feature variance across the real retinal sample images. They are **NOT clinically validated** by an ophthalmologist or clinical trials.

- **Blurry Threshold**: `< 25.0` (Images with low vascular gradient contrast)
- **Borderline Threshold**: `[25.0, 50.0)` (Moderate edge definition, eligible for enhancement)
- **Sharp Threshold**: `>= 50.0` (Clear microvascular margins and optic disc definition)

## 3. Individual Image Evaluation Results

| Filename | DR Grade / Metadata | Raw Laplacian Variance | Tenengrad Gradient Energy | Normalized Score (0-100) | Focus Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `aptos_train_sample_c10.png` | Grade 0 (APTOS Train Sample) | 22.72 | 896.67 | **21.63** | **Blurry** |
| `cell13_r0_c2_grade2.png` | Grade 2 (Moderate DR) | 24.19 | 1050.93 | **22.57** | **Blurry** |
| `cell13_r0_c0_grade0.png` | Grade 0 (No DR) | 28.45 | 1013.92 | **25.13** | **Borderline** |
| `cell13_r0_c1_grade1.png` | Grade 1 (Mild DR) | 40.12 | 1368.21 | **31.15** | **Borderline** |
| `cell13_r1_c0_grade2_dup.png` | Grade 2 (Moderate DR) | 139.73 | 4749.61 | **57.21** | **Sharp** |
| `cell13_r1_c1_grade3.png` | Grade 3 (Severe DR) | 154.76 | 4680.64 | **59.37** | **Sharp** |
| `cell13_r1_c2_grade4.png` | Grade 4 (Proliferative DR) | 173.10 | 6427.50 | **61.69** | **Sharp** |
| `aptos_eval_6959267_grade3.png` | Grade 3 (Severe DR) | 487.30 | 17861.41 | **79.83** | **Sharp** |
| `confirmed_grade4_proliferative.jpg` | Grade 4 (Proliferative DR) | 1093.43 | 16373.00 | **88.87** | **Sharp** |

## 4. Key Observations & Data Sanity Analysis
- **Highest Sharpness**: `confirmed_grade4_proliferative.jpg` (Score: 88.87, LapVar: 1093.43). Features high-contrast proliferative neovascularization and fibrous lesions.
- **Lowest Sharpness**: `aptos_train_sample_c10.png` (Score: 21.63, LapVar: 22.72). Features smooth, diffuse illumination with faint background vessel boundaries.
- **Metric Correlation**: Raw Laplacian variance and Tenengrad gradient energy correlate strongly across the cohort ($R > 0.90$), confirming that 2nd-derivative curvature and 1st-derivative edge energy agree on vascular transition steepness.
- **Dataset Diversity Limitation**: The current local real dataset contains 9 retinal images. While it successfully separates softer images from crisp, high-contrast proliferative cases, full clinical calibration across subtle boundary cases requires a broader expert-annotated blur cohort.

## 5. Artifacts Generated
- Machine-readable summary: `image_quality/results/focus/focus_results.json`
- Distribution bar chart: `image_quality/results/focus/focus_score_distribution.png`
- Per-image 4-panel visual evidence: `image_quality/results/focus/*_focus.png`