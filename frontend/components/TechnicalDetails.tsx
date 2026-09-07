import React, { useState } from "react";
import { Cpu, ChevronDown, ChevronUp, Layers } from "lucide-react";
import { ScreeningResponse } from "@/types/screening";

export interface TechnicalDetailsProps {
  result: ScreeningResponse;
}

export const TechnicalDetails: React.FC<TechnicalDetailsProps> = ({ result }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const proc = result.processing;
  const b = proc.breakdown_ms || {};

  const techRows = [
    { label: "SIH Challenge & Problem ID", value: "SIH 2026 PS 26038 (MathWorks MedTech)" },
    { label: "Classifier Architecture", value: result.classification?.model_name || "EfficientNetB3_DR (Keras Frozen)" },
    { label: "Optic Disc Segmenter", value: "U-Net ResNet34 (Val Dice: 0.9859, IDRiD Parts A & C)" },
    { label: "Exudates Segmenter", value: "U-Net ResNet34 (Val Dice: 0.7580, IDRiD Part A)" },
    { label: "Segmentation Ground Truth", value: "10,409 Patches (512 × 512, IDRiD Dataset)" },
    { label: "Tensor Input Shape", value: "[None, 384, 384, 3]" },
    { label: "Output Prediction Vector", value: "[None, 5] (Softmax Probability Distribution)" },
    { label: "Feature Attribution Layer", value: result.explainability?.layer_name || "top_conv" },
    { label: "Native Heatmap Resolution", value: "12 × 12 convolutional grid" },
    { label: "Display Heatmap Resolution", value: `${result.explainability?.heatmap_dimensions?.[0] || 384} × ${result.explainability?.heatmap_dimensions?.[1] || 384} px (Retinal Coordinate Projection)` },
    { label: "Referable Threshold Cutoff", value: `${(result.referable?.threshold || 0.33).toFixed(2)} (Calibrated operating point)` },
    { label: "Total Pipeline Latency", value: `${proc.total_time_ms.toFixed(1)} ms (${(proc.total_time_ms / 1000).toFixed(2)} s)` },
    { label: "Image Quality Execution", value: `${b.iqa_ms?.toFixed(1) ?? "0.0"} ms` },
    { label: "Deep Learning Inference", value: `${b.classification_ms?.toFixed(1) ?? "0.0"} ms` },
    { label: "Grad-CAM Gradient Backprop", value: `${b.gradcam_ms?.toFixed(1) ?? "0.0"} ms` },
    { label: "IDRiD Lesions & Evidence", value: `${b.evidence_ms?.toFixed(1) ?? "0.0"} ms` },
  ];

  return (
    <div className="rounded-2xl border border-stone-200/90 bg-white overflow-hidden shadow-xs">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-stone-50 transition text-left"
      >
        <div className="flex items-center space-x-2.5">
          <Cpu className="h-4 w-4 text-emerald-800" />
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-stone-900">
              Technical Pipeline Specifications & Runtime Metrics
            </h4>
            <p className="text-[11px] text-stone-500">
              Deep-learning architecture, IDRiD segmenters, tensor shapes, gradient layers & execution breakdown
            </p>
          </div>
        </div>

        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-stone-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-stone-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-stone-100 bg-stone-50/40 p-5 divide-y divide-stone-100 text-xs">
          {techRows.map((row) => (
            <div key={row.label} className="py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <span className="font-medium text-stone-600">{row.label}</span>
              <span className="font-mono text-[11px] font-semibold text-stone-900 sm:text-right">
                {row.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
