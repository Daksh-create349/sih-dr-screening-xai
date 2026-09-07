# Diabetic Retinopathy Screening API (FastAPI)

Engineering backend connecting the diabetic retinopathy deep-learning screening pipeline to client applications.

## Purpose

The FastAPI backend provides a RESTful interface to the frozen, trained EfficientNetB3 screening pipeline, including:
1. Optical Image Quality Assessment (IQA) & routing gatekeeper.
2. 5-Class ICDR Diabetic Retinopathy severity classification.
3. Referable DR screening decision at calibrated 0.33 threshold.
4. Native back-warped retinal Grad-CAM feature attribution heatmaps.
5. Anatomical evidence and landmark spatial correlation.

> **CRITICAL MEDICAL DISCLAIMER:**
> This system is an engineering prototype developed for hackathon demonstration. It does **not** provide clinical diagnoses, has **not** received FDA/CE regulatory clearance, and must **not** be deployed for patient management. Grad-CAM visual heatmaps represent model feature attributions, **not** certified lesion detections.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and loaded model metadata |
| `POST` | `/api/screen` | Multipart upload for retinal image screening |
| `GET` | `/api/result/{result_id}/overlay` | PNG Grad-CAM visualization overlay on original retina |
| `GET` | `/api/result/{result_id}/gradcam` | Raw JET colormap Grad-CAM heatmap PNG |
| `GET` | `/api/result/{result_id}/original` | Stored session copy of input retinal photograph |

---

## Local Run Command

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend health:
```bash
curl http://localhost:8000/api/health
```

Expected output:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "EfficientNetB3_DR",
  "model_input_shape": [null, 384, 384, 3],
  "model_output_shape": [null, 5]
}
```

---

## Request & Response Format

### `POST /api/screen`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `image`: Retinal image file (`.png`, `.jpg`, `.jpeg`). Max size: 25 MB.

### Response (`ScreeningResponse`)
```json
{
  "result_id": "c7a8b6d2-...",
  "filename": "aptos_eval_6959267_grade3.png",
  "screening_status": "COMPLETED",
  "image_quality": {
    "overall_score": 88.4,
    "decision": "GOOD",
    "focus": 92.1,
    "illumination": 86.3,
    "fov": 89.0,
    "centering": 87.2,
    "enhancement_applied": false,
    "initial_decision": "GOOD",
    "sub_decisions": {},
    "recapture_guidance": null
  },
  "classification": {
    "predicted_class": 3,
    "predicted_label": "Severe DR",
    "probabilities": {
      "0": 0.0012,
      "1": 0.0154,
      "2": 0.0821,
      "3": 0.8845,
      "4": 0.0168
    },
    "top_probability": 0.8845,
    "model_name": "EfficientNetB3_DR"
  },
  "referable": {
    "is_referable": true,
    "probability": 0.9834,
    "threshold": 0.33,
    "status": "Referable DR"
  },
  "explainability": {
    "gradcam_available": true,
    "target_class": 3,
    "target_score": 0.8845,
    "heatmap_dimensions": [384, 384],
    "attention_summary": "Peak Grad-CAM activation in macular region targeting Severe DR.",
    "gradcam_url": "/api/result/c7a8b6d2-.../gradcam",
    "overlay_url": "/api/result/c7a8b6d2-.../overlay"
  },
  "anatomy": {
    "optic_disc": { "detected": true, "center": [120, 192] },
    "macula": { "detected": true, "center": [240, 192] },
    "top_attention_region": "macular"
  },
  "evidence": {
    "narrative": "Model classified retinal image as Grade 3 (Severe DR) with 88.5% confidence...",
    "disclaimer": "Image quality and model attention provide technical decision support only..."
  },
  "processing": {
    "total_time_ms": 2450.2,
    "breakdown_ms": {
      "iqa_ms": 21.3,
      "classifier_ms": 0.0,
      "referable_ms": 0.1,
      "gradcam_ms": 1056.7,
      "evidence_ms": 1057.1
    }
  }
}
```

---

## Safety Routing

1. **UNGRADEABLE Quality Gate**:
   - If an uploaded fundus image fails quality gates (severe blur, underexposure, clipping), the backend responds with `screening_status = "REJECTED_UNGRADEABLE"`.
   - The deep-learning classifier and Grad-CAM backprop are **strictly bypassed**.
   - Specific recapture feedback is returned (e.g. adjust camera lighting, re-center pupil).

2. **BORDERLINE Routing**:
   - Images with borderline optical quality attempt enhancement.
   - If quality improves, pipeline proceeds under borderline advisory status (`screening_status = "BORDERLINE_PROCEEDED"`).
   - Downstream reports state enhancement does not recover lost clinical details.

---

## Storage & Result Lifecycle

- Uploaded images and rendered Grad-CAM overlays are stored temporarily in `results/api_cache/{result_id}/`.
- Temporary assets enable web browser rendering via the `/api/result/{result_id}/overlay` and `/gradcam` endpoints.
- No permanent patient identifiers or raw photographs are stored beyond the runtime session cache.
- Local temporary files can be purged at any time without impacting pipeline evaluation.

---

## CORS Policy

Development CORS is explicitly restricted to local Next.js client origins:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
