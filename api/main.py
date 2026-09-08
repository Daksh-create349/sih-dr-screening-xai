"""FastAPI application for the Diabetic Retinopathy screening pipeline."""

from pathlib import Path
import sys

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure DR root in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from classifier.model import (  # noqa: E402
    load_classifier_model,
    get_model_metadata,
)
from api.schemas import HealthResponse, ScreeningResponse  # noqa: E402
from api.service import (  # noqa: E402
    run_screening_service,
    get_cached_image_path,
)

app = FastAPI(
    title="DR Screening Pipeline API",
    description="Local clinical screening API integrating IQA, "
    "EfficientNetB3 classifier, Grad-CAM, and anatomical evidence.",
    version="0.1.0",
)

# CORS configuration (allow local dev + any Vercel preview/production domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """System health check and live model verification endpoint (Task 13)."""
    try:
        model = load_classifier_model()
        meta = get_model_metadata(model)

        input_shape = list(meta.get("input_shape", [None, 384, 384, 3]))
        output_shape = list(meta.get("output_shape", [None, 5]))
        model_name = getattr(model, "name", "EfficientNetB3_DR")


        return HealthResponse(
            status="healthy",
            model_loaded=True,
            model_name=model_name,
            model_input_shape=input_shape,
            model_output_shape=output_shape,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model loading or service health failure: {str(exc)}",
        )


@app.post(
    "/api/screen",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
)
async def screen_retinal_image(
    image: UploadFile = File(
        ..., description="Color retinal fundus photograph"
    ),
) -> ScreeningResponse:

    """Execute end-to-end clinical screening on uploaded fundus photograph."""
    filename = image.filename or "uploaded_retina.png"
    ext = Path(filename).suffix.lower()

    if ext not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PNG, JPG, or JPEG retinal photograph.",  # noqa: E501
        )

    try:
        file_bytes = await image.read()
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty (0 bytes).",
            )

        response = run_screening_service(file_bytes, filename)
        return response

    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        # Sanitize unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening pipeline execution error: {str(exc)}",
        )



@app.get("/api/result/{result_id}/overlay")
def get_overlay_asset(result_id: str) -> FileResponse:
    """Retrieve computed Grad-CAM overlay asset for a given result ID."""
    img_path = get_cached_image_path(result_id, "overlay")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grad-CAM overlay asset not found or expired for this screening session.",  # noqa: E501
        )
    return FileResponse(img_path, media_type="image/png")


@app.get("/api/result/{result_id}/gradcam")
def get_gradcam_asset(result_id: str) -> FileResponse:
    """Retrieve raw computed Grad-CAM colormap asset for a given result ID."""
    img_path = get_cached_image_path(result_id, "gradcam")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grad-CAM asset not found or expired for this screening session.",  # noqa: E501
        )
    return FileResponse(img_path, media_type="image/png")


@app.get("/api/result/{result_id}/original")
def get_original_asset(result_id: str) -> FileResponse:
    """Retrieve cached original retinal photograph for a given result ID."""
    img_path = get_cached_image_path(result_id, "original")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original image asset not found or expired for this screening session.",  # noqa: E501
        )
    return FileResponse(img_path, media_type="image/png")


@app.get("/api/result/{result_id}/enhanced")
def get_enhanced_asset(result_id: str) -> FileResponse:
    """Retrieve cached CLAHE-enhanced retinal photograph for a borderline session."""
    img_path = get_cached_image_path(result_id, "enhanced")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhanced image asset not found or not generated for this screening session.",  # noqa: E501
        )
    return FileResponse(img_path, media_type="image/png")


@app.get("/api/result/{result_id}/evidence_overlay")
def get_evidence_overlay_asset(result_id: str) -> FileResponse:
    """Retrieve anatomical optic disc & exudate lesion overlay for a screening session."""
    img_path = get_cached_image_path(result_id, "evidence_overlay")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence overlay asset not found or not generated for this session.",
        )
    return FileResponse(img_path, media_type="image/png")


@app.get("/api/result/{result_id}/vessels")
def get_vessels_asset(result_id: str) -> FileResponse:
    """Retrieve high-contrast retinal vessel segmentation angiogram asset."""
    img_path = get_cached_image_path(result_id, "vessels")
    if img_path is None or not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vessels asset not found or not generated for this session.",
        )
    return FileResponse(img_path, media_type="image/png")

