import React from "react";
import { ScreeningResponse } from "@/types/screening";

export interface PrintableSummaryProps {
  result: ScreeningResponse;
}

export const PrintableSummary: React.FC<PrintableSummaryProps> = ({ result }) => {
  const iq = result.image_quality;
  const cls = result.classification;
  const ref = result.referable;
  const ev = result.evidence;
  const anat = result.anatomy;

  return (
    <div className="hidden print-only p-8 text-black space-y-6 font-sans">
      {/* Header */}
      <div className="border-b-2 border-black pb-4 flex justify-between items-start">
        <div>
          <h1 className="text-xl font-bold uppercase tracking-wider">
            Diabetic Retinopathy Screening Summary
          </h1>
          <p className="text-xs text-gray-600">
            Automated Decision Support &bull; AI-Assisted Clinical Triaging Protocol
          </p>
        </div>
        <div className="text-right text-xs">
          <p className="font-mono">Result ID: {result.result_id.slice(0, 12)}</p>
          <p className="font-mono">File: {result.filename}</p>
        </div>
      </div>

      {/* Primary Triage & Grade Strip */}
      <div className="border border-black p-4 grid grid-cols-3 gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase text-gray-500 block">Overall Quality</span>
          <span className="text-base font-bold">
            {iq.decision} ({iq.overall_score.toFixed(1)}/100)
          </span>
        </div>
        <div>
          <span className="text-[10px] font-bold uppercase text-gray-500 block">Predicted Severity</span>
          <span className="text-base font-bold">
            {cls ? `Grade ${cls.predicted_class} (${cls.predicted_label})` : "Bypassed"}
          </span>
          {cls && <span className="text-xs text-gray-600 block">Confidence: {(cls.top_probability * 100).toFixed(1)}%</span>}
        </div>
        <div>
          <span className="text-[10px] font-bold uppercase text-gray-500 block">Triage Status</span>
          <span className="text-base font-bold">
            {ref ? ref.status : "Bypassed"}
          </span>
          {ref && <span className="text-xs text-gray-600 block">Risk: {(ref.probability * 100).toFixed(1)}% (cutoff: 33.0%)</span>}
        </div>
      </div>

      {/* Optical Component Breakdown */}
      <div className="border border-gray-300 p-3 text-xs">
        <h4 className="font-bold uppercase text-[10px] text-gray-600 mb-2">Optical Quality Parameters</h4>
        <div className="grid grid-cols-4 gap-2 font-mono">
          <div>Focus: {iq.focus.toFixed(1)}%</div>
          <div>Illumination: {iq.illumination.toFixed(1)}%</div>
          <div>FOV: {iq.fov.toFixed(1)}%</div>
          <div>Centering: {iq.centering.toFixed(1)}%</div>
        </div>
      </div>

      {/* Synthesized Narrative */}
      {ev?.narrative && (
        <div className="border border-gray-300 p-4 text-xs space-y-1">
          <h4 className="font-bold uppercase text-[10px] text-gray-600">Diagnostic Evidence Synthesis</h4>
          <p className="leading-relaxed">{ev.narrative}</p>
        </div>
      )}

      {/* Anatomical Context */}
      {anat && (
        <div className="border border-gray-300 p-3 text-xs space-y-1">
          <h4 className="font-bold uppercase text-[10px] text-gray-600">Anatomical Localization & Attention</h4>
          <p>
            Dominant Attention: <strong className="capitalize">{anat.top_attention_region?.replace(/_/g, " ") || "Macular Region"}</strong>. Optic Disc: {anat.optic_disc?.detected ? "Localized" : "Estimated"}. Macula: {anat.macula?.detected ? "Localized" : "Estimated"}.
          </p>
        </div>
      )}

      {/* Recommended Workflow Action */}
      <div className="border-2 border-black p-4 text-xs space-y-1">
        <h4 className="font-bold uppercase text-[10px] text-black">Recommended Workflow Action</h4>
        <p className="font-semibold text-sm">
          {ref?.is_referable
            ? "Clinical Review Recommended: Specialist ophthalmological evaluation indicated based on referable criteria."
            : "Continue Routine Screening: Rescreen patient in 12 months in accordance with diabetic eye-care protocols."}
        </p>
      </div>

      {/* Sign-off & Disclaimer */}
      <div className="pt-6 border-t border-gray-300 grid grid-cols-2 gap-8 text-xs">
        <div className="space-y-4">
          <p className="text-[10px] text-gray-500 leading-relaxed">
            {ev?.disclaimer || "Feature attribution only. Technical decision support prototype; not an independent medical diagnosis."}
          </p>
        </div>
        <div className="space-y-8 text-right">
          <div className="border-b border-black w-48 ml-auto pb-1 text-left text-[10px] text-gray-500">
            Reviewing Clinician Signature
          </div>
          <div className="border-b border-black w-48 ml-auto pb-1 text-left text-[10px] text-gray-500">
            Date
          </div>
        </div>
      </div>
    </div>
  );
};
