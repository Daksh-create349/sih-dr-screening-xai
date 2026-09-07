import React from "react";
import {
  FileCheck2,
  Layers,
  Sparkles,
  Clock,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { ScreeningResponse } from "@/types/screening";

export interface ScreeningSummaryBarProps {
  result: ScreeningResponse;
}

export const ScreeningSummaryBar: React.FC<ScreeningSummaryBarProps> = ({
  result,
}) => {
  const iq = result.image_quality;
  const cls = result.classification;
  const ref = result.referable;
  const proc = result.processing;
  const isUngradeable = iq.decision === "UNGRADEABLE";

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-2xl border border-stone-200/90 bg-white p-4 shadow-xs animate-slide-up">
      {/* 1. Quality */}
      <div className="flex items-center space-x-3 border-r border-stone-100 pr-2">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
            iq.decision === "GOOD"
              ? "bg-emerald-100 text-emerald-800"
              : iq.decision === "BORDERLINE"
              ? "bg-amber-100 text-amber-800"
              : "bg-rose-100 text-rose-800"
          }`}
        >
          <FileCheck2 className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
            Image Quality
          </span>
          <span className="truncate block text-xs font-bold text-stone-900">
            {iq.decision} ({iq.overall_score.toFixed(0)}/100)
          </span>
        </div>
      </div>

      {/* 2. DR Grade */}
      <div className="flex items-center space-x-3 border-r border-stone-100 pr-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-800">
          <Layers className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
            DR Classification
          </span>
          <span className="truncate block text-xs font-bold text-stone-900">
            {isUngradeable
              ? "Bypassed"
              : cls
              ? `Grade ${cls.predicted_class} &bull; ${cls.predicted_label}`
              : "N/A"}
          </span>
        </div>
      </div>

      {/* 3. Referable Status */}
      <div className="flex items-center space-x-3 border-r border-stone-100 pr-2">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
            ref?.is_referable
              ? "bg-amber-100 text-amber-800"
              : "bg-emerald-100 text-emerald-800"
          }`}
        >
          {ref?.is_referable ? (
            <AlertTriangle className="h-4 w-4" />
          ) : (
            <ShieldCheck className="h-4 w-4" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
            Triage Status
          </span>
          <span className="truncate block text-xs font-bold text-stone-900">
            {isUngradeable ? "Bypassed" : ref ? ref.status : "N/A"}
          </span>
        </div>
      </div>

      {/* 4. Processing Time */}
      <div className="flex items-center space-x-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-stone-100 text-stone-800">
          <Clock className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-stone-400">
            Total Latency
          </span>
          <span className="font-mono block text-xs font-bold text-stone-900">
            {(proc.total_time_ms / 1000).toFixed(2)}s
          </span>
        </div>
      </div>
    </div>
  );
};
