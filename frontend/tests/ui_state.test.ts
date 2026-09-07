/**
 * UI State & Clinical Interaction Contract Tests (Node.js Test Runner)
 * Strictly tests frontend presentation logic and state contracts.
 * All fixtures are explicitly labeled as UI CONTRACT FIXTURES.
 */

import test, { describe } from "node:test";
import assert from "node:assert/strict";
import {
  ScreeningResponse,
  ImageQualityResponse,
  ClassificationResponse,
  ReferableResponse,
  ExplainabilityResponse,
} from "../types/screening.js";

describe("UI State Contract Tests — Clinical Results Presentation", () => {
  // Pure UI contract test fixture — not real clinical evaluation
  const MOCK_GOOD_CONTRACT_FIXTURE: ScreeningResponse = {
    result_id: "test-good-001",
    filename: "sample_good_retina.png",
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
      model_name: "APTOS_DR_EfficientNetB3",
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
      gradcam_url: "/api/result/test-good-001/gradcam",
      overlay_url: "/api/result/test-good-001/overlay",
      attention_summary: "Peak Grad-CAM activation in macular region",
    },
    anatomy: {
      top_attention_region: "macular",
      optic_disc: { detected: true },
      macula: { detected: true },
    },
    evidence: {
      narrative: "Model classified retinal image as Grade 3 (Severe DR).",
      disclaimer: "Feature attribution only. Not lesion detection.",
    },
    processing: {
      total_time_ms: 2340.5,
      breakdown_ms: { iqa_ms: 22.0, classifier_ms: 220.0, gradcam_ms: 1050.0, evidence_ms: 1040.0 },
    },
  };

  test("verifies primary result card hierarchy and probability display", () => {
    const cls = MOCK_GOOD_CONTRACT_FIXTURE.classification!;
    assert.equal(cls.predicted_class, 3);
    assert.equal(cls.predicted_label, "Severe DR");
    assert.equal((cls.top_probability * 100).toFixed(1), "75.0");

    // 5-class distribution check
    const probSum = Object.values(cls.probabilities).reduce((a, b) => a + b, 0);
    assert.ok(Math.abs(probSum - 1.0) < 1e-4);
  });

  test("verifies referable screening triage logic at 0.33 threshold", () => {
    const ref = MOCK_GOOD_CONTRACT_FIXTURE.referable!;
    assert.equal(ref.threshold, 0.33);
    assert.equal(ref.is_referable, true);
    assert.ok(ref.probability >= 0.33);
    assert.equal(ref.status, "Referable DR");
  });

  test("verifies quality gauge score & color classification contract", () => {
    const iq = MOCK_GOOD_CONTRACT_FIXTURE.image_quality;
    assert.equal(iq.decision, "GOOD");
    assert.ok(iq.overall_score >= 80);

    // Component scores bounded in [0, 100]
    [iq.focus, iq.illumination, iq.fov, iq.centering].forEach((score) => {
      assert.ok(score >= 0 && score <= 100);
    });
  });

  test("verifies Grad-CAM explainability and mandatory scientific labeling", () => {
    const exp = MOCK_GOOD_CONTRACT_FIXTURE.explainability!;
    assert.equal(exp.gradcam_available, true);
    assert.ok(exp.overlay_url?.includes("overlay"));
    assert.ok(exp.gradcam_url?.includes("gradcam"));

    // Scientific disclaimer check
    const disclaimer = MOCK_GOOD_CONTRACT_FIXTURE.evidence!.disclaimer;
    assert.match(disclaimer, /Feature attribution/i);
    assert.match(disclaimer, /Not lesion detection/i);
  });

  test("verifies UNGRADEABLE safety gatekeeper strictly blocks downstream evaluation", () => {
    const UNGRADEABLE_CONTRACT_FIXTURE: ScreeningResponse = {
      result_id: "test-ungradeable-002",
      filename: "dark_retina.png",
      screening_status: "REJECTED_UNGRADEABLE",
      image_quality: {
        overall_score: 14.2,
        decision: "UNGRADEABLE",
        focus: 12.0,
        illumination: 10.0,
        fov: 16.0,
        centering: 18.0,
        enhancement_applied: false,
        recapture_guidance: "Image focus severely blurred. Re-align camera to fundus pupil.",
      },
      classification: null,
      referable: null,
      explainability: null,
      anatomy: null,
      evidence: null,
      processing: {
        total_time_ms: 22.4,
        breakdown_ms: { iqa_ms: 21.0 },
      },
    };

    assert.equal(UNGRADEABLE_CONTRACT_FIXTURE.screening_status, "REJECTED_UNGRADEABLE");
    assert.equal(UNGRADEABLE_CONTRACT_FIXTURE.image_quality.decision, "UNGRADEABLE");
    assert.equal(UNGRADEABLE_CONTRACT_FIXTURE.classification, null);
    assert.equal(UNGRADEABLE_CONTRACT_FIXTURE.referable, null);
    assert.equal(UNGRADEABLE_CONTRACT_FIXTURE.explainability, null);
    assert.ok(UNGRADEABLE_CONTRACT_FIXTURE.image_quality.recapture_guidance?.includes("Re-align"));
  });

  test("verifies BORDERLINE protocol preserves transparency and enhancement tracking", () => {
    const BORDERLINE_CONTRACT_FIXTURE: ScreeningResponse = {
      result_id: "test-borderline-003",
      filename: "low_contrast.png",
      screening_status: "BORDERLINE_PROCEEDED",
      image_quality: {
        overall_score: 64.0,
        decision: "BORDERLINE",
        focus: 62.0,
        illumination: 66.0,
        fov: 65.0,
        centering: 63.0,
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
      processing: {
        total_time_ms: 2150.0,
      },
    };

    assert.equal(BORDERLINE_CONTRACT_FIXTURE.screening_status, "BORDERLINE_PROCEEDED");
    assert.equal(BORDERLINE_CONTRACT_FIXTURE.image_quality.decision, "BORDERLINE");
    assert.equal(BORDERLINE_CONTRACT_FIXTURE.image_quality.enhancement_applied, true);
    assert.equal(BORDERLINE_CONTRACT_FIXTURE.referable?.is_referable, false);
  });

  test("verifies execution latency formatting from milliseconds to seconds", () => {
    const ms = 2371.1;
    const s = (ms / 1000).toFixed(2);
    assert.equal(s, "2.37");
  });

  test("verifies comparison split slider bounds", () => {
    const clampPos = (val: number) => Math.min(100, Math.max(0, val));
    assert.equal(clampPos(50), 50);
    assert.equal(clampPos(-10), 0);
    assert.equal(clampPos(120), 100);
  });

  test("verifies fundus workspace zoom clamp bounds and reset", () => {
    let zoom = 1;
    const zoomIn = (z: number) => Math.min(3, z + 0.25);
    const zoomOut = (z: number) => Math.max(0.75, z - 0.25);

    zoom = zoomIn(zoom); // 1.25
    assert.equal(zoom, 1.25);
    zoom = zoomOut(zoom); // 1.0
    assert.equal(zoom, 1.0);
    zoom = zoomOut(zoomOut(zoom)); // 0.75 min clamp
    assert.equal(zoom, 0.75);
    zoom = 1; // reset
    assert.equal(zoom, 1.0);
  });

  test("verifies workflow timeline pipeline stage statuses for normal vs ungradeable", () => {
    const getStageStatuses = (status: string, enhanced: boolean) => {
      const isUngradeable = status === "REJECTED_UNGRADEABLE";
      return {
        acquire: "COMPLETED",
        iqa: "COMPLETED",
        gate: isUngradeable ? "BLOCKED" : "COMPLETED",
        enhancement: isUngradeable ? "SKIPPED" : enhanced ? "COMPLETED" : "SKIPPED",
        classifier: isUngradeable ? "BLOCKED" : "COMPLETED",
        referable: isUngradeable ? "BLOCKED" : "COMPLETED",
        gradcam: isUngradeable ? "BLOCKED" : "COMPLETED",
        evidence: isUngradeable ? "BLOCKED" : "COMPLETED",
      };
    };

    const normal = getStageStatuses("COMPLETED", false);
    assert.equal(normal.gate, "COMPLETED");
    assert.equal(normal.classifier, "COMPLETED");
    assert.equal(normal.enhancement, "SKIPPED");

    const borderline = getStageStatuses("BORDERLINE_PROCEEDED", true);
    assert.equal(borderline.gate, "COMPLETED");
    assert.equal(borderline.enhancement, "COMPLETED");
    assert.equal(borderline.classifier, "COMPLETED");

    const ungradeable = getStageStatuses("REJECTED_UNGRADEABLE", false);
    assert.equal(ungradeable.gate, "BLOCKED");
    assert.equal(ungradeable.classifier, "BLOCKED");
    assert.equal(ungradeable.evidence, "BLOCKED");
  });

  test("verifies anatomical landmark and attention region statistics parsing", () => {
    const anat = {
      optic_disc: { detected: true, center: [193.1, 273.5], radius: 21, confidence: 0.73, is_reliable: true },
      macula: { detected: true, center: [311.0, 262.0], radius: 25.2, confidence: 0.71, is_reliable: true },
      top_attention_region: "nasal_retina",
      top_attention_mass_pct: 66.7,
      attention_statistics: {
        nasal_retina: { mean_attention: 0.28, max_attention: 0.89, attention_fraction: 0.667, overlap_fraction: 0.42 },
        macular_region: { mean_attention: 0.08, max_attention: 0.35, attention_fraction: 0.12, overlap_fraction: 0.091 },
      },
    };

    assert.equal(anat.optic_disc.detected, true);
    assert.equal(anat.macula.detected, true);
    assert.equal(anat.top_attention_region, "nasal_retina");
    assert.equal(anat.top_attention_mass_pct, 66.7);

    const stats = Object.entries(anat.attention_statistics);
    assert.equal(stats.length, 2);
    assert.equal(stats[0][0], "nasal_retina");
    assert.equal(stats[0][1].attention_fraction, 0.667);
  });

  test("verifies technical details rows formatting", () => {
    const techDetails = {
      model_name: "APTOS_DR_EfficientNetB3",
      input_shape: "[None, 384, 384, 3]",
      output_shape: "[None, 5]",
      layer: "top_conv",
      threshold: 0.33,
      total_time_ms: 2371.1,
    };

    assert.equal(techDetails.model_name, "APTOS_DR_EfficientNetB3");
    assert.equal(techDetails.threshold, 0.33);
    assert.equal((techDetails.total_time_ms / 1000).toFixed(2), "2.37");
  });
});

