import React, { useEffect, useState } from "react";
import { ImageQualityResponse, QualityStatus } from "@/types/screening";

export interface QualityGaugeProps {
  quality: ImageQualityResponse;
}

export const QualityGauge: React.FC<QualityGaugeProps> = ({ quality }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const targetScore = quality.overall_score;
  const status: QualityStatus = quality.decision;

  useEffect(() => {
    let startTimestamp: number | null = null;
    const duration = 1000; // 1 second ease-out

    // Check if reduced motion is preferred
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setAnimatedScore(targetScore);
      return;
    }

    let frameId: number;
    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(eased * targetScore);

      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setAnimatedScore(targetScore);
      }
    };

    frameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameId);
  }, [targetScore]);

  // SVG circular gauge geometry
  const radius = 38;
  const circumference = 2 * Math.PI * radius; // ~238.76
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  const colorConfig = {
    GOOD: {
      stroke: "#047857", // emerald-700
      text: "text-emerald-800",
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      bar: "bg-emerald-600",
      label: "GOOD QUALITY",
    },
    BORDERLINE: {
      stroke: "#d97706", // amber-600
      text: "text-amber-800",
      bg: "bg-amber-50",
      border: "border-amber-200",
      bar: "bg-amber-500",
      label: "BORDERLINE QUALITY",
    },
    UNGRADEABLE: {
      stroke: "#e11d48", // rose-600
      text: "text-rose-800",
      bg: "bg-rose-50",
      border: "border-rose-200",
      bar: "bg-rose-600",
      label: "UNGRADEABLE",
    },
  }[status] || {
    stroke: "#475569",
    text: "text-slate-800",
    bg: "bg-slate-50",
    border: "border-slate-200",
    bar: "bg-slate-600",
    label: status,
  };

  const components = [
    { label: "Focus / Sharpness", value: quality.focus },
    { label: "Illumination Uniformity", value: quality.illumination },
    { label: "Field of View (FOV)", value: quality.fov },
    { label: "Centering / Positioning", value: quality.centering },
  ];

  return (
    <div className="space-y-4">
      {/* Gauge & Main Rating Row */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 rounded-xl border border-stone-100 bg-stone-50/50 p-4">
        {/* Animated Radial Meter */}
        <div className="relative flex shrink-0 items-center justify-center">
          <svg className="h-24 w-24 -rotate-90 transform" viewBox="0 0 96 96">
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke="#e7e5e4"
              strokeWidth="7"
              fill="transparent"
            />
            <circle
              cx="48"
              cy="48"
              r={radius}
              stroke={colorConfig.stroke}
              strokeWidth="7"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              style={{ transition: "stroke-dashoffset 0.1s linear" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="font-mono text-xl font-bold tracking-tight text-stone-900">
              {animatedScore.toFixed(0)}
            </span>
            <span className="text-[10px] font-semibold text-stone-400 uppercase">/ 100</span>
          </div>
        </div>

        {/* Status Copy */}
        <div className="flex-1 text-center sm:text-left space-y-1">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
            <span className="text-xs font-semibold text-stone-400 uppercase tracking-wide">
              Optical Assessment
            </span>
            <span
              className={`rounded-md border px-2 py-0.5 font-mono text-[11px] font-bold ${colorConfig.bg} ${colorConfig.border} ${colorConfig.text}`}
            >
              {colorConfig.label}
            </span>
          </div>
          <p className="text-xs leading-relaxed text-stone-600">
            {status === "GOOD" &&
              "Optical characteristics meet certified quality criteria for downstream deep-learning classification."}
            {status === "BORDERLINE" &&
              "Optical characteristics are borderline. Enhancement was evaluated under quality triage protocol."}
            {status === "UNGRADEABLE" &&
              "Quality is insufficient for automated screening. Downstream classifier is strictly bypassed."}
          </p>
        </div>
      </div>

      {/* Component Sub-scores */}
      <div className="space-y-2 pt-1">
        <span className="block text-[11px] font-semibold tracking-wide text-stone-500 uppercase">
          Component Optical Parameters
        </span>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {components.map((comp) => {
            const compValue = Math.min(100, Math.max(0, comp.value));
            return (
              <div
                key={comp.label}
                className="rounded-lg border border-stone-200/80 bg-white p-2.5 shadow-2xs"
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-medium text-stone-700">{comp.label}</span>
                  <span className="font-mono font-bold text-stone-900">
                    {comp.value.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${
                      compValue >= 60
                        ? "bg-emerald-600"
                        : compValue >= 40
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    }`}
                    style={{ width: `${compValue}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
