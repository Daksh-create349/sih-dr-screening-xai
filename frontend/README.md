# Diabetic Retinopathy Clinical Retinal Analysis Workstation (Next.js 16)

A clinical-grade retinal decision support workstation and explainability visualization system connected to the frozen Python EfficientNetB3 screening pipeline.

---

## Workstation Architecture & Design Language

- **Visual Concept**: Premium Medical Imaging Technology & Authoritative Decision Support.
- **Palette**: Warm stone canvas (`#fbfbf9`), deep forest primary accent (`#0f3b2e`), dark charcoal typography (`#1c1917`), subtle neutral borders, and restrained elevation.
- **Hero Image Prominence**: The retinal fundus photograph is the central hero asset with zoom, fit, and fullscreen pan capabilities.

---

## Major Workstation Sections

### 1. Fundus Imaging Workspace
- **Viewport**: Aspect-ratio-preserved fundus photograph viewport with optical center reticle.
- **Controls**: Lightweight controls for Fit-to-view, 100% reset, Zoom In (+), Zoom Out (-), and Fullscreen.
- **Keyboard Shortcuts**: `+` (zoom in), `-` (zoom out), `0` (reset), `Escape` (exit fullscreen).
- **Metadata**: Real-time display of filename, resolution dimensions, and byte size.

### 2. Clinical Screening Summary Strip
- Directly below the imaging workspace displaying real-time API values:
  - **Image Quality**: Decision & composite score (e.g. `GOOD (82/100)`)
  - **DR Classification**: Predicted grade and clinical label
  - **Triage Status**: `Referable DR` vs `Non-Referable DR`
  - **Total Latency**: Measured end-to-end execution time

### 3. Analysis Workflow Pipeline Trace
- 8-stage visual pipeline timeline reflecting genuine runtime execution state:
  1. `01` Image Acquisition (Completed)
  2. `02` Quality Assessment (Completed)
  3. `03` Quality Gatekeeper (Completed / Blocked)
  4. `04` Optical Enhancement (Completed / Skipped)
  5. `05` DR Classification (Completed / Blocked)
  6. `06` Referable Triage (Completed / Blocked)
  7. `07` Model Attribution (Completed / Blocked)
  8. `08` Evidence Synthesis (Completed / Blocked)

### 4. Image Quality Diagnostics & Enhancement Comparison
- **Composite Gauge**: SVG radial meter animating from 0 to composite score over 1000ms with ease-out interpolation.
- **Diagnostic Visual Meters**:
  - Focus / Sharpness meter with threshold classification
  - Illumination Uniformity exposure meter
  - Field of View (FOV) coverage meter
  - Retinal Centering alignment meter
- **Triggered Gates**: Displays any flagged quality attributes.
- **Before / After Enhancement Viewer**: Draggable split-slider and side-by-side view comparing original photograph to CLAHE-enhanced image for borderline acquisitions.

### 5. DR Classification & Severity Scale
- **Primary Result**: Predicted DR Grade (0 to 4) with ICDR clinical name and model confidence.
- **Horizontal Clinical Scale**: Visual 5-stage progression scale (0 — 1 — 2 — 3 — 4) highlighting the predicted grade.
- **5-Class Distribution**: Interactive probability bars displaying genuine Softmax probabilities (summing to 1.0).

### 6. Referable Screening & Clinical Action
- **Triage Decision**: Status badge comparing cumulative P(Grades 2-4) against the calibrated 0.33 threshold.
- **Triage Scale**: Visual relationship between Non-referable (Grades 0-1) and Referable (Grades 2-4).
- **Recommended Workflow Action**: Actionable triage advice (e.g., specialist referral vs routine annual screening vs repeat acquisition).

### 7. Model Feature Attribution (Grad-CAM)
- **Viewer Modes**: `Overlay`, `Split Slider` (interactive dragging handle), `Raw Heatmap`, and `Original Retina`.
- **Animated Reveal**: Finite 1.4s opacity ramp and activation sweep settling into a static final state.
- **Replay Reveal**: Button allowing evaluators to replay the activation transition.
- **Attribution Metadata**: Displays target class, target score, native resolution (`12 × 12`), display resolution (`384 × 384`), and layer name (`top_conv`).
- **Mandatory Framing**: *"Model feature attribution — not lesion detection"*.

### 8. Retinal Anatomical Context & Regional Statistics
- **Retinal Landmark Map**: Scaled SVG coordinate overlay on top of the actual fundus photograph:
  - Optic Disc circle candidate (`center`, `radius`, `confidence`)
  - Macula estimate candidate (`center`, `radius`, `confidence`)
  - Peak Attention bounding box (`[x, y, width, height]`)
- **Landmark Reliability**: Physiological confidence indicators ("Localized" vs "Estimated").
- **Regional Attention Table**: Expandable table listing mean attention, max attention, attention fraction, and overlap fraction across anatomical regions.

### 9. Evidence Narrative & Multi-Dimensional Reliability
- **Evidence Report**: Synthesized diagnostic narrative from the Python explainability layer.
- **What the Model Focused On**: Explicit regional concentration callout.
- **Reliability Assessment**: 4 separate dimensions: Optical Quality, Classifier Confidence, Landmark Localization, and Explainability Availability.

### 10. Technical Pipeline Specifications
- Collapsible panel detailing model architecture, tensor input/output shapes, convolutional gradient layers, and measured latency breakdown.

### 11. Printable Clinical Report
- Clicking **Print Report** in the header or pressing `Cmd+P` formats a high-contrast clinical screening summary sheet using `@media print` CSS. Hides interactive buttons and navigation while preserving image, quality metrics, classification, triage, narrative, and reviewing clinician signature blocks.

---

## Accessibility & Reduced Motion

- Fully compliant with `@media (prefers-reduced-motion: reduce)`.
- When reduced motion is enabled, all large animations, Grad-CAM reveals, and circular meters display their final static state immediately.
- Keyboard accessible slider controls (`ArrowLeft`, `ArrowRight`) and zoom controls (`+`, `-`, `0`, `Escape`).

---

## Local Development & Testing

Start FastAPI Backend (port 8000):
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Start Next.js Client (port 3000):
```bash
npm run dev
```

Run Frontend Test Suite (30 tests):
```bash
npm test
```

Run Production Build:
```bash
npm run build
```

Run Backend Regression Suite (371 tests):
```bash
pytest -q
```

---

## Clinical Safety Disclaimer

This software is an engineering decision-support prototype created for technical demonstration. It does not provide medical diagnoses, has not received regulatory clearance, and must not replace professional clinical evaluation. Grad-CAM visual heatmaps represent model feature attribution, not certified lesion detection.
