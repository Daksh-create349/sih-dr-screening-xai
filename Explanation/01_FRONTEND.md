# 01. Frontend Architecture & Diagnostic Workstation UI

---

## What is This? (In Simple Words)
The **Frontend** is the doctor's and health worker's digital command center. It is what appears on the computer screen when using the app. 

It does two main jobs:
1. **The Educational Landing Page**: Explains how the AI works to patients and visiting evaluators using plain English, interactive comparison sliders, and a full system walkthrough.
2. **The Clinical PACS Workstation**: An ultra-fast medical viewer where healthcare workers upload retinal photos, zoom in on tiny blood vessels, toggle medical filters, and print signed clinical reports in seconds.

---

## Why Was It Needed? (The Real Problem It Solves)

1. **Doctors Hate Clunky, Ugly Software**: Most hospital software looks like it was built in 1998. Doctors refuse to adopt tools that have confusing buttons or slow loading times.
2. **Rural Health Workers Are Not Tech Experts**: The person taking the photo at a rural Primary Health Centre (PHC) is usually a technician or nurse, not an AI engineer. They need clear visual feedback like *"GREEN = Good to go"*, *"RED = Blurry, retake photo"*, and *"YELLOW = Doctor review needed"*.
3. **Medical Transparency**: An AI that just gives a number like *"Grade 3"* without letting the doctor zoom in and see the bleeding with their own eyes will never be trusted or cleared by hospital boards.
4. **Internet Independence**: The viewer tools (zoom, pan, red-free filter, contrast) run directly inside the browser using HTML5 Canvas and CSS filters, meaning the interface never lags even on slow connections.

---

## Key Features & How They Work (Step-by-Step)

### 1. The Interactive Landing Page
- **Hero Section**: Displays a looping retina video and sets the clinical tone with clear, authoritative medical branding.
- **6-Stage Interactive Flowchart**: Allows anyone to click through the entire diagnostic pipeline from optical gating to PDF generation. It shows exactly what happens inside each stage and what safety guardrails exist.
- **Live System Demo Player**: A clean, 16:9 theater-mode video player streaming an actual end-to-end clinical workflow runthrough.
- **Visual Explainability Pipeline ("How the AI Sees Your Eye")**:
  - *Stage 1 (Contrast)*: An interactive before/after split slider showing how camera glare and haze are removed via CLAHE.
  - *Stage 2 (Blood Vessels)*: An interactive toggle showing how the AI traces the retinal vascular tree like a road map.
  - *Stage 3 (Lesion Pinpointing)*: Filter chips that let the user isolate microaneurysms (pinpoint bleeds), hemorrhages (blot bleeds), and hard exudates (fat deposits).
  - *Stage 4 (CSME Zone)*: Visualizes the danger circle around the macula (central vision).
  - *Stage 5 (Grad-CAM Heatmap)*: Shows the AI's neural attention heatmap mapped directly onto real pathology.

### 2. Clinical PACS Workstation
- **Pan & Zoom (0.75x to 3x)**: Retinal lesions (like microaneurysms) can be as small as 15 to 30 microns (smaller than a human hair). Clinicians can zoom smoothly using buttons or keyboard shortcuts (`+`, `-`, `0` reset).
- **Red-Free Filter (Green Channel Emulation)**: In ophthalmology, doctors use a green filter on their ophthalmoscopes because retinal blood vessels and hemorrhages absorb green light and turn pitch black against a light background, making leaks jump out. We built a digital Red-Free toggle directly into the workstation.
- **Contrast & Brightness Sliders**: Allows the clinician to adjust illumination dynamically for underexposed or overexposed eyes.

### 3. Pre-Loaded Clinical Cohort Library
- Contains real, pre-validated Indian patient cases ranging from normal healthy eyes to severe proliferative DR with CSME and optical blur rejections.
- Allows immediate demonstration and offline testing without needing to find a fresh image file each time.

### 4. Vector PDF Clinical Dossier Export
- Clinicians can click **Print Clinical Report** or export a signed PDF.
- Auto-compiles patient metadata, IQA metrics, 5-class severity probabilities, referral triage urgency, CSME status, and visual Grad-CAM overlays into an official diagnostic dossier ready for tele-ophthalmology referral.

---

## Tech Stack & Architecture

- **Framework**: Next.js 16 (App Router with Turbopack for sub-second hot reloads).
- **UI Library**: React 19 with strict TypeScript typing (`screening.ts`).
- **Styling**: Vanilla Tailwind CSS with an authentic **"Doctor Theme"** (clinical monochrome: crisp medical white `#ffffff`, neutral dark charcoal `#18181b`, and deep black `#000000` with zero distracting neon gaming colors).
- **Icons**: Lucide React for consistent medical and technical iconography.
- **PDF Generation**: Client-side `jspdf` and `html2canvas` for instantaneous vector report compilation.

---

## Judge Q&A Cheatsheet (Frontend)

* **Q: "Why did you build a custom workstation instead of just showing an image with a prediction text?"**
  * *A*: *"Because in clinical practice, a diagnosis without visual verification is unacceptable. Doctors require DICOM/PACS inspection capabilities — specifically optical zoom, red-free illumination filtering to spot microaneurysms, and side-by-side evidence overlays — before they can sign off on a patient referral."*

* **Q: "Does the frontend require internet to display and zoom images?"**
  * *A*: *"No. All workstation image manipulation (pan, zoom, contrast, green-channel red-free filtering) executes 100% client-side via hardware-accelerated CSS and HTML5 Canvas inside the clinician's browser."*
