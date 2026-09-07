import React from "react";
import { Sparkles, AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react";
import { ReferableResponse } from "@/types/screening";

export interface ReferableTriageCardProps {
  referable: ReferableResponse;
  isBorderline?: boolean;
}

export const ReferableTriageCard: React.FC<ReferableTriageCardProps> = ({
  referable,
  isBorderline = false,
}) => {
  const isRef = referable.is_referable;

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            03 &bull; Referable DR Screening & Clinical Triage
          </h3>
        </div>
        <span className="font-mono text-xs text-stone-400">
          Threshold: {(referable.threshold * 100).toFixed(1)}% (0.33)
        </span>
      </div>

      {/* Main Triage Decision Box */}
      <div
        className={`flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border p-5 ${
          isRef
            ? "border-amber-200 bg-amber-50/60"
            : "border-emerald-200 bg-emerald-50/50"
        }`}
      >
        <div className="flex items-center space-x-3.5">
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-xs ${
              isRef ? "bg-amber-600 text-white" : "bg-emerald-700 text-white"
            }`}
          >
            {isRef ? (
              <AlertTriangle className="h-6 w-6" />
            ) : (
              <CheckCircle2 className="h-6 w-6" />
            )}
          </div>
          <div>
            <span
              className={`font-mono text-[10px] font-bold uppercase tracking-wider ${
                isRef ? "text-amber-800" : "text-emerald-800"
              }`}
            >
              Triage Classification
            </span>
            <h4 className="text-xl font-extrabold text-stone-950">
              {referable.status}
            </h4>
            <p className="text-xs text-stone-600 mt-0.5">
              {isRef
                ? "Cumulative vision-threatening DR risk exceeds operating threshold."
                : "Cumulative vision-threatening DR risk remains below operating threshold."}
            </p>
          </div>
        </div>

        <div className="sm:text-right">
          <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
            Referable Probability
          </span>
          <p
            className={`font-mono text-2xl font-extrabold ${
              isRef ? "text-amber-900" : "text-emerald-900"
            }`}
          >
            {(referable.probability * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Triage Scale: Non-referable (0-1) vs Referable (2-4) (Task 14) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <div
          className={`rounded-xl border p-3 ${
            !isRef
              ? "border-emerald-700 bg-emerald-50/70 shadow-2xs font-semibold"
              : "border-stone-200 bg-stone-50/40 opacity-70"
          }`}
        >
          <span className="block text-[10px] font-mono text-stone-500 uppercase">Non-Referable Category</span>
          <span className="text-xs font-bold text-stone-900">Grade 0 &mdash; Grade 1 (No DR, Mild DR)</span>
          <span className="block text-[11px] text-stone-500 mt-1">
            Threshold: &lt; 33.0% cumulative risk
          </span>
        </div>

        <div
          className={`rounded-xl border p-3 ${
            isRef
              ? "border-amber-600 bg-amber-50/70 shadow-2xs font-semibold"
              : "border-stone-200 bg-stone-50/40 opacity-70"
          }`}
        >
          <span className="block text-[10px] font-mono text-stone-500 uppercase">Referable Category</span>
          <span className="text-xs font-bold text-stone-900">Grade 2 &mdash; Grade 4 (Moderate, Severe, PDR)</span>
          <span className="block text-[11px] text-stone-500 mt-1">
            Threshold: &ge; 33.0% cumulative risk
          </span>
        </div>
      </div>

      {/* Why this screening result? (Task 15) */}
      <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-4 text-xs space-y-1">
        <h5 className="font-bold text-stone-900">Why this screening result?</h5>
        <p className="text-stone-600 leading-relaxed">
          {isRef
            ? `The model's referable probability (${(referable.probability * 100).toFixed(1)}%) is above the configured screening operating threshold (33.0%). Cumulative probability of Moderate, Severe, or Proliferative DR warrants specialist triage.`
            : `The model's referable probability (${(referable.probability * 100).toFixed(1)}%) is below the configured screening operating threshold (33.0%). The predicted probability distribution does not meet the threshold for immediate specialist referral.`}
        </p>
      </div>

      {/* Clinical Workflow Action Panel (Task 16) */}
      <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-2xs">
        <div className="flex items-start space-x-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-stone-100 text-stone-700">
            <ArrowRight className="h-4 w-4" />
          </div>
          <div className="space-y-1">
            <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-stone-400">
              Recommended Workflow Action
            </span>
            <p className="text-xs font-bold text-stone-900">
              {isRef
                ? "Clinical review recommended: Schedule patient for comprehensive dilated fundus examination by a specialist ophthalmologist or optometrist."
                : "Continue according to local screening protocol: Schedule routine annual follow-up diabetic retinal screening."}
            </p>
            <p className="text-[11px] text-stone-500">
              {isBorderline
                ? "Quality advisory: Borderline acquisition quality noted. Confirm clinical visibility during review."
                : "Framed as clinical workflow triaging guidance, not autonomous diagnostic prescription."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
