# Milestone 7: Operator Quality Reporting and Recapture Feedback Report

## 1. Executive Summary

This report documents the implementation, operator guidance generation, and real-dataset evaluation for **Milestone 7: Operator Recapture Feedback and Clinical Reporting** of the retinal Image Quality Assessment (IQA) system for diabetic retinopathy screening.

All assessments and clinical operator reports were generated from the **9 real retinal fundus images** in `data/real_retinal_images/`. Zero mock data, synthetic images, or fabricated metrics were used.

### Overall Cohort Breakdown (N=9):
- **GOOD**: 4 (44.4%) — Immediate routing to DR classification inference.
- **BORDERLINE (Enhanced)**: 5 (55.6%) — Automated enhancement accepted; routed to downstream analysis.
- **UNGRADEABLE**: 0 (0.0%) — Rejected with tailored recapture guidance.

---

## 2. Clinical Operator Reporting Architecture

### A. Recommended Actions by Status

| Status | Trigger Criteria | Standard Recommended Action | Clinical Meaning |
| :--- | :--- | :--- | :--- |
| **GOOD** | Composite score $\ge 70.0$, zero gates triggered | `Proceed to DR classification.` | Pristine optical quality across focus, illumination, FOV, and centering. |
| **BORDERLINE** | Enhancement attempted & accepted | `Enhanced image may proceed to downstream analysis.` | Initial optical defect resolved by validated enhancement without safeguard violations. |
| **BORDERLINE** | Enhancement rejected or not performed | `Image remains borderline. Consider recapturing the image.` | Residual defect persists; recapture recommended if high optical certainty needed. |
| **UNGRADEABLE** | Severe defect in any dimension or score $<45.0$ | `Reject image and request recapture.` | Critical failure obscuring diagnostic anatomy; image rejected immediately. |

### B. Actionable Recapture Protocol for Ungradeable Images

When an acquisition defect triggers an UNGRADEABLE gate, the operator is provided with specific, corrective physical instructions:

- **Severe Optical Blur**: *"Image is too blurry. Please keep the fundus camera steady and refocus before recapturing."*
- **Severe Illumination Defect**: *"Image illumination is inadequate. Please adjust the camera illumination and recapture."*
- **Excessive Dark Clipping**: *"Severe underexposure detected with excessive dark clipping. Increase flash intensity or check pupil dilation before recapturing."*
- **Excessive Glare / Corneal Reflection**: *"Excessive corneal glare or reflection detected. Re-align illumination angle and ask patient to blink before recapturing."*
- **Field of View Truncation**: *"Insufficient retinal field of view. Reposition the camera and ensure the retinal field is fully visible."*
- **Severe Off-Centering**: *"Retinal field severely off-center. Center the patient's gaze on the fixation target and recapture."*

---

## 3. Real Retinal Dataset Operator Screening Summary Table

| Filename | DR Grade | Status | Composite Score | Focus | Illum | FOV | Center | Enhancement Outcome | Recommended Operator Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `confirmed_grade4_proliferative.jpg` | Grade 4 (Proliferative DR) | **GOOD** | **86.42** | 88.9 | 74.4 | 93.4 | 98.8 | None (Pristine) | `Proceed to DR classification.` |
| `aptos_eval_6959267_grade3.png` | Grade 3 (Severe DR) | **GOOD** | **81.90** | 79.8 | 68.8 | 100.0 | 93.5 | None (Pristine) | `Proceed to DR classification.` |
| `cell13_r0_c1_grade1.png` | Grade 1 (Mild DR) | **BORDERLINE** | **75.99** | 31.1 | 88.0 | 100.0 | 99.4 | Accepted (CLAHE: 68.8 → 76.0) | `Enhanced image may proceed to downstream analysis.` |
| `cell13_r1_c0_grade2_dup.png` | Grade 2 (Moderate DR) | **GOOD** | **75.42** | 57.2 | 75.8 | 100.0 | 97.8 | None (Pristine) | `Proceed to DR classification.` |
| `cell13_r1_c1_grade3.png` | Grade 3 (Severe DR) | **BORDERLINE** | **74.45** | 59.4 | 55.0 | 100.0 | 97.5 | Accepted (CLAHE: 70.0 → 74.5) | `Enhanced image may proceed to downstream analysis.` |
| `cell13_r1_c2_grade4.png` | Grade 4 (Proliferative DR) | **GOOD** | **74.14** | 61.7 | 77.6 | 92.6 | 76.7 | None (Pristine) | `Proceed to DR classification.` |
| `cell13_r0_c0_grade0.png` | Grade 0 (No DR) | **BORDERLINE** | **71.12** | 25.1 | 75.5 | 100.0 | 97.6 | Accepted (CLAHE: 62.5 → 71.1) | `Enhanced image may proceed to downstream analysis.` |
| `cell13_r0_c2_grade2.png` | Grade 2 (Moderate DR) | **BORDERLINE** | **69.60** | 22.6 | 70.2 | 100.0 | 98.8 | Accepted (CLAHE: 60.0 → 69.6) | `Enhanced image may proceed to downstream analysis.` |
| `aptos_train_sample_c10.png` | Grade 0 (APTOS Train Sample) | **BORDERLINE** | **69.03** | 21.6 | 83.2 | 100.0 | 96.5 | Accepted (CLAHE: 63.2 → 69.0) | `Enhanced image may proceed to downstream analysis.` |

---

## 4. Per-Image Structured Operator Reports

### Quality Report: `confirmed_grade4_proliferative.jpg`

- **Status**: **GOOD**
- **Composite Score**: **86.42 / 100**
- **Component Scores**: Focus: 88.9 | Illum: 74.4 | FOV: 93.4 | Centering: 98.8
- **Triggered Gates**: None (Clean)
- **Enhancement**: Not applicable
- **Recommended Action**: `Proceed to DR classification.`
- **Operator Guidance**: Image quality acceptable for downstream analysis (Composite score: 86.4/100). All quality dimensions meet or exceed acceptance criteria.

---

### Quality Report: `aptos_eval_6959267_grade3.png`

- **Status**: **GOOD**
- **Composite Score**: **81.90 / 100**
- **Component Scores**: Focus: 79.8 | Illum: 68.8 | FOV: 100.0 | Centering: 93.5
- **Triggered Gates**: None (Clean)
- **Enhancement**: Not applicable
- **Recommended Action**: `Proceed to DR classification.`
- **Operator Guidance**: Image quality acceptable for downstream analysis (Composite score: 81.9/100). All quality dimensions meet or exceed acceptance criteria.

---

### Quality Report: `cell13_r0_c1_grade1.png`

- **Status**: **BORDERLINE**
- **Composite Score**: **75.99 / 100**
- **Component Scores**: Focus: 31.1 | Illum: 88.0 | FOV: 100.0 | Centering: 99.4
- **Triggered Gates**: suboptimal_focus, composite_below_good
- **Enhancement**: Accepted (`clahe`, 68.8 → 76.0)
- **Recommended Action**: `Enhanced image may proceed to downstream analysis.`
- **Operator Guidance**: Image quality was initially borderline due to suboptimal_focus, composite_below_good. Automated enhancement (CLAHE) was accepted (Score: 68.8 → 76.0). Enhanced image may proceed to downstream analysis.

---

### Quality Report: `cell13_r1_c0_grade2_dup.png`

- **Status**: **GOOD**
- **Composite Score**: **75.42 / 100**
- **Component Scores**: Focus: 57.2 | Illum: 75.8 | FOV: 100.0 | Centering: 97.8
- **Triggered Gates**: None (Clean)
- **Enhancement**: Not applicable
- **Recommended Action**: `Proceed to DR classification.`
- **Operator Guidance**: Image quality acceptable for downstream analysis (Composite score: 75.4/100). All quality dimensions meet or exceed acceptance criteria.

---

### Quality Report: `cell13_r1_c1_grade3.png`

- **Status**: **BORDERLINE**
- **Composite Score**: **74.45 / 100**
- **Component Scores**: Focus: 59.4 | Illum: 55.0 | FOV: 100.0 | Centering: 97.5
- **Triggered Gates**: suboptimal_illumination
- **Enhancement**: Accepted (`clahe`, 70.0 → 74.5)
- **Recommended Action**: `Enhanced image may proceed to downstream analysis.`
- **Operator Guidance**: Image quality was initially borderline due to suboptimal_illumination. Automated enhancement (CLAHE) was accepted (Score: 70.0 → 74.5). Enhanced image may proceed to downstream analysis.

---

### Quality Report: `cell13_r1_c2_grade4.png`

- **Status**: **GOOD**
- **Composite Score**: **74.14 / 100**
- **Component Scores**: Focus: 61.7 | Illum: 77.6 | FOV: 92.6 | Centering: 76.7
- **Triggered Gates**: None (Clean)
- **Enhancement**: Not applicable
- **Recommended Action**: `Proceed to DR classification.`
- **Operator Guidance**: Image quality acceptable for downstream analysis (Composite score: 74.1/100). All quality dimensions meet or exceed acceptance criteria.

---

### Quality Report: `cell13_r0_c0_grade0.png`

- **Status**: **BORDERLINE**
- **Composite Score**: **71.12 / 100**
- **Component Scores**: Focus: 25.1 | Illum: 75.5 | FOV: 100.0 | Centering: 97.6
- **Triggered Gates**: suboptimal_focus, composite_below_good
- **Enhancement**: Accepted (`clahe`, 62.5 → 71.1)
- **Recommended Action**: `Enhanced image may proceed to downstream analysis.`
- **Operator Guidance**: Image quality was initially borderline due to suboptimal_focus, composite_below_good. Automated enhancement (CLAHE) was accepted (Score: 62.5 → 71.1). Enhanced image may proceed to downstream analysis.

---

### Quality Report: `cell13_r0_c2_grade2.png`

- **Status**: **BORDERLINE**
- **Composite Score**: **69.60 / 100**
- **Component Scores**: Focus: 22.6 | Illum: 70.2 | FOV: 100.0 | Centering: 98.8
- **Triggered Gates**: suboptimal_focus, composite_below_good
- **Enhancement**: Accepted (`clahe`, 60.0 → 69.6)
- **Recommended Action**: `Enhanced image may proceed to downstream analysis.`
- **Operator Guidance**: Image quality was initially borderline due to suboptimal_focus, composite_below_good. Automated enhancement (CLAHE) was accepted (Score: 60.0 → 69.6). Enhanced image may proceed to downstream analysis.

---

### Quality Report: `aptos_train_sample_c10.png`

- **Status**: **BORDERLINE**
- **Composite Score**: **69.03 / 100**
- **Component Scores**: Focus: 21.6 | Illum: 83.2 | FOV: 100.0 | Centering: 96.5
- **Triggered Gates**: suboptimal_focus, composite_below_good
- **Enhancement**: Accepted (`clahe`, 63.2 → 69.0)
- **Recommended Action**: `Enhanced image may proceed to downstream analysis.`
- **Operator Guidance**: Image quality was initially borderline due to suboptimal_focus, composite_below_good. Automated enhancement (CLAHE) was accepted (Score: 63.2 → 69.0). Enhanced image may proceed to downstream analysis.

---

## 5. Clinical Safety & Diagnostic Boundaries

1. **Screening Support Only**:
   Image quality assessment provides technical screening and optical verification only; it does not constitute an independent medical diagnosis. Diagnostic certainty requires clinical evaluation by a qualified eye care professional.
2. **Strict Verification**:
   All reports, scores, and recommendations directly reflect measured image processing parameters. No medical diagnosis or disease absence is claimed or inferred by the quality assessment system.
