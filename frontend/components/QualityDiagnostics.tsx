import React, { useState } from "react";
import {
  FileCheck2,
  AlertTriangle,
  SlidersHorizontal,
  Info,
  CheckCircle2,
  Crosshair,
} from "lucide-react";
import { ImageQualityResponse } from "@/types/screening";
import { QualityGauge } from "./QualityGauge";
import { getAssetUrl } from "@/lib/api";

export interface QualityDiagnosticsProps {
  quality: ImageQualityResponse;
  originalImageUrl?: string | null;
}

export const QualityDiagnostics: React.FC<QualityDiagnosticsProps> = ({
  quality,
  originalImageUrl,
}) => {
  const [activeCompareView, setActiveCompareView] = useState<"slider" | "enhanced" | "original">("slider");
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [enhancedLoadError, setEnhancedLoadError] = useState(false);

  const enhancedUrl = getAssetUrl(quality.enhanced_url);
  const origUrl = originalImageUrl || "";
  const subDec = quality.sub_decisions || {};

  const handleSliderMove = (clientX: number, rect: DOMRect) => {
    const x = clientX - rect.left;
    const percent = Math.min(100, Math.max(0, (x / rect.width) * 100));
    setSliderPos(percent);
  };

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <FileCheck2 className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            01 &bull; Image Quality Assessment & Diagnostic Metrics
          </h3>
        </div>
        <span
          className={`rounded-md border px-2 py-0.5 text-xs font-bold uppercase ${
            quality.decision === "GOOD"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : quality.decision === "BORDERLINE"
              ? "bg-amber-50 text-amber-800 border-amber-200"
              : "bg-rose-50 text-rose-800 border-rose-200"
          }`}
        >
          Gate: {quality.decision}
        </span>
      </div>

      {/* Main Radial Gauge & Interpretation */}
      <QualityGauge quality={quality} />

      {/* 4 Diagnostic Meters (Task 7, 8) */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* FOCUS */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-stone-600">Focus / Sharpness</span>
            <span className="font-mono font-bold text-stone-900">{quality.focus.toFixed(1)} / 100</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-stone-200">
            <div
              style={{ width: `${Math.min(100, Math.max(0, quality.focus))}%` }}
              className={`h-full rounded-full transition-all duration-700 ${
                quality.focus >= 75 ? "bg-emerald-600" : quality.focus >= 50 ? "bg-amber-500" : "bg-rose-500"
              }`}
            />
          </div>
          <p className="text-[11px] text-stone-500">
            Status: <span className="font-medium text-stone-700">{subDec.focus_decision || "Calculated"}</span>
          </p>
        </div>

        {/* ILLUMINATION */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-stone-600">Illumination & Exposure</span>
            <span className="font-mono font-bold text-stone-900">{quality.illumination.toFixed(1)} / 100</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-gradient-to-r from-stone-400 via-emerald-500 to-amber-500">
            <div
              style={{ width: `${Math.min(100, Math.max(0, quality.illumination))}%` }}
              className="h-full rounded-full bg-stone-900/40 backdrop-invert"
            />
          </div>
          <p className="text-[11px] text-stone-500">
            Status: <span className="font-medium text-stone-700">{subDec.illumination_decision || "Calculated"}</span>
          </p>
        </div>

        {/* FIELD OF VIEW (FOV) */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-stone-600">Field of View (FOV)</span>
            <span className="font-mono font-bold text-stone-900">{quality.fov.toFixed(1)} / 100</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-stone-200">
            <div
              style={{ width: `${Math.min(100, Math.max(0, quality.fov))}%` }}
              className={`h-full rounded-full transition-all duration-700 ${
                quality.fov >= 75 ? "bg-emerald-600" : quality.fov >= 50 ? "bg-amber-500" : "bg-rose-500"
              }`}
            />
          </div>
          <p className="text-[11px] text-stone-500">
            Status: <span className="font-medium text-stone-700">{subDec.fov_decision || "Calculated"}</span>
          </p>
        </div>

        {/* CENTERING */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-stone-600">Retinal Centering</span>
            <span className="font-mono font-bold text-stone-900">{quality.centering.toFixed(1)} / 100</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-stone-200">
            <div
              style={{ width: `${Math.min(100, Math.max(0, quality.centering))}%` }}
              className={`h-full rounded-full transition-all duration-700 ${
                quality.centering >= 75 ? "bg-emerald-600" : quality.centering >= 50 ? "bg-amber-500" : "bg-rose-500"
              }`}
            />
          </div>
          <p className="text-[11px] text-stone-500">
            Status: <span className="font-medium text-stone-700">{subDec.centering_decision || "Calculated"}</span>
          </p>
        </div>
      </div>

      {/* Quality Gate Explanation (Task 9) */}
      <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-3.5 text-xs text-stone-700 space-y-1">
        <span className="font-bold text-stone-900">Screening Quality Gate:</span>
        <p className="text-stone-600 text-[11px] leading-relaxed">
          {quality.decision === "GOOD" && "Image passed the quality gate. Signal fidelity adequate for diagnostic screening."}
          {quality.decision === "BORDERLINE" && "Marginal acquisition fidelity. Contrast enhancement applied to assist downstream feature attribution."}
          {quality.decision === "UNGRADEABLE" && "Image failed quality gate. Screening classifier strictly blocked to prevent misclassification."}
        </p>
      </div>

      {/* Triggered Quality Gates (Task 9) */}
      {quality.triggered_gates && quality.triggered_gates.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-3.5 text-xs text-amber-900 space-y-1">
          <div className="flex items-center space-x-1.5 font-bold">
            <AlertTriangle className="h-4 w-4 text-amber-700" />
            <span>Triggered Quality Flags:</span>
          </div>
          <ul className="list-disc pl-5 text-[11px] space-y-0.5">
            {quality.triggered_gates.map((gate, i) => (
              <li key={i} className="capitalize">{gate.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      )}

      {/* BEFORE / AFTER CONTRAST ENHANCEMENT (CLAHE) */}
      {enhancedUrl && origUrl && (
        <div className="space-y-3 rounded-xl border border-stone-200 bg-stone-50/60 p-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center space-x-2">
                <h4 className="text-xs font-bold text-stone-900 uppercase tracking-wide">
                  Before / After Contrast Enhancement
                </h4>
                {quality.enhancement_applied ? (
                  <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-900">
                    Downstream Active
                  </span>
                ) : (
                  <span className="rounded bg-stone-200/80 px-2 py-0.5 text-[10px] font-medium text-stone-700">
                    Diagnostic Inspection Mode
                  </span>
                )}
              </div>
              <p className="text-[11px] text-stone-500">
                CLAHE (Contrast Limited Adaptive Histogram Equalization)
              </p>
            </div>

            <div className="inline-flex rounded-lg border border-stone-200 bg-white p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setActiveCompareView("slider")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                  activeCompareView === "slider" ? "bg-stone-900 text-white" : "text-stone-600"
                }`}
              >
                Split Slider
              </button>
              <button
                type="button"
                onClick={() => setActiveCompareView("enhanced")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                  activeCompareView === "enhanced" ? "bg-stone-900 text-white" : "text-stone-600"
                }`}
              >
                Enhanced
              </button>
              <button
                type="button"
                onClick={() => setActiveCompareView("original")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                  activeCompareView === "original" ? "bg-stone-900 text-white" : "text-stone-600"
                }`}
              >
                Original
              </button>
            </div>
          </div>

          {/* Viewport */}
          <div
            onMouseMove={(e) => {
              if (isDragging && activeCompareView === "slider") {
                const rect = e.currentTarget.getBoundingClientRect();
                handleSliderMove(e.clientX, rect);
              }
            }}
            onMouseUp={() => setIsDragging(false)}
            className="relative aspect-square w-full max-w-sm mx-auto overflow-hidden rounded-xl border border-stone-300 bg-black cursor-ew-resize select-none"
          >
            {activeCompareView === "slider" && (
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={origUrl} alt="Original Fundus" className="absolute inset-0 h-full w-full object-contain" />
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
                >
                  {enhancedLoadError ? (
                    <div className="flex h-full w-full flex-col items-center justify-center p-4 text-center text-xs text-stone-400">
                      <AlertTriangle className="h-6 w-6 text-amber-500 mb-2" />
                      <span>Enhanced asset currently unavailable</span>
                    </div>
                  ) : (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={enhancedUrl}
                      alt="Enhanced Fundus"
                      className="absolute inset-0 h-full w-full object-contain"
                      onError={() => setEnhancedLoadError(true)}
                    />
                  )}
                </div>
                <div
                  onMouseDown={() => setIsDragging(true)}
                  style={{ left: `${sliderPos}%` }}
                  className="absolute top-0 bottom-0 w-0.5 bg-white shadow-md cursor-ew-resize"
                >
                  <div className="absolute top-1/2 -mt-3 -ml-3 flex h-6 w-6 items-center justify-center rounded-full bg-white text-stone-700 shadow-md">
                    <SlidersHorizontal className="h-3 w-3" />
                  </div>
                </div>
              </>
            )}

            {activeCompareView === "enhanced" && (
              enhancedLoadError ? (
                <div className="flex h-full w-full flex-col items-center justify-center p-4 text-center text-xs text-stone-400">
                  <AlertTriangle className="h-6 w-6 text-amber-500 mb-2" />
                  <span>Enhanced asset currently unavailable</span>
                </div>
              ) : (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={enhancedUrl}
                  alt="Enhanced Fundus"
                  className="h-full w-full object-contain"
                  onError={() => setEnhancedLoadError(true)}
                />
              )
            )}

            {activeCompareView === "original" && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img src={origUrl} alt="Original Fundus" className="h-full w-full object-contain" />
            )}
          </div>

          <div className="rounded-lg bg-amber-50/80 p-2.5 text-[11px] text-amber-900 flex items-start space-x-2">
            <Info className="h-3.5 w-3.5 text-amber-700 shrink-0 mt-0.5" />
            <p>
              Enhancement improves image presentation but does not restore information that was not captured during acquisition.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
