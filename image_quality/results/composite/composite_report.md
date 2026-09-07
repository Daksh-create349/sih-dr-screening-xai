# Milestone 5: Composite Image Quality Scoring and Decision Classification Report

## 1. Executive Summary

This report documents the implementation and real-dataset evaluation for **Milestone 5: Composite Image Quality Scoring and Decision Classification** of the retinal Image Quality Assessment (IQA) system for diabetic retinopathy screening.

All evaluations were executed on the **9 real retinal fundus images** in `data/real_retinal_images/`. Zero mock data, synthetic blurs, or fabricated metrics were used.

### Overall Classification Summary (N=9):
- **GOOD**: 4 (44.4%) — Proceed immediately to DR classification inference.
- **BORDERLINE**: 5 (55.6%) — Automated enhancement recommended prior to DR classification.
- **UNGRADEABLE**: 0 (0.0%) — Reject image and request recapture.

---

## 2. Methodology & Engineering Design

### A. Dimensional Weighting Method

Independent dimensional metrics are weighted according to optical and clinical engineering rationale:

```text
Composite Score = 0.40 * Focus + 0.30 * Illumination + 0.20 * FOV + 0.10 * Centering
```

| Dimension | Metric Source | Weight (w) | Engineering Rationale |
| :--- | :--- | :--- | :--- |
| **Focus / Sharpness** | `image_quality.focus` | **0.40** (40%) | Critical driver for resolving subtle microaneurysms (<30µm), intraretinal hemorrhages, and fine vessel bifurcations. Defocus cannot be fully restored by downstream networks. |
| **Illumination / Exposure** | `image_quality.illumination` | **0.30** (30%) | Determines lesion visibility against background retina, signal-to-noise ratio, and absence of shadow or glare saturation. |
| **Field of View (FOV)** | `image_quality.field_of_view` | **0.20** (20%) | Verifies adequate posterior pole coverage (standard clinical standard requires >= 75% coverage of sensor mask). |
| **Retinal Centering** | `image_quality.field_of_view` | **0.10** (10%) | Ensures macula and posterior pole reside within the central diagnostic frame without edge truncation. |
| **Optic Disc Localization** | `image_quality.field_of_view` | **Tracked** (0%) | Tracked in diagnostics for anatomical verification, but deliberately excluded from primary acquisition scoring so valid macula-centered photography is not penalized. |

### B. Minimum Hard Quality Gates

A composite average alone is dangerous: an image with pristine illumination and FOV could achieve an average $>70.0$ despite severe defocus that obscures all retinopathy lesions. Hard quality gates prevent false "GOOD" classifications:

1. **UNGRADEABLE Gates (Forces Immediate Rejection & Recapture)**:
   - **Severe Blur**: Focus Score $< 15.0$
   - **Severe Illumination Defect**: Illumination Score $< 35.0$
   - **Severe Clipping**: Dark pixels $> 50.0\%$ or Glare pixels $> 30.0\%$
   - **Severe FOV Truncation**: FOV Score $< 40.0$
   - **Severe Off-Centering**: Centering Score $< 30.0$
   - **Composite Floor**: Composite Score $< 45.0$

2. **BORDERLINE Gates (Forces Enhancement Routing)**:
   - **Soft Focus Gate**: Focus Score $< 50.0$
   - **Sub-optimal Illumination Gate**: Illumination Score $< 65.0$
   - **Marginal FOV Gate**: FOV Score $< 75.0$
   - **Sub-optimal Centering Gate**: Centering Score $< 70.0$
   - **Composite Score Gate**: Composite Score $< 70.0$

3. **GOOD Acceptance Criteria**:
   - Composite Score $\ge 70.0$ **AND** Zero Quality Gates Triggered.

---

## 3. Real Retinal Dataset Evaluation Table

Evaluated on all 9 real retinal images from `data/real_retinal_images/`:

| Filename | Clinical DR Grade | Focus (40%) | Illum (30%) | FOV (20%) | Center (10%) | Composite Score | Final Decision | Triggered Quality Gates | Recommended Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `confirmed_grade4_proliferative.jpg` | Grade 4 (Proliferative DR) | 88.9 | 74.4 | 93.4 | 98.8 | **86.42** | **GOOD** | None (Clean) | Proceed to DR classification. |
| `aptos_eval_6959267_grade3.png` | Grade 3 (Severe DR) | 79.8 | 68.8 | 100.0 | 93.5 | **81.90** | **GOOD** | None (Clean) | Proceed to DR classification. |
| `cell13_r1_c0_grade2_dup.png` | Grade 2 (Moderate DR) | 57.2 | 75.8 | 100.0 | 97.8 | **75.42** | **GOOD** | None (Clean) | Proceed to DR classification. |
| `cell13_r1_c2_grade4.png` | Grade 4 (Proliferative DR) | 61.7 | 77.6 | 92.6 | 76.7 | **74.14** | **GOOD** | None (Clean) | Proceed to DR classification. |
| `cell13_r1_c1_grade3.png` | Grade 3 (Severe DR) | 59.4 | 55.0 | 100.0 | 97.5 | **70.00** | **BORDERLINE** | suboptimal_illumination | Enhancement recommended before DR classification. |
| `cell13_r0_c1_grade1.png` | Grade 1 (Mild DR) | 31.1 | 88.0 | 100.0 | 99.4 | **68.80** | **BORDERLINE** | suboptimal_focus; composite_below_good | Enhancement recommended before DR classification. |
| `aptos_train_sample_c10.png` | Grade 0 (APTOS Train Sample) | 21.6 | 83.2 | 100.0 | 96.5 | **63.25** | **BORDERLINE** | suboptimal_focus; composite_below_good | Enhancement recommended before DR classification. |
| `cell13_r0_c0_grade0.png` | Grade 0 (No DR) | 25.1 | 75.5 | 100.0 | 97.6 | **62.48** | **BORDERLINE** | suboptimal_focus; composite_below_good | Enhancement recommended before DR classification. |
| `cell13_r0_c2_grade2.png` | Grade 2 (Moderate DR) | 22.6 | 70.2 | 100.0 | 98.8 | **59.97** | **BORDERLINE** | suboptimal_focus; composite_below_good | Enhancement recommended before DR classification. |

---

## 4. Cohort Score Statistics

- **Minimum Composite Score**: 59.97 (`cell13_r0_c2_grade2.png`)
- **Maximum Composite Score**: 86.42 (`confirmed_grade4_proliferative.jpg`)
- **Median Composite Score**: 70.00
- **Mean Composite Score**: 71.38
- **Standard Deviation**: 8.46

### Breakdown of Decision Drivers in Real Cohort:
- **4 Images Classified as GOOD**:
  - `confirmed_grade4_proliferative.jpg` (86.42): Focus 88.9, Illum 74.4, FOV 93.4, Centering 98.8. Clean pass across all quality gates.
  - `aptos_eval_6959267_grade3.png` (81.90): Focus 79.8, Illum 68.8, FOV 100.0, Centering 93.5. Clean pass across all quality gates.
  - `cell13_r1_c0_grade2_dup.png` (75.42): Focus 57.2, Illum 75.8, FOV 100.0, Centering 97.8. Clean pass across all quality gates.
  - `cell13_r1_c2_grade4.png` (74.14): Focus 61.7, Illum 77.6, FOV 92.6, Centering 76.7. Clean pass across all quality gates.
- **5 Images Classified as BORDERLINE**:
  - `cell13_r1_c1_grade3.png` (70.00): Focus 59.4, Illum 55.0, FOV 100.0, Centering 97.5. Triggered: suboptimal_illumination.
  - `cell13_r0_c1_grade1.png` (68.80): Focus 31.1, Illum 88.0, FOV 100.0, Centering 99.4. Triggered: suboptimal_focus; composite_below_good.
  - `aptos_train_sample_c10.png` (63.25): Focus 21.6, Illum 83.2, FOV 100.0, Centering 96.5. Triggered: suboptimal_focus; composite_below_good.
  - `cell13_r0_c0_grade0.png` (62.48): Focus 25.1, Illum 75.5, FOV 100.0, Centering 97.6. Triggered: suboptimal_focus; composite_below_good.
  - `cell13_r0_c2_grade2.png` (59.97): Focus 22.6, Illum 70.2, FOV 100.0, Centering 98.8. Triggered: suboptimal_focus; composite_below_good.
- **0 Images Classified as UNGRADEABLE**:
  - None. Consistent with cohort provenance: all 9 images were sourced from diagnostic archives viable for screening evaluation. None suffered from catastrophic optical failure (<15 focus or <35 illumination).

---

## 5. Limitations & Engineering Assumptions

1. **Dataset Size (N=9)**:
   While all 9 images are authentic clinical fundus photographs covering Diabetic Retinopathy Grades 0 through 4, a 9-image cohort is insufficient to establish statistically definitive, clinically validated cutoffs.
2. **Threshold Categorization**:
   The decision thresholds ($70.0$ for Good, $45.0$ for Ungradeable floor, $50.0$ for focus gate, $65.0$ for illumination gate) are **engineering heuristic baselines** derived from signal processing metrics. They have not undergone multi-center clinical validation trials.
3. **Optic Disc Confidence Exclusion**:
   Optic disc candidate confidence is tracked for anatomical contextualization but excluded from primary acquisition scoring because macula-centered photography standardly offsets the optic disc toward the temporal edge.
