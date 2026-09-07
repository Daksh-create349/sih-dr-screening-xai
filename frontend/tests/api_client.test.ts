/**
 * Tests for frontend API client and backend contract handling.
 * Pure UI contract test suite — mock responses explicitly labeled as test fixtures.
 */

import test, { describe } from "node:test";
import assert from "node:assert/strict";
import { getAssetUrl, getEvidenceOverlayUrl, screenRetinalImage, getBackendHealth, API_BASE_URL } from "../lib/api.js";
import { ScreeningResponse } from "../types/screening.js";

describe("Frontend API Client & Asset URL Resolution", () => {
  test("getAssetUrl resolves relative paths with API_BASE_URL", () => {
    const url = getAssetUrl("/api/result/123/overlay");
    assert.equal(url, `${API_BASE_URL}/api/result/123/overlay`);

    const urlNoSlash = getAssetUrl("api/result/123/overlay");
    assert.equal(urlNoSlash, `${API_BASE_URL}/api/result/123/overlay`);
  });

  test("getAssetUrl preserves absolute URLs", () => {
    const absUrl = "https://screening.retina.org/api/result/123/overlay";
    assert.equal(getAssetUrl(absUrl), absUrl);
  });

  test("getAssetUrl handles null or empty inputs", () => {
    assert.equal(getAssetUrl(null), "");
    assert.equal(getAssetUrl(undefined), "");
    assert.equal(getAssetUrl(""), "");
  });

  test("getEvidenceOverlayUrl resolves evidence overlay path with result ID", () => {
    assert.equal(
      getEvidenceOverlayUrl("res-12345"),
      `${API_BASE_URL}/api/result/res-12345/evidence_overlay`
    );
    assert.equal(getEvidenceOverlayUrl(null), "");
    assert.equal(getEvidenceOverlayUrl(undefined), "");
    assert.equal(getEvidenceOverlayUrl(""), "");
  });
});

describe("API Client Request & Response Parsing (Contract Fixtures)", () => {
  const originalFetch = globalThis.fetch;

  test("screenRetinalImage successfully parses completed screening response", async () => {
    const UI_CONTRACT_FIXTURE: ScreeningResponse = {
      result_id: "test-result-001",
      filename: "retina_test.png",
      screening_status: "COMPLETED",
      image_quality: {
        overall_score: 84.5,
        decision: "GOOD",
        focus: 88.0,
        illumination: 82.0,
        fov: 85.0,
        centering: 83.0,
        enhancement_applied: false,
      },
      classification: {
        predicted_class: 3,
        predicted_label: "Severe DR",
        probabilities: { 0: 0.01, 1: 0.04, 2: 0.15, 3: 0.75, 4: 0.05 },
        top_probability: 0.75,
        model_name: "EfficientNetB3_DR",
      },
      referable: {
        is_referable: true,
        probability: 0.95,
        threshold: 0.33,
        status: "Referable DR",
      },
      explainability: {
        gradcam_available: true,
        target_class: 3,
        target_score: 0.75,
        gradcam_url: "/api/result/test-result-001/gradcam",
        overlay_url: "/api/result/test-result-001/overlay",
        attention_summary: "Peak Grad-CAM activation in macular region",
      },
      anatomy: {
        top_attention_region: "macular",
      },
      evidence: {
        narrative: "Model classified retinal image as Grade 3 (Severe DR).",
        disclaimer: "Image quality and model attention provide technical decision support only.",
      },
      processing: {
        total_time_ms: 2340.5,
        breakdown_ms: { iqa_ms: 22.0, classifier_ms: 0.0, gradcam_ms: 1100.0, evidence_ms: 1200.0 },
      },
    };

    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      assert.equal(String(input), `${API_BASE_URL}/api/screen`);
      assert.equal(init?.method, "POST");
      assert.ok(init?.body instanceof FormData);

      return new Response(JSON.stringify(UI_CONTRACT_FIXTURE), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    try {
      const dummyFile = new File(["dummy content"], "retina_test.png", { type: "image/png" });
      const result = await screenRetinalImage(dummyFile);

      assert.equal(result.result_id, "test-result-001");
      assert.equal(result.screening_status, "COMPLETED");
      assert.equal(result.image_quality.decision, "GOOD");
      assert.equal(result.classification?.predicted_class, 3);
      assert.equal(result.classification?.predicted_label, "Severe DR");
      assert.equal(result.referable?.is_referable, true);
      assert.equal(result.explainability?.gradcam_available, true);
      assert.equal(result.explainability?.overlay_url, "/api/result/test-result-001/overlay");
      assert.ok(result.evidence?.narrative);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("screenRetinalImage handles UNGRADEABLE response contract", async () => {
    const UNGRADEABLE_CONTRACT_FIXTURE: ScreeningResponse = {
      result_id: "test-ungradeable-002",
      filename: "dark_scan.png",
      screening_status: "REJECTED_UNGRADEABLE",
      image_quality: {
        overall_score: 12.0,
        decision: "UNGRADEABLE",
        focus: 10.0,
        illumination: 12.0,
        fov: 14.0,
        centering: 12.0,
        enhancement_applied: false,
        recapture_guidance: "Image severely underexposed. Recapture with proper illumination.",
      },
      classification: null,
      referable: null,
      explainability: null,
      anatomy: null,
      evidence: null,
      processing: {
        total_time_ms: 25.0,
        breakdown_ms: { iqa_ms: 24.5 },
      },
    };

    globalThis.fetch = async () => {
      return new Response(JSON.stringify(UNGRADEABLE_CONTRACT_FIXTURE), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    try {
      const dummyFile = new File(["dummy"], "dark_scan.png", { type: "image/png" });
      const result = await screenRetinalImage(dummyFile);

      assert.equal(result.screening_status, "REJECTED_UNGRADEABLE");
      assert.equal(result.image_quality.decision, "UNGRADEABLE");
      assert.equal(result.classification, null);
      assert.equal(result.referable, null);
      assert.equal(result.explainability, null);
      assert.ok(result.image_quality.recapture_guidance?.includes("underexposed"));
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("screenRetinalImage handles BORDERLINE response contract", async () => {
    const BORDERLINE_CONTRACT_FIXTURE: ScreeningResponse = {
      result_id: "test-borderline-003",
      filename: "borderline_scan.png",
      screening_status: "BORDERLINE_PROCEEDED",
      image_quality: {
        overall_score: 62.0,
        decision: "BORDERLINE",
        focus: 60.0,
        illumination: 64.0,
        fov: 62.0,
        centering: 62.0,
        enhancement_applied: true,
      },
      classification: {
        predicted_class: 1,
        predicted_label: "Mild DR",
        probabilities: { 0: 0.15, 1: 0.70, 2: 0.10, 3: 0.03, 4: 0.02 },
        top_probability: 0.70,
      },
      referable: {
        is_referable: false,
        probability: 0.15,
        threshold: 0.33,
        status: "Non-Referable DR",
      },
      explainability: {
        gradcam_available: true,
        overlay_url: "/api/result/test-borderline-003/overlay",
      },
      processing: { total_time_ms: 2200.0 },
    };

    globalThis.fetch = async () => {
      return new Response(JSON.stringify(BORDERLINE_CONTRACT_FIXTURE), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    try {
      const dummyFile = new File(["dummy"], "borderline_scan.png", { type: "image/png" });
      const result = await screenRetinalImage(dummyFile);

      assert.equal(result.screening_status, "BORDERLINE_PROCEEDED");
      assert.equal(result.image_quality.decision, "BORDERLINE");
      assert.equal(result.image_quality.enhancement_applied, true);
      assert.equal(result.classification?.predicted_class, 1);
      assert.equal(result.referable?.is_referable, false);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("screenRetinalImage handles 400 validation error from backend", async () => {
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({ detail: "Unsupported file type: application/pdf" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    };

    try {
      const dummyFile = new File(["bad"], "file.pdf", { type: "application/pdf" });
      await assert.rejects(
        async () => screenRetinalImage(dummyFile),
        /Unsupported file type/i
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("screenRetinalImage handles server unreachable error", async () => {
    globalThis.fetch = async () => {
      throw new TypeError("Failed to fetch");
    };

    try {
      const dummyFile = new File(["dummy"], "scan.png", { type: "image/png" });
      await assert.rejects(
        async () => screenRetinalImage(dummyFile),
        /Backend screening server unavailable/i
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("getBackendHealth parses loaded model parameters", async () => {
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify({
          status: "healthy",
          model_loaded: true,
          model_name: "EfficientNetB3_DR",
          model_input_shape: [null, 384, 384, 3],
          model_output_shape: [null, 5],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    };

    try {
      const health = await getBackendHealth();
      assert.equal(health.status, "healthy");
      assert.equal(health.model_loaded, true);
      assert.equal(health.model_name, "EfficientNetB3_DR");
      assert.deepEqual(health.model_input_shape, [null, 384, 384, 3]);
      assert.deepEqual(health.model_output_shape, [null, 5]);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
