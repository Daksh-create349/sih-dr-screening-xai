/**
 * API client for interacting with the Python Diabetic Retinopathy screening backend.
 * Connects Next.js frontend to FastAPI backend.
 */

import { HealthResponse, ScreeningResponse } from "@/types/screening";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Send a color retinal fundus image to the backend for real-time screening.
 * Runs IQA, routing, classification, referable triage, Grad-CAM, and evidence extraction.
 */
export async function screenRetinalImage(
  file: File,
  signal?: AbortSignal
): Promise<ScreeningResponse> {
  const formData = new FormData();
  formData.append("image", file, file.name);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/screen`, {
      method: "POST",
      body: formData,
      signal,
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error("Screening request timed out. Please try again.");
    }
    throw new Error(
      "Backend screening server unavailable. Ensure FastAPI is running on port 8000."
    );
  }

  if (!response.ok) {
    let errorDetail = "Screening analysis failed.";
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Non-JSON response
      errorDetail = `Server responded with status ${response.status} (${response.statusText})`;
    }
    throw new Error(errorDetail);
  }

  const data: ScreeningResponse = await response.json();
  return data;
}

/**
 * Fetch health status and verified model dimensions from Python backend.
 */
export async function getBackendHealth(
  signal?: AbortSignal
): Promise<HealthResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
      signal,
    });
  } catch (err: unknown) {
    throw new Error(
      "Backend screening server unavailable. Ensure FastAPI is running on port 8000."
    );
  }

  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }

  return response.json();
}

/**
 * Resolve full URL for backend image assets (e.g. Grad-CAM heatmaps, overlays).
 */
export function getAssetUrl(pathOrUrl?: string | null): string {
  if (!pathOrUrl) return "";
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  const cleanPath = pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
  return `${API_BASE_URL}${cleanPath}`;
}

/**
 * Resolve full URL for IDRiD deep lesions and optic disc segmentation overlay.
 */
export function getEvidenceOverlayUrl(resultId?: string | null): string {
  if (!resultId) return "";
  return `${API_BASE_URL}/api/result/${resultId}/evidence_overlay`;
}

/**
 * Resolve full URL for high-contrast retinal vessel tree angiogram.
 */
export function getVesselsUrl(resultId?: string | null): string {
  if (!resultId) return "";
  return `${API_BASE_URL}/api/result/${resultId}/vessels`;
}
