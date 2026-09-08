# 02. Backend Architecture & API Orchestration

---

## What is This? (In Simple Words)
The **Backend** is the engine room of RetinaScan AI. While the frontend is the dashboard that the doctor sees, the backend is the Python server that actually receives the eye photo, fires up the AI models, measures the pixels, calculates the disease probabilities, and sends back the answers.

It is built with **FastAPI**, a modern, blazing-fast Python web framework widely used in production AI systems.

---

## Why Was It Needed? (The Real Problem It Solves)

1. **AI Models Need Heavy Python Libraries**: Deep learning models (PyTorch, TensorFlow, OpenCV, SciPy) run in Python. The browser cannot natively run 500MB neural network weights with sub-second latency. The backend handles this heavy compute.
2. **Pipelines Need Strict Orchestration**: You cannot just throw an image into a classifier. You must run quality checks first, enhance contrast if needed, run segmentation, calculate foveal distances, and generate heatmaps. The backend coordinates all these moving parts in an orderly, crash-proof pipeline.
3. **Data Privacy (Zero Cloud Leakage)**: In rural India and hospital networks, patient photos cannot be sent to third-party overseas cloud APIs due to medical privacy regulations. Our backend runs locally on the screening device (laptop/mini-PC).

---

## How It Works (Step-by-Step Request Lifecycle)

When the health worker clicks **"Run Screening Analysis"** in the frontend:

```
[Browser: Next.js Frontend]
       │
       ▼ (1) POST /api/screen (Image Multipart Upload)
┌───────────────────────────────────────────────────────────┐
│ FastAPI Server (api/main.py & api/service.py)             │
│                                                           │
│  ├── Step A: Read Image Bytes via OpenCV                  │
│  ├── Step B: Run Optical IQA Gatekeeper (<140ms)          │
│  │     └─ If blurry/dark ──> Return UNGRADEABLE           │
│  ├── Step C: Adaptive CLAHE Enhancement (if borderline)   │
│  ├── Step D: Deep Classifier Prediction (ResNet/Efficient)│
│  ├── Step E: IDRiD Lesion Segmentation (PyTorch U-Net)    │
│  ├── Step F: Anatomical Context & CSME Distance Math      │
│  ├── Step G: Grad-CAM Feature Attribution Extraction      │
│  └── Step H: Cache Overlays & Compile JSON Response       │
└───────────────────────────────────────────────────────────┘
       │
       ▼ (2) HTTP 200 OK: Complete Structured JSON Payload
[Browser: Visualizes Result Cards & Renders Overlays]
```

---

## Core API Endpoints

| Method | Endpoint | Purpose | Output |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health check & model verification | System status, loaded weights, input/output tensors. |
| `POST` | `/api/screen` | Primary screening endpoint | Full JSON dossier: grade, probabilities, triage, IQA score. |
| `GET` | `/api/result/{id}/enhanced` | Contrast-enhanced image | JPEG stream of green-channel CLAHE image. |
| `GET` | `/api/result/{id}/gradcam` | Grad-CAM heatmap | JPEG stream of Jet-colormapped attention overlay. |
| `GET` | `/api/result/{id}/evidence_overlay` | Pixel lesion overlay | JPEG stream with labeled lesions (exudates, bleeds). |
| `GET` | `/api/result/{id}/vessels` | Vascular tree angiogram | JPEG stream of segmented retinal blood vessels. |

---

## Performance & Optimization Techniques

1. **In-Memory Buffer Streaming**: Images are decoded in RAM using NumPy and OpenCV. We avoid unnecessary disk writes during the critical inference path to prevent I/O bottlenecks.
2. **Session Result Caching**: Generated overlays (Grad-CAM heatmaps, vessel masks, enhanced photos) are cached by UUID in `results/api_cache/`. When the frontend requests `/api/result/{id}/gradcam`, it returns instantly without re-running the neural network.
3. **CORS Middleware**: Configured with `allow_origins=["*"]` to allow seamless communication whether the frontend runs on `localhost:3000` or deployed on a clinic intranet domain.
4. **Sub-2.5s Edge Execution**: The entire multi-model pipeline executes in **under 2.5 seconds** on consumer-grade CPU/Metal backends, making it completely practical for battery-powered field laptops in mobile eye camps.

---

## Judge Q&A Cheatsheet (Backend)

* **Q: "Why FastAPI instead of Flask or Django?"**
  * *A*: *"FastAPI provides asynchronous concurrency, Pydantic type validation for medical schemas, automatic OpenAPI documentation, and up to 3x higher throughput than synchronous Flask, which is critical for handling rapid photo uploads."*

* **Q: "What happens if a corrupted or non-eye image is sent to the backend?"**
  * *A*: *"The backend validates MIME types and array dimensions first. Then, Stage 1 (Field-of-View and IQA checks) immediately detects the lack of a retinal circular mask or valid illumination and safely returns an UNGRADEABLE rejection before any deep learning classifier is invoked."*
