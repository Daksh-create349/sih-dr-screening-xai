# Simulink Workflow Simulation for Diabetic Retinopathy Screening

## 1. System Purpose
Models the end-to-end operational workflow of the clinical Diabetic Retinopathy (DR) screening system at a macro systems level:
- Ingestion and acquisition of retinal fundus images.
- Upstream Image Quality Assessment (IQA) gating.
- Automated enhancement for borderline quality images.
- Re-capture queue routing for ungradeable images (strictly bypassing inference).
- Deep learning classifier inference (EfficientNetB3) for 5-class DR grading.
- Calibrated binary referable DR clinical screening triage (threshold = 0.33).
- Explainability layer (Grad-CAM localization and anatomical landmark reporting).
- Clinical ophthalmologist review queue and latency analysis.

---

## 2. Subsystem Architecture & Signal Flow

```text
                     [Patient Arrival]
                             │
                             ▼
                    ┌─────────────────┐
                    │ 1. Acquisition  │
                    └────────┬────────┘
                             │ image_arrival, image_ready
                             ▼
                    ┌─────────────────┐
                    │     2. IQA      │
                    └────────┬────────┘
        ┌────────────────────┼────────────────────┐
        │ iqa_good           │ iqa_borderline     │ iqa_ungradeable
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ 4. Classifier │   │ 3. Enhancement  │   │ Recapture Queue │
└───────┬───────┘   └────────┬────────┘   └────────┬────────┘
        │                    │ enhancement_complete│ recapture_required
        │                    ▼                     ▼
        │             Quality Re-check           [STOP]
        │                    │
        │                    ▼ (if accepted)
        │           ┌─────────────────┐
        └──────────>│ 4. Classifier   │
                    └────────┬────────┘
                             │ classification_complete
                             ▼
                    ┌─────────────────┐
                    │  5. Referable   │
                    └────────┬────────┘
                             │ referable_alert / non_referable
                             ▼
                    ┌─────────────────┐
                    │6. Explainability│
                    └────────┬────────┘
                             │ gradcam_complete
                             ▼
                    ┌─────────────────┐
                    │  7. Reporting   │
                    └────────┬────────┘
                             │ report_complete
                             ▼
                    ┌─────────────────┐
                    │8. ClinicalReview│
                    └─────────────────┘
```

---

## 3. Parameter Classification

Parameters are strictly categorized to avoid unverified performance claims:
- **MEASURED**: Empirically measured system timings (None at this stage; profiling deferred until environment setup).
- **ASSUMED**: Configurable operational assumptions for simulation.
- **TARGET**: System-level throughput and volume requirements.

| Parameter | Classification | Description |
|---|---|---|
| `annual_patient_volume = 100000` | **TARGET** | Target annual screening capacity (100,000 patients/yr) |
| `arrival_rate ~ 0.0139 patients/s` | **TARGET** | Calculated: 100,000 / (250 days * 8h * 3600s) |
| `acquisition_rate` | **ASSUMED** | Configurable assumption — not yet measured |
| `image_size_bytes` | **ASSUMED** | Configurable assumption — not yet measured |
| `iqa_processing_time` | **ASSUMED** | Configurable assumption — not yet measured |
| `enhancement_processing_time` | **ASSUMED** | Configurable assumption — not yet measured |
| `classifier_processing_time` | **ASSUMED** | Configurable assumption — not yet measured |
| `gradcam_processing_time` | **ASSUMED** | Configurable assumption — not yet measured |
| `report_processing_time` | **ASSUMED** | Configurable assumption — not yet measured |
| `reviewer_rate` | **ASSUMED** | Configurable assumption — not yet measured |

---

## 4. Current Environment Status & Limitations
- **Current Status**: `BLOCKED` — MATLAB and Simulink runtimes are not installed on this workstation.
- **Rules Adhered**:
  - No synthetic/fake `.slx` mock file created.
  - No alternative simulation tool substituted and falsely labeled as Simulink.
  - 100% frozen model weights preserved; zero retraining.
- **Next Steps**: Mount or configure MATLAB/Simulink environment on host before compiling `.slx` model diagrams and running latency/throughput simulations.
