import React from "react";
import {
  Sparkles,
  RefreshCw,
  XCircle,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import { ScreeningSummaryBar } from "./ScreeningSummaryBar";
import { WorkflowTimeline } from "./WorkflowTimeline";
import { QualityDiagnostics } from "./QualityDiagnostics";
import { ClassificationCard } from "./ClassificationCard";
import { ReferableTriageCard } from "./ReferableTriageCard";
import { GradCAMViewer } from "./GradCAMViewer";
import { AnatomyViewer } from "./AnatomyViewer";
import { EvidenceCard } from "./EvidenceCard";
import { TechnicalDetails } from "./TechnicalDetails";
import { ProcessingState } from "./ProcessingState";
import { ResultSection } from "./ResultSection";
import { ScreeningResponse, ScreeningState } from "@/types/screening";

export interface AnalysisPanelProps {
  state: ScreeningState;
  result: ScreeningResponse | null;
  onAnalyze?: () => void;
  canAnalyze?: boolean;
  errorMessage?: string | null;
  onRetry?: () => void;
  onReset?: () => void;
  originalImageUrl?: string | null;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  state,
  result,
  onAnalyze,
  canAnalyze = false,
  errorMessage,
  onRetry,
  onReset,
  originalImageUrl,
}) => {
  const isAnalyzing = state === "ANALYZING";

  const iq = result?.image_quality;
  const cls = result?.classification;
  const ref = result?.referable;
  const exp = result?.explainability;
  const ev = result?.evidence;
  const anat = result?.anatomy;

  const isUngradeable = iq?.decision === "UNGRADEABLE" || result?.screening_status === "REJECTED_UNGRADEABLE";
  const isBorderline = iq?.decision === "BORDERLINE" || result?.screening_status === "BORDERLINE_PROCEEDED";

  return (
    <div className="space-y-6">
      {/* Top Action Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-stone-200/90 bg-white p-4 sm:p-5 shadow-xs no-print">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-stone-900">
            Clinical Screening & Decision Support System
          </h2>
          <p className="text-xs text-stone-500">
            End-to-end multi-stage optical grading, deep inference, and explainability
          </p>
        </div>

        {canAnalyze && (
          <button
            type="button"
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="inline-flex items-center space-x-2 rounded-xl bg-emerald-950 px-5 py-2.5 text-xs font-semibold text-white shadow-xs transition duration-200 hover:bg-emerald-900 hover:shadow-sm focus:outline-hidden focus:ring-2 focus:ring-emerald-600 disabled:opacity-60"
          >
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Analyze Image</span>
          </button>
        )}
      </div>

      {/* Error State Banner */}
      {state === "ERROR" && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/90 p-5 text-xs text-rose-800 animate-slide-up shadow-xs no-print">
          <div className="flex items-start space-x-3">
            <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" aria-hidden="true" />
            <div className="flex-1 space-y-1">
              <h4 className="font-bold text-sm text-rose-900">Screening Request Failed</h4>
              <p className="text-rose-700 leading-relaxed">
                {errorMessage ||
                  "An unexpected error occurred during pipeline execution. Please ensure the Python backend is running on port 8000 and retry."}
              </p>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="mt-3 inline-flex items-center space-x-1.5 rounded-xl bg-rose-700 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-rose-800"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry Analysis</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Analyzing Processing State (Task 5) */}
      {isAnalyzing && <ProcessingState />}

      {/* FULL RESULTS WORKSTATION PRESENTATION */}
      {state === "RESULT" && result && (
        <div className="space-y-6 animate-slide-up">
          {/* Summary Strip (Task 5) */}
          <ScreeningSummaryBar result={result} />

          {/* Workflow Pipeline Trace (Task 6, 31) */}
          <WorkflowTimeline result={result} />

          {/* UNGRADEABLE SAFETY HERO CARD (Task 17, 32) */}
          {isUngradeable ? (
            <div className="rounded-2xl border-2 border-rose-300 bg-rose-50/80 p-6 sm:p-7 shadow-xs space-y-4">
              <div className="flex items-start space-x-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-600 text-white shadow-sm">
                  <ShieldAlert className="h-6 w-6" />
                </div>
                <div className="space-y-1.5 flex-1">
                  <span className="rounded-md border border-rose-300 bg-rose-100 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-800 uppercase">
                    Safety Gatekeeper Engaged
                  </span>
                  <h3 className="text-xl font-bold text-rose-950">
                    Image Not Suitable for AI Screening
                  </h3>
                  <p className="text-xs leading-relaxed text-rose-800">
                    Optical characteristics failed minimum clinical diagnostic thresholds. In accordance with safety protocol, downstream deep-learning classification and Grad-CAM explainability were strictly bypassed to prevent misclassification.
                  </p>
                </div>
              </div>

              {iq?.recapture_guidance && (
                <div className="rounded-xl border border-rose-200 bg-white p-4 text-xs text-rose-950 space-y-1">
                  <strong className="font-bold text-rose-900 block">Recapture Guidance:</strong>
                  <p className="leading-relaxed">{iq.recapture_guidance}</p>
                </div>
              )}

              {onReset && (
                <div className="pt-1">
                  <button
                    type="button"
                    onClick={onReset}
                    className="inline-flex items-center space-x-2 rounded-xl bg-rose-900 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-rose-950"
                  >
                    <span>Upload Replacement Fundus Image</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              {/* 02. DR CLASSIFICATION (Task 11, 12, 13) */}
              {cls && <ClassificationCard classification={cls} />}

              {/* 03. REFERABLE SCREENING TRIAGE (Task 14, 15, 16) */}
              {ref && (
                <ReferableTriageCard
                  referable={ref}
                  isBorderline={isBorderline}
                />
              )}
            </>
          )}

          {/* 01. IMAGE QUALITY DIAGNOSTICS (Task 7, 8, 9, 10) */}
          {iq && (
            <QualityDiagnostics
              quality={iq}
              originalImageUrl={originalImageUrl}
            />
          )}

          {/* 04. MODEL ATTENTION (GRAD-CAM) (Task 17, 18, 19, 20) */}
          {!isUngradeable && exp?.gradcam_available && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 px-1">
                <span className="text-xs font-bold uppercase tracking-wider text-stone-400">
                  04 &bull; Model Feature Attribution
                </span>
              </div>
              <GradCAMViewer
                explainability={exp}
                anatomy={anat}
                originalImageUrl={originalImageUrl}
                resultId={result?.result_id}
              />
            </div>
          )}

          {/* 05. RETINAL ANATOMICAL CONTEXT (Task 21, 22, 23, 24, 25, 26) */}
          {!isUngradeable && anat && exp && (
            <AnatomyViewer
              anatomy={anat}
              explainability={exp}
              originalImageUrl={originalImageUrl}
            />
          )}

          {/* 06. EVIDENCE & RELIABILITY NARRATIVE (Task 27, 28, 29) */}
          {!isUngradeable && ev && iq && (
            <EvidenceCard
              evidence={ev}
              anatomy={anat}
              quality={iq}
              classification={cls}
              explainability={exp}
              resultId={result?.result_id}
            />
          )}

          {/* TECHNICAL SPECIFICATIONS & LATENCY (Task 30) */}
          <TechnicalDetails result={result} />
        </div>
      )}

      {/* WAITING FOR IMAGE / EMPTY INFERENCE PLACEHOLDER */}
      {state !== "RESULT" && !isAnalyzing && (
        <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-500">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-stone-900">
              Awaiting Fundus Photograph Analysis
            </h3>
            <p className="text-xs text-stone-500 max-w-sm mx-auto leading-relaxed">
              Select or drop a color fundus image on the left to begin multi-stage optical quality assessment, ICDR classification, and Grad-CAM explainability.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
