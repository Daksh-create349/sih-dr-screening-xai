/**
 * TypeScript definitions for Diabetic Retinopathy screening application.
 * Matches genuine FastAPI backend schemas and runtime states without mock values.
 */

export type ScreeningState =
  | "EMPTY"
  | "IMAGE_SELECTED"
  | "VALIDATING"
  | "READY_TO_ANALYZE"
  | "ANALYZING"
  | "RESULT"
  | "ERROR";

export type QualityStatus = "GOOD" | "BORDERLINE" | "UNGRADEABLE";

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  model_name: string;
  model_input_shape: (number | null)[];
  model_output_shape: (number | null)[];
}

export interface ImageQualityResponse {
  overall_score: number;
  decision: QualityStatus;
  focus: number;
  illumination: number;
  fov: number;
  centering: number;
  enhancement_applied: boolean;
  initial_decision?: string | null;
  sub_decisions?: Record<string, string> | null;
  recapture_guidance?: string | null;
  triggered_gates?: string[] | null;
  enhanced_url?: string | null;
}

export interface ClassificationResponse {
  predicted_class: number;
  predicted_label: string;
  probabilities: Record<number, number>;
  top_probability: number;
  model_name?: string | null;
}

export interface ReferableResponse {
  is_referable: boolean;
  probability: number;
  threshold: number;
  status: string;
}

export interface ExplainabilityResponse {
  gradcam_available: boolean;
  target_class?: number | null;
  target_score?: number | null;
  heatmap_dimensions?: number[] | null;
  native_dimensions?: number[] | null;
  layer_name?: string | null;
  attention_summary?: string | null;
  gradcam_url?: string | null;
  overlay_url?: string | null;
}

export interface AnatomyResponse {
  optic_disc?: Record<string, any> | null;
  macula?: Record<string, any> | null;
  top_attention_region?: string | null;
  top_attention_mass_pct?: number | null;
  macular_overlap_pct?: number | null;
  optic_disc_overlap_pct?: number | null;
  attention_bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
    area_fraction?: number;
    mean_attention?: number;
    max_attention?: number;
  } | null;
  attention_statistics?: Record<
    string,
    {
      mean_attention: number;
      max_attention: number;
      attention_fraction: number;
      overlap_fraction: number;
    }
  > | null;
}

export interface OpticDiscDetection {
  present: boolean;
  center_xy: [number, number];
  radius_px: number;
  confidence: number;
  fovea_estimate?: [number, number] | null;
  model_architecture?: string;
  training_source?: string;
}

export interface HardExudatesDetection {
  lesion_count: number;
  total_lesion_pixels: number;
  area_fraction: number;
  cluster_centroids: [number, number][];
  csme_proximity_risk?: "LOW" | "MODERATE" | "HIGH" | "NONE" | string;
}

export interface HemorrhagesDetection {
  lesion_count: number;
  total_lesion_pixels: number;
  area_fraction: number;
  cluster_centroids: [number, number][];
}

export interface CSMERisk {
  risk_level: "LOW" | "MODERATE" | "HIGH" | "NONE" | string;
  min_distance_to_fovea_px?: number | null;
  min_distance_in_disc_diameters?: number | null;
}

export interface LesionEvidence {
  optic_disc?: OpticDiscDetection | null;
  hard_exudates?: HardExudatesDetection | null;
  hemorrhages?: HemorrhagesDetection | null;
  csme_risk?: CSMERisk | null;
  [key: string]: any;
}

export interface EvidenceResponse {
  narrative?: string | null;
  lesions?: LesionEvidence | null;
  structured_record?: Record<string, any> | null;
  disclaimer: string;
}

export interface ProcessingResponse {
  total_time_ms: number;
  breakdown_ms?: Record<string, number> | null;
}

export interface ScreeningResponse {
  result_id: string;
  filename: string;
  screening_status:
    | "COMPLETED"
    | "BORDERLINE_PROCEEDED"
    | "REJECTED_UNGRADEABLE"
    | string;
  image_quality: ImageQualityResponse;
  classification?: ClassificationResponse | null;
  referable?: ReferableResponse | null;
  explainability?: ExplainabilityResponse | null;
  anatomy?: AnatomyResponse | null;
  evidence?: EvidenceResponse | null;
  processing: ProcessingResponse;
}

export interface UploadedImageMeta {
  file: File;
  previewUrl: string;
  filename: string;
  fileSizeBytes: number;
  fileSizeFormatted: string;
  dimensions: {
    width: number;
    height: number;
  };
  mimeType: string;
}

export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
}
