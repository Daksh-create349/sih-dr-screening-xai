import React from "react";
import { CheckCircle2, CircleOff, AlertOctagon, GitCommit } from "lucide-react";
import { ScreeningResponse } from "@/types/screening";

export interface WorkflowTimelineProps {
  result: ScreeningResponse;
}

export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({ result }) => {
  const iq = result.image_quality;
  const proc = result.processing;
  const b = proc.breakdown_ms || {};
  const isUngradeable = iq.decision === "UNGRADEABLE";
  const enhancementApplied = iq.enhancement_applied;

  const stages = [
    {
      step: "01",
      name: "Image Acquisition",
      desc: `Ingested ${result.filename}`,
      status: "COMPLETED",
      latency: b.image_decoding_ms ? `${b.image_decoding_ms.toFixed(0)} ms` : null,
    },
    {
      step: "02",
      name: "Quality Assessment",
      desc: `Focus, illumination, FOV, centering (${iq.overall_score.toFixed(0)}/100)`,
      status: "COMPLETED",
      latency: b.iqa_ms ? `${b.iqa_ms.toFixed(0)} ms` : null,
    },
    {
      step: "03",
      name: "Quality Gatekeeper",
      desc: isUngradeable ? "Halted — image ungradeable" : "Approved for inference",
      status: isUngradeable ? "BLOCKED" : "COMPLETED",
      latency: null,
    },
    {
      step: "04",
      name: "Optical Enhancement",
      desc: enhancementApplied ? "Applied CLAHE contrast enhancement" : "Skipped — quality adequate",
      status: isUngradeable ? "SKIPPED" : enhancementApplied ? "COMPLETED" : "SKIPPED",
      latency: b.enhancement_ms ? `${b.enhancement_ms.toFixed(0)} ms` : null,
    },
    {
      step: "05",
      name: "DR Classification",
      desc: isUngradeable ? "Bypassed by safety gatekeeper" : `EfficientNetB3 (Grade ${result.classification?.predicted_class})`,
      status: isUngradeable ? "BLOCKED" : "COMPLETED",
      latency: b.classification_ms ? `${b.classification_ms.toFixed(0)} ms` : null,
    },
    {
      step: "06",
      name: "Referable Triage",
      desc: isUngradeable ? "Bypassed" : `Calibrated cutoff = 0.33 (${result.referable?.status})`,
      status: isUngradeable ? "BLOCKED" : "COMPLETED",
      latency: b.referable_ms ? `${b.referable_ms.toFixed(0)} ms` : null,
    },
    {
      step: "07",
      name: "Model Attribution",
      desc: isUngradeable ? "Bypassed" : "Grad-CAM back-warped to native retina",
      status: isUngradeable ? "BLOCKED" : "COMPLETED",
      latency: b.gradcam_ms ? `${b.gradcam_ms.toFixed(0)} ms` : null,
    },
    {
      step: "08",
      name: "Evidence Synthesis",
      desc: isUngradeable ? "Bypassed" : "Landmarks & structured clinical narrative",
      status: isUngradeable ? "BLOCKED" : "COMPLETED",
      latency: b.evidence_ms ? `${b.evidence_ms.toFixed(0)} ms` : null,
    },
  ];

  return (
    <div className="rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      <div className="mb-4 flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <GitCommit className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            Analysis Workflow Pipeline Trace
          </h3>
        </div>
        <span className="font-mono text-xs text-stone-400">
          Total: {proc.total_time_ms.toFixed(0)} ms
        </span>
      </div>

      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
        {stages.map((stage) => {
          const isDone = stage.status === "COMPLETED";
          const isBlocked = stage.status === "BLOCKED";

          return (
            <div
              key={stage.step}
              className={`rounded-xl border p-3 transition-all ${
                isDone
                  ? "border-emerald-200/90 bg-emerald-50/40"
                  : isBlocked
                  ? "border-rose-200 bg-rose-50/60"
                  : "border-stone-100 bg-stone-50/40 text-stone-400"
              }`}
            >
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-mono text-[10px] font-bold text-stone-400">
                  {stage.step}
                </span>
                <span
                  className={`flex items-center space-x-1 rounded-md px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                    isDone
                      ? "bg-emerald-100 text-emerald-800"
                      : isBlocked
                      ? "bg-rose-100 text-rose-800"
                      : "bg-stone-200/70 text-stone-600"
                  }`}
                >
                  {isDone ? (
                    <>
                      <CheckCircle2 className="h-2.5 w-2.5 mr-0.5" />
                      <span>Completed</span>
                    </>
                  ) : isBlocked ? (
                    <>
                      <AlertOctagon className="h-2.5 w-2.5 mr-0.5" />
                      <span>Blocked</span>
                    </>
                  ) : (
                    <>
                      <CircleOff className="h-2.5 w-2.5 mr-0.5" />
                      <span>Skipped</span>
                    </>
                  )}
                </span>
              </div>

              <h4 className="text-xs font-bold text-stone-900 mt-1">{stage.name}</h4>
              <p className="text-[11px] text-stone-500 mt-0.5 line-clamp-1">{stage.desc}</p>

              {stage.latency && (
                <span className="mt-2 block font-mono text-[10px] text-stone-400">
                  {stage.latency}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
