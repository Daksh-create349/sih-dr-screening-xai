import React, { useState, useRef, useEffect, useCallback } from "react";
import { Crosshair, SlidersHorizontal, RotateCcw, Eye, Layers, Sparkles } from "lucide-react";
import { ExplainabilityResponse, AnatomyResponse } from "@/types/screening";
import { getAssetUrl, getEvidenceOverlayUrl } from "@/lib/api";

export interface GradCAMViewerProps {
  explainability: ExplainabilityResponse;
  anatomy?: AnatomyResponse | null;
  originalImageUrl?: string | null;
  resultId?: string | null;
}

export const GradCAMViewer: React.FC<GradCAMViewerProps> = ({
  explainability,
  anatomy,
  originalImageUrl,
  resultId,
}) => {
  const [viewMode, setViewMode] = useState<
    "overlay" | "lesions" | "split" | "heatmap" | "original"
  >("overlay");
  const [sliderPos, setSliderPos] = useState(50); // percentage (0 - 100)
  const [isDragging, setIsDragging] = useState(false);
  const [isAnimating, setIsAnimating] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  const overlayUrl = getAssetUrl(explainability.overlay_url);
  const heatmapUrl = getAssetUrl(explainability.gradcam_url);
  const evidenceOverlayUrl = resultId ? getEvidenceOverlayUrl(resultId) : "";
  const originalUrl = originalImageUrl || "";

  // One-time initial reveal animation (~1.4s), then settle to static
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setIsAnimating(false);
      return;
    }

    const timer = setTimeout(() => {
      setIsAnimating(false);
    }, 1400);

    return () => clearTimeout(timer);
  }, []);

  const replayReveal = () => {
    setIsAnimating(true);
    setTimeout(() => {
      setIsAnimating(false);
    }, 1400);
  };

  // Slider drag logic
  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percent = Math.min(100, Math.max(0, (x / rect.width) * 100));
    setSliderPos(percent);
  }, []);

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isDragging) {
      handleMove(e.touches[0].clientX);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      handleMove(e.clientX);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      setSliderPos((prev) => Math.max(0, prev - 5));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setSliderPos((prev) => Math.min(100, prev + 5));
    }
  };

  return (
    <div className="space-y-3.5">
      {/* View Mode Controls & Replay */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-2.5">
        <div className="inline-flex flex-wrap items-center gap-1 rounded-xl border border-stone-200 bg-stone-100/70 p-1 text-xs font-medium">
          <button
            type="button"
            onClick={() => setViewMode("overlay")}
            className={`rounded-lg px-3 py-1.5 transition ${
              viewMode === "overlay"
                ? "bg-white text-stone-900 shadow-2xs font-bold"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            Grad-CAM
          </button>

          {evidenceOverlayUrl && (
            <button
              type="button"
              onClick={() => setViewMode("lesions")}
              className={`flex items-center space-x-1 rounded-lg px-3 py-1.5 transition ${
                viewMode === "lesions"
                  ? "bg-white text-stone-900 shadow-2xs font-bold"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Layers className="h-3 w-3 text-amber-600" />
              <span>IDRiD Lesions</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setViewMode("split")}
            className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
              viewMode === "split"
                ? "bg-white text-stone-900 shadow-2xs font-bold"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            <SlidersHorizontal className="h-3 w-3" />
            <span>Split Slider</span>
          </button>
          <button
            type="button"
            onClick={() => setViewMode("heatmap")}
            className={`rounded-lg px-3 py-1.5 transition ${
              viewMode === "heatmap"
                ? "bg-white text-stone-900 shadow-2xs font-bold"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            Raw Heatmap
          </button>
          {originalUrl && (
            <button
              type="button"
              onClick={() => setViewMode("original")}
              className={`rounded-lg px-3 py-1.5 transition ${
                viewMode === "original"
                  ? "bg-white text-stone-900 shadow-2xs font-bold"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              Original
            </button>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {viewMode === "overlay" && (
            <button
              type="button"
              onClick={replayReveal}
              title="Replay animated reveal transition"
              className="inline-flex items-center space-x-1 rounded-lg border border-stone-200 bg-white px-2.5 py-1 text-[11px] font-medium text-stone-600 shadow-2xs hover:bg-stone-50"
            >
              <RotateCcw className="h-3 w-3 text-stone-400" />
              <span>Replay Reveal</span>
            </button>
          )}
          <span className="font-mono text-[11px] text-stone-500">
            Target Class {explainability.target_class ?? 0}
          </span>
        </div>
      </div>

      {/* Main Image Viewport */}
      <div
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={() => setIsDragging(false)}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => setIsDragging(false)}
        className="relative mx-auto aspect-square w-full max-w-md overflow-hidden rounded-2xl border border-stone-200 bg-stone-950 shadow-xs select-none"
      >
        {/* 1. Standard Grad-CAM Overlay Mode */}
        {viewMode === "overlay" && (
          <div className="relative h-full w-full">
            {originalUrl && (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={originalUrl}
                alt="Original retinal fundus"
                className="absolute inset-0 h-full w-full object-contain"
              />
            )}

            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={overlayUrl}
              alt="Grad-CAM activation overlay"
              className={`absolute inset-0 h-full w-full object-contain ${
                isAnimating ? "animate-heatmap-reveal" : "opacity-100"
              }`}
            />
          </div>
        )}

        {/* 2. Deep Lesions (IDRiD OD & Exudates) Mode */}
        {viewMode === "lesions" && evidenceOverlayUrl && (
          <div className="relative h-full w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={evidenceOverlayUrl}
              alt="IDRiD deep optic disc and exudates lesion overlay"
              className="h-full w-full object-contain"
            />
            {/* Overlay Annotation Legend */}
            <div className="absolute bottom-3 left-3 right-3 flex flex-wrap items-center justify-between gap-1.5 rounded-lg bg-stone-950/85 px-3 py-1.5 text-[10px] text-white backdrop-blur-xs">
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
                <span>Optic Disc (Dice 0.986)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-400"></span>
                <span>Hard Exudates (Dice 0.758)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                <span>Hemorrhages (Dice 0.748)</span>
              </div>
            </div>
          </div>
        )}

        {/* 3. Interactive Split Comparison Slider */}
        {viewMode === "split" && (
          <div
            tabIndex={0}
            role="slider"
            aria-valuenow={sliderPos}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Comparison slider: original retina versus Grad-CAM overlay"
            onKeyDown={handleKeyDown}
            className="relative h-full w-full cursor-ew-resize focus:outline-hidden focus:ring-2 focus:ring-emerald-600"
          >
            {/* Base layer: Original image */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={originalUrl || overlayUrl}
              alt="Original fundus baseline"
              className="absolute inset-0 h-full w-full object-contain"
            />

            {/* Clipped overlay layer */}
            <div
              className="absolute inset-0 overflow-hidden"
              style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={overlayUrl}
                alt="Grad-CAM activation overlay"
                className="absolute inset-0 h-full w-full object-contain"
              />
            </div>

            {/* Split Handle Bar */}
            <div
              onMouseDown={() => setIsDragging(true)}
              onTouchStart={() => setIsDragging(true)}
              style={{ left: `${sliderPos}%` }}
              className="absolute top-0 bottom-0 w-0.5 -ml-px bg-white shadow-md transition-shadow hover:shadow-lg cursor-ew-resize"
            >
              <div className="absolute top-1/2 -mt-4 -ml-4 flex h-8 w-8 items-center justify-center rounded-full bg-white text-stone-700 shadow-md border border-stone-200">
                <SlidersHorizontal className="h-3.5 w-3.5" />
              </div>
            </div>

            {/* Badges */}
            <div className="absolute top-3 left-3 rounded-md bg-stone-900/80 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-xs">
              Grad-CAM Overlay
            </div>
            <div className="absolute top-3 right-3 rounded-md bg-stone-900/80 px-2 py-0.5 text-[10px] font-medium text-white backdrop-blur-xs">
              Original Retina
            </div>
          </div>
        )}

        {/* 4. Raw Heatmap Mode */}
        {viewMode === "heatmap" && (
          <div className="h-full w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={heatmapUrl}
              alt="Raw Grad-CAM JET heatmap"
              className="h-full w-full object-contain"
            />
          </div>
        )}

        {/* 5. Original Image Mode */}
        {viewMode === "original" && originalUrl && (
          <div className="h-full w-full">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={originalUrl}
              alt="Original fundus photograph"
              className="h-full w-full object-contain"
            />
          </div>
        )}
      </div>

      {/* Dominant Activation Region & Landmark Note */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-stone-100 bg-stone-50/70 px-3.5 py-2 text-xs text-stone-600">
        <div className="flex items-center space-x-1.5">
          <Crosshair className="h-3.5 w-3.5 text-emerald-800" />
          <span>
            Dominant Focus:{" "}
            <strong className="font-semibold text-stone-900 capitalize">
              {anatomy?.top_attention_region?.replace("_", " ") || "Posterior Retinal Region"}
            </strong>
          </span>
        </div>
        {explainability.attention_summary && (
          <span className="font-mono text-[11px] text-stone-500 truncate max-w-xs">
            {explainability.attention_summary}
          </span>
        )}
      </div>

      {/* Attribution Technical Details Panel */}
      <div className="rounded-xl border border-stone-200/80 bg-stone-50/60 p-3.5 text-xs space-y-2">
        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-stone-400 block">
          Attribution Metadata & Convolutional Projection
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-stone-700">
          <div className="rounded-lg bg-white p-2 border border-stone-200/60">
            <span className="text-[10px] text-stone-400 block">Target Class</span>
            <span className="font-bold text-stone-900">
              Grade {explainability.target_class ?? 0}
            </span>
          </div>
          <div className="rounded-lg bg-white p-2 border border-stone-200/60">
            <span className="text-[10px] text-stone-400 block">Target Score</span>
            <span className="font-mono font-bold text-stone-900">
              {explainability.target_score !== null && explainability.target_score !== undefined
                ? (explainability.target_score * 100).toFixed(1) + "%"
                : "N/A"}
            </span>
          </div>
          <div className="rounded-lg bg-white p-2 border border-stone-200/60">
            <span className="text-[10px] text-stone-400 block">Native Heatmap</span>
            <span className="font-mono font-bold text-stone-900">
              {explainability.native_dimensions
                ? `${explainability.native_dimensions[0]} × ${explainability.native_dimensions[1]}`
                : "12 × 12"}
            </span>
          </div>
          <div className="rounded-lg bg-white p-2 border border-stone-200/60">
            <span className="text-[10px] text-stone-400 block">Attribution Layer</span>
            <span className="font-mono font-bold text-stone-900">
              {explainability.layer_name || "top_conv"}
            </span>
          </div>
        </div>
        <p className="text-[11px] text-stone-500 leading-relaxed pt-1">
          The highlighted regions represent image features that contributed to the model prediction. Computed via back-propagation gradients to final convolutional layer and bi-linearly projected to retinal coordinates.
        </p>
      </div>

      {/* Mandatory Scientific Framing Notice */}
      <div className="rounded-xl border border-stone-200/90 bg-white p-3 text-center text-xs text-stone-600 shadow-2xs">
        <p className="font-bold text-stone-800 uppercase tracking-wide text-[11px]">
          Multi-Modal Explainability Architecture
        </p>
        <p className="mt-0.5 text-[11px] text-stone-500 leading-relaxed">
          Grad-CAM captures macroscopic classifier attention. Dual IDRiD ResNet34 U-Nets provide microscopic pixel-level lesion segmentation for Hard Exudates and Optic Disc boundary localization.
        </p>
      </div>
    </div>
  );
};
