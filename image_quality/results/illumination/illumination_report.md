# Retinal Fundus Image Illumination & Exposure Assessment Report

## 1. Overview
- **Total Real Images Evaluated**: 9
- **Dataset Path**: `/Users/dakshsrivastava/Desktop/DR /data/real_retinal_images`
- **Overall Score Range**: [55.02, 87.99]
- **Median Overall Score**: 75.55
- **Mean Overall Score (Std)**: 74.28 (±8.82)
- **Mean Foreground Luminance Range**: [70.32, 144.06] (Median: 105.08)
- **Decision Breakdown**: 8 Well Illuminated, 1 Borderline Illumination, 0 Poor Illumination

## 2. Engineering Baseline Thresholds & Rationale
> [!IMPORTANT]
> Thresholds below are **engineering baseline heuristics** derived from observed retinal fundus distributions. They are **NOT clinically validated** by an ophthalmologist or clinical trial protocol.

- **Optimal Mean Target**: ~115.0 on 8-bit scale [0, 255]. Retinal tissue typically displays healthy vascular and macula detail in the 80 - 150 luminance window.
- **Dark Pixel Cutoff**: Intensity `< 30.0` within foreground mask.
- **Bright Pixel Cutoff**: Intensity `> 220.0` within foreground mask (detects specular reflections and glare).
- **Poor Illumination**: Overall Score `< 45.0` or severe clipping (> 20% dark or > 15% bright).
- **Borderline Illumination**: Overall Score `[45.0, 65.0)`.
- **Well Illuminated**: Overall Score `>= 65.0`.

## 3. Individual Image Evaluation Results

| Filename | DR Grade | Mean (Median) | Dark % (<30) | Bright % (>220) | Uniformity Score | Exposure Score | Overall Illum Score | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cell13_r1_c1_grade3.png` | Grade 3 (Severe DR) | 70.3 (67.0) | 0.2% | 1.4% | 55.6 | 54.5 | **55.0** | **Borderline Illumination** |
| `aptos_eval_6959267_grade3.png` | Grade 3 (Severe DR) | 144.1 (148.0) | 0.4% | 1.7% | 66.8 | 70.4 | **68.8** | **Well Illuminated** |
| `cell13_r0_c2_grade2.png` | Grade 2 (Moderate DR) | 85.8 (85.0) | 0.4% | 0.1% | 59.5 | 78.9 | **70.2** | **Well Illuminated** |
| `confirmed_grade4_proliferative.jpg` | Grade 4 (Proliferative DR) | 142.4 (143.0) | 0.4% | 1.5% | 75.7 | 73.3 | **74.4** | **Well Illuminated** |
| `cell13_r0_c0_grade0.png` | Grade 0 (No DR) | 78.3 (79.0) | 0.2% | 0.0% | 81.2 | 71.0 | **75.5** | **Well Illuminated** |
| `cell13_r1_c0_grade2_dup.png` | Grade 2 (Moderate DR) | 105.1 (100.0) | 0.4% | 1.7% | 64.7 | 84.9 | **75.8** | **Well Illuminated** |
| `cell13_r1_c2_grade4.png` | Grade 4 (Proliferative DR) | 119.9 (114.0) | 0.3% | 2.1% | 69.3 | 84.3 | **77.6** | **Well Illuminated** |
| `aptos_train_sample_c10.png` | Grade 0 (APTOS Train Sample) | 91.8 (91.0) | 0.2% | 0.0% | 79.1 | 86.5 | **83.2** | **Well Illuminated** |
| `cell13_r0_c1_grade1.png` | Grade 1 (Mild DR) | 106.8 (105.0) | 0.4% | 0.0% | 77.8 | 96.3 | **88.0** | **Well Illuminated** |

## 4. Key Observations & Data Sanity Analysis
- **Highest Illumination Score**: `cell13_r0_c1_grade1.png` (Overall: 88.0, Mean: 106.8, Uniformity: 77.8). Features balanced exposure across all 4 quadrants with zero saturated pixels.
- **Lowest Illumination Score / Borderline**: `cell13_r1_c1_grade3.png` (Overall: 55.0, Mean: 70.3, Exposure Score: 54.5). The retinal field is notably darker (mean 70.3, 5th percentile 46.0), causing reduced exposure score.
- **Zero Poor Illumination in Cohort**: None of the 9 images in this training/validation subset suffered from total dark blackout or severe overexposed glare flashes; all were clinically gradable in the classifier dataset.
- **Black Background Isolation**: The circular camera aperture borders are completely isolated by foreground masking, ensuring dark background border pixels never falsely drag down exposure or uniformity calculations.

## 5. Artifacts Generated
- Machine-readable summary: `image_quality/results/illumination/illumination_results.json`
- Score distribution plot: `image_quality/results/illumination/illumination_score_distribution.png`
- Per-image 4-panel visual evidence: `image_quality/results/illumination/*_illumination.png`