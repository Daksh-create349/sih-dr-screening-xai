import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle2, CircleDot } from "lucide-react";

export interface ProcessingStage {
  id: string;
  label: string;
  description: string;
}

const STAGES: ProcessingStage[] = [
  {
    id: "acquire",
    label: "Acquiring image",
    description: "Validating payload & format integrity",
  },
  {
    id: "iqa",
    label: "Assessing image quality",
    description: "Evaluating focus, illumination, FOV, centering",
  },
  {
    id: "classifier",
    label: "Running DR classifier",
    description: "Inferring 5-class ICDR severity with EfficientNetB3",
  },
  {
    id: "gradcam",
    label: "Generating feature attribution",
    description: "Computing retinal coordinate gradient activation map",
  },
  {
    id: "evidence",
    label: "Preparing evidence",
    description: "Synthesizing anatomical landmark correlation report",
  },
];

export const ProcessingState: React.FC = () => {
  const [activeStageIndex, setActiveStageIndex] = useState(0);

  useEffect(() => {
    // Stage pacing across expected ~2.4s execution window
    const timeouts = [
      setTimeout(() => setActiveStageIndex(1), 400),
      setTimeout(() => setActiveStageIndex(2), 900),
      setTimeout(() => setActiveStageIndex(3), 1500),
      setTimeout(() => setActiveStageIndex(4), 2100),
    ];

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200 bg-white p-6 shadow-xs animate-fade-in">
      {/* Header */}
      <div className="flex items-center space-x-3 border-b border-stone-100 pb-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-950 text-white shadow-xs">
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            Executing Screening Pipeline
          </h3>
          <p className="text-xs text-stone-500">
            Real-time multi-stage inference & explainability in progress
          </p>
        </div>
      </div>

      {/* Staged Pipeline Progression (Task 5) */}
      <div className="space-y-3">
        {STAGES.map((stage, idx) => {
          const isDone = idx < activeStageIndex;
          const isCurrent = idx === activeStageIndex;
          const isPending = idx > activeStageIndex;

          return (
            <div
              key={stage.id}
              className={`flex items-start space-x-3 rounded-xl p-2.5 transition-all duration-300 ${
                isCurrent
                  ? "bg-emerald-50/70 border border-emerald-200/80 shadow-2xs"
                  : isDone
                  ? "bg-stone-50/60 border border-stone-100 opacity-90"
                  : "opacity-40"
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                ) : isCurrent ? (
                  <CircleDot className="h-4 w-4 text-emerald-800 animate-pulse" aria-hidden="true" />
                ) : (
                  <div className="h-4 w-4 rounded-full border border-stone-300" aria-hidden="true" />
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-semibold ${
                      isCurrent
                        ? "text-emerald-950"
                        : isDone
                        ? "text-stone-800"
                        : "text-stone-400"
                    }`}
                  >
                    {stage.label}
                  </span>
                  {isCurrent && (
                    <span className="text-[10px] font-mono font-medium text-emerald-700 uppercase tracking-wide">
                      Processing...
                    </span>
                  )}
                  {isDone && (
                    <span className="text-[10px] font-mono text-stone-400 uppercase tracking-wide">
                      Complete
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-[11px] text-stone-500">
                  {stage.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-lg bg-stone-50 p-2.5 text-center text-[11px] text-stone-500">
        Processing live retinal photograph with local EfficientNetB3 &bull; Calibrated referral triage &bull; Grad-CAM
      </div>
    </div>
  );
};
