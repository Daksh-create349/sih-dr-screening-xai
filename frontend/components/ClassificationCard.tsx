import React from "react";
import { Layers, Info } from "lucide-react";
import { ClassificationResponse } from "@/types/screening";

export interface ClassificationCardProps {
  classification: ClassificationResponse;
}

const DR_STAGES = [
  { grade: 0, label: "No DR", detail: "No abnormalities" },
  { grade: 1, label: "Mild DR", detail: "Microaneurysms only" },
  { grade: 2, label: "Moderate DR", detail: "More than mild, less than severe" },
  { grade: 3, label: "Severe DR", detail: "4-2-1 rule criteria" },
  { grade: 4, label: "Proliferative DR", detail: "Neovascularization present" },
];

export const ClassificationCard: React.FC<ClassificationCardProps> = ({
  classification,
}) => {
  const predGrade = classification.predicted_class;

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <Layers className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            02 &bull; Diabetic Retinopathy Assessment & Severity Grading
          </h3>
        </div>
        <span className="font-mono text-xs text-stone-400">
          Model: {classification.model_name || "EfficientNetB3"}
        </span>
      </div>

      {/* Primary Result Banner */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 rounded-xl bg-stone-50/70 p-4 border border-stone-200/70">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
            Predicted DR Stage
          </span>
          <h4 className="text-xl sm:text-2xl font-extrabold text-stone-950">
            Grade {predGrade} &mdash; {classification.predicted_label}
          </h4>
        </div>
        <div className="sm:text-right">
          <span className="text-[11px] font-bold uppercase tracking-wider text-stone-400">
            Model Confidence
          </span>
          <p className="font-mono text-xl sm:text-2xl font-extrabold text-emerald-900">
            {(classification.top_probability * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Horizontal Clinical Scale (Task 13) */}
      <div className="space-y-2 pt-1">
        <span className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
          ICDR Clinical Severity Scale
        </span>
        <div className="relative flex items-center justify-between pt-2">
          {/* Connecting Track */}
          <div className="absolute top-1/2 left-4 right-4 -translate-y-1/2 h-0.5 bg-stone-200" />

          {DR_STAGES.map(({ grade, label }) => {
            const isSelected = grade === predGrade;
            return (
              <div key={grade} className="relative z-10 flex flex-col items-center">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full font-mono text-xs font-bold transition-all ${
                    isSelected
                      ? "bg-emerald-950 text-white ring-4 ring-emerald-100 shadow-sm scale-110"
                      : "bg-white border border-stone-300 text-stone-600"
                  }`}
                >
                  {grade}
                </div>
                <span
                  className={`mt-1.5 text-[10px] whitespace-nowrap ${
                    isSelected ? "font-bold text-stone-900" : "text-stone-500"
                  }`}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Full 5-Class Probability Distribution (Task 12) */}
      <div className="space-y-2.5 pt-3 border-t border-stone-100">
        <span className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
          Full 5-Class Probability Distribution
        </span>

        <div className="space-y-2">
          {DR_STAGES.map(({ grade, label, detail }) => {
            const prob = classification.probabilities[grade] ?? 0;
            const isSelected = grade === predGrade;

            return (
              <div
                key={grade}
                className={`rounded-xl border p-2.5 transition-all ${
                  isSelected
                    ? "border-emerald-700 bg-emerald-50/50 shadow-2xs"
                    : "border-stone-100 bg-stone-50/40"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center space-x-2">
                    <span className={`font-bold ${isSelected ? "text-emerald-950" : "text-stone-800"}`}>
                      Grade {grade} &bull; {label}
                    </span>
                    <span className="text-[11px] text-stone-400 hidden sm:inline">
                      ({detail})
                    </span>
                  </div>
                  <span className="font-mono font-bold text-stone-900">
                    {(prob * 100).toFixed(2)}%
                  </span>
                </div>

                <div className="h-2 w-full overflow-hidden rounded-full bg-stone-200">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${
                      isSelected ? "bg-emerald-800" : "bg-stone-400"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, prob * 100))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex items-start space-x-2 pt-1 text-[11px] text-stone-500">
          <Info className="h-3.5 w-3.5 text-stone-400 shrink-0 mt-0.5" />
          <p>
            Model probabilities are outputs of the screening classifier and should not be interpreted as independently measured clinical likelihoods.
          </p>
        </div>
      </div>
    </div>
  );
};
