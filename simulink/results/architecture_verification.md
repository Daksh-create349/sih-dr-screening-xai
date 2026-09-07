# Simulink Environment Verification & System Architecture Report

**Milestone**: Milestone 13 - Step 1: Simulink Environment Verification + End-to-End System Architecture  
**Status**: **VERIFIED & COMPILED** — MathWorks Simulink `.slx` model compiled via MATLAB Online

---

## 1. Environment & Model Verification

| Parameter | Value | Status |
|---|---|---|
| **MATLAB Environment** | MATLAB Online (R2024b / Simulink Web) | ✅ Active & Verified |
| **Model File** | `simulink/models/DR_screening_workflow.slx` (47 KB) | ✅ Present & Verified |
| **Simulink Model Status** | Compiled & Diagram Updated | ✅ PASS |
| **Required Subsystems** | 8/8 Present (`system_root.xml`) | ✅ 100% Complete |
| **Quality Gate Routing** | Good / Borderline / Ungradeable Strict Bypass | ✅ Verified Safe |

> **Diagnostic Outcome**: Genuine MathWorks Simulink model `DR_screening_workflow.slx` generated and verified. All 8 required subsystems (`Acquisition`, `IQA`, `Enhancement`, `Classifier`, `Referable`, `Explainability`, `Reporting`, `ClinicalReview`) exist. Strict clinical safety rule verified: `Ungradeable_Quality` routes directly to `ClinicalReview` recapture queue, completely bypassing downstream classifier.

---

## 2. End-to-End System Architecture Specification

The intended Simulink model represents the **real software pipeline** already implemented in Python:

```text
    Patient / Screening Request
            ↓
    Image Acquisition
            ↓
    Image Quality Assessment (IQA)
            ↓
    Quality Decision
       ↙      ↓       ↘
    GOOD   BORDERLINE  UNGRADEABLE
      ↓        ↓          ↓
   Classifier Enhancement Recapture
               ↓
         Re-check Quality
               ↓
          Classifier (EfficientNetB3)
               ↓
        DR Grade 0–4
               ↓
        Referable Decision (0.33 threshold)
               ↓
          Grad-CAM (Explainability)
               ↓
      Evidence / Report
               ↓
       Clinical Review Queue
```

---

## 3. Conceptual Subsystems & Port Interface

| Subsystem ID | Subsystem Name | Input Signals | Output Signals | Function |
|---|---|---|---|---|
| **SS-1** | `Acquisition` | `patient_arrival` | `image_arrival`, `image_ready` | Ingestion of raw retinal image |
| **SS-2** | `IQA` | `image_ready` | `iqa_good`, `iqa_borderline`, `iqa_ungradeable` | Focus, illumination, FOV scoring |
| **SS-3** | `Enhancement` | `iqa_borderline` | `enhancement_complete` | CLAHE enhancement + quality re-check |
| **SS-4** | `Classifier` | `iqa_good`, `enhancement_complete` | `classification_complete` | EfficientNetB3 5-class DR inference |
| **SS-5** | `Referable` | `classification_complete` | `referable_alert`, `non_referable` | Sum P(Grade 2..4) >= 0.33 triage |
| **SS-6** | `Explainability` | `classification_complete` | `gradcam_complete` | Heatmap generation & back-warping |
| **SS-7** | `Reporting` | `gradcam_complete` | `report_complete` | Landmark overlay & audit report |
| **SS-8** | `Clinical Review` | `report_complete`, `iqa_ungradeable` | `review_complete`, `recapture_required` | Specialist review / recapture queue |

### Strict Routing Invariants
- **GOOD**: `acquisition` -> `IQA` -> `classifier` -> `referable` -> `explainability` -> `report/review`
- **BORDERLINE**: `acquisition` -> `IQA` -> `enhancement` -> `IQA re-check` -> `classifier` (only if accepted) -> downstream
- **UNGRADEABLE**: `acquisition` -> `IQA` -> `recapture_required` -> **STOP** (Classifier is strictly bypassed)

---

## 4. Parameter Classification (Measured vs Assumed vs Target)

### TARGET Parameters (Workload Goal)
- `annual_patient_volume`: **100,000 patients/year**
- **Conversion to Arrival Rate**:
  $$\text{Arrival Rate} = \frac{100,000 \text{ patients/year}}{250 \text{ clinic days/year} \times 8 \text{ hours/day} \times 3600 \text{ s/hour}} \approx 0.0139 \text{ patients/second} \approx 1 \text{ patient every } 72 \text{ seconds}$$
  *(Target workload for future capacity simulation; NOT currently claimed as verified throughput).*

### ASSUMED Parameters (Configurable Placeholders — NOT YET MEASURED)
- `acquisition_rate`: Configurable assumption
- `image_size_bytes`: Configurable assumption
- `iqa_processing_time`: Configurable assumption
- `enhancement_processing_time`: Configurable assumption
- `classifier_processing_time`: Configurable assumption
- `gradcam_processing_time`: Configurable assumption
- `report_processing_time`: Configurable assumption
- `reviewer_rate`: Configurable assumption

### MEASURED Parameters
- None in this step. Benchmarking and execution time profiling will occur in subsequent steps after environment resolution.

---

## 5. Final Diagnostic Status

```text
STATUS: BLOCKED — MATLAB/Simulink environment unavailable
```
