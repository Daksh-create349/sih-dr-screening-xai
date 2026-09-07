"""Pydantic schemas for the DR screening REST API."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "healthy"
    model_loaded: bool
    model_name: str
    model_input_shape: List[Optional[int]]
    model_output_shape: List[Optional[int]]


class ImageQualityResponse(BaseModel):
    """Image Quality Assessment (IQA) details."""

    overall_score: float
    decision: str
    focus: float
    illumination: float
    fov: float
    centering: float
    enhancement_applied: bool
    initial_decision: Optional[str] = None
    sub_decisions: Optional[Dict[str, str]] = None
    recapture_guidance: Optional[str] = None
    triggered_gates: Optional[List[str]] = None
    enhanced_url: Optional[str] = None


class ClassificationResponse(BaseModel):
    """5-Class ICDR DR classification details."""

    predicted_class: int
    predicted_label: str
    probabilities: Dict[int, float]
    top_probability: float
    model_name: Optional[str] = None


class ReferableResponse(BaseModel):
    """Referable DR screening decision."""

    is_referable: bool
    probability: float
    threshold: float
    status: str


class ExplainabilityResponse(BaseModel):
    """Grad-CAM explainability and visual attribution metadata."""

    gradcam_available: bool
    target_class: Optional[int] = None
    target_score: Optional[float] = None
    heatmap_dimensions: Optional[List[int]] = None
    native_dimensions: Optional[List[int]] = None
    layer_name: Optional[str] = "top_conv"
    attention_summary: Optional[str] = None
    gradcam_url: Optional[str] = None
    overlay_url: Optional[str] = None


class AnatomyResponse(BaseModel):
    """Retinal anatomical landmark context."""

    optic_disc: Optional[Dict[str, Any]] = None
    macula: Optional[Dict[str, Any]] = None
    top_attention_region: Optional[str] = None
    top_attention_mass_pct: Optional[float] = None
    macular_overlap_pct: Optional[float] = None
    optic_disc_overlap_pct: Optional[float] = None
    attention_bounding_box: Optional[Dict[str, Any]] = None
    attention_statistics: Optional[Dict[str, Any]] = None


class EvidenceResponse(BaseModel):
    """Synthesized clinical evidence narrative, deep lesion detections, and disclaimer."""

    narrative: Optional[str] = None
    lesions: Optional[Dict[str, Any]] = None
    structured_record: Optional[Dict[str, Any]] = None
    disclaimer: str = Field(
        default="Image quality and model attention provide technical decision "
        "support only; they do not constitute independent medical diagnosis."
    )


class ProcessingResponse(BaseModel):
    """End-to-end execution latency."""

    total_time_ms: float
    breakdown_ms: Optional[Dict[str, float]] = None


class ScreeningResponse(BaseModel):
    """Complete screening pipeline response payload."""

    result_id: str
    filename: str
    screening_status: str
    image_quality: ImageQualityResponse
    classification: Optional[ClassificationResponse] = None
    referable: Optional[ReferableResponse] = None
    explainability: Optional[ExplainabilityResponse] = None
    anatomy: Optional[AnatomyResponse] = None
    evidence: Optional[EvidenceResponse] = None
    processing: ProcessingResponse
