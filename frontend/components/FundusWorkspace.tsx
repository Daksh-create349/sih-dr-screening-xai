import React, { useState, useEffect } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize,
  Minimize,
  Eye,
  FileText,
  Maximize2,
  HardDrive,
  X,
  Contrast,
  SlidersHorizontal,
  Sun,
} from "lucide-react";
import { UploadedImageMeta } from "@/types/screening";

export interface FundusWorkspaceProps {
  imageMeta: UploadedImageMeta;
  onRemove?: () => void;
  disabled?: boolean;
}

export const FundusWorkspace: React.FC<FundusWorkspaceProps> = ({
  imageMeta,
  onRemove,
  disabled = false,
}) => {
  const [zoom, setZoom] = useState(1);
  const [contrast, setContrast] = useState(100);
  const [brightness, setBrightness] = useState(100);
  const [isRedFree, setIsRedFree] = useState(false);
  const [showAdjustments, setShowAdjustments] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Keyboard navigation (+, -, 0, Escape)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "+" || e.key === "=") {
        e.preventDefault();
        setZoom((prev) => Math.min(3, prev + 0.25));
      } else if (e.key === "-") {
        e.preventDefault();
        setZoom((prev) => Math.max(0.75, prev - 0.25));
      } else if (e.key === "0") {
        e.preventDefault();
        setZoom(1);
      } else if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullscreen]);

  const handleZoomIn = () => setZoom((prev) => Math.min(3, prev + 0.25));
  const handleZoomOut = () => setZoom((prev) => Math.max(0.75, prev - 0.25));
  const handleResetZoom = () => setZoom(1);

  const handleResetAdjustments = () => {
    setContrast(100);
    setBrightness(100);
    setIsRedFree(false);
  };

  const hasCustomAdjustments = contrast !== 100 || brightness !== 100 || isRedFree;

  return (
    <div className={`space-y-3.5 ${isFullscreen ? "fixed inset-0 z-50 bg-stone-950/95 p-6 flex flex-col" : ""}`}>
      {/* Workspace Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-2.5">
        <div className="flex items-center space-x-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-stone-100 text-stone-700">
            <Eye className="h-3.5 w-3.5" />
          </span>
          <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700">
            Fundus Imaging Workspace
          </h3>
          <span className="rounded-md border border-stone-200 bg-stone-50 px-2 py-0.5 font-mono text-[10px] text-stone-500">
            {(zoom * 100).toFixed(0)}%
          </span>
        </div>

        {/* Zoom, Contrast & Fullscreen Controls */}
        <div className="flex items-center space-x-1.5">
          {/* Contrast & Filter Toggle Button */}
          <button
            type="button"
            onClick={() => setShowAdjustments(!showAdjustments)}
            disabled={disabled}
            aria-label="Toggle contrast and image adjustments"
            title="Image Contrast & Filter Adjustments"
            className={`rounded-lg border px-2.5 py-1 text-xs font-semibold flex items-center space-x-1.5 shadow-2xs transition ${
              showAdjustments || hasCustomAdjustments
                ? "border-amber-400 bg-amber-50 text-amber-900"
                : "border-stone-200 bg-white text-stone-600 hover:bg-stone-100 hover:text-stone-900"
            }`}
          >
            <Contrast className="h-3.5 w-3.5" />
            <span>Contrast</span>
            {hasCustomAdjustments && (
              <span className="h-1.5 w-1.5 rounded-full bg-amber-600" />
            )}
          </button>

          <div className="inline-flex rounded-lg border border-stone-200 bg-white p-0.5 shadow-2xs">
            <button
              type="button"
              onClick={handleZoomOut}
              disabled={disabled || zoom <= 0.75}
              aria-label="Zoom out"
              title="Zoom out (-)"
              className="rounded-md p-1.5 text-stone-600 hover:bg-stone-100 hover:text-stone-900 disabled:opacity-40"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={handleResetZoom}
              disabled={disabled || zoom === 1}
              aria-label="Reset zoom"
              title="Reset zoom (0)"
              className="rounded-md p-1.5 text-stone-600 hover:bg-stone-100 hover:text-stone-900 disabled:opacity-40"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={handleZoomIn}
              disabled={disabled || zoom >= 3}
              aria-label="Zoom in"
              title="Zoom in (+)"
              className="rounded-md p-1.5 text-stone-600 hover:bg-stone-100 hover:text-stone-900 disabled:opacity-40"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            disabled={disabled}
            aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen viewer"}
            title={isFullscreen ? "Exit fullscreen (Esc)" : "Fullscreen viewer"}
            className="rounded-lg border border-stone-200 bg-white p-2 text-stone-600 shadow-2xs hover:bg-stone-100 hover:text-stone-900 disabled:opacity-40"
          >
            {isFullscreen ? (
              <Minimize className="h-3.5 w-3.5" />
            ) : (
              <Maximize className="h-3.5 w-3.5" />
            )}
          </button>

          {onRemove && !isFullscreen && (
            <button
              type="button"
              onClick={onRemove}
              disabled={disabled}
              aria-label="Remove image"
              title="Remove image"
              className="rounded-lg border border-stone-200 bg-white p-2 text-rose-600 shadow-2xs hover:bg-rose-50 disabled:opacity-40"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* PACS Contrast & Brightness Adjustment Drawer */}
      {showAdjustments && (
        <div className="rounded-xl border border-stone-200 bg-stone-50/90 p-3.5 text-xs space-y-3 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-stone-900 text-[11px] uppercase tracking-wider flex items-center space-x-1.5">
              <SlidersHorizontal className="h-3.5 w-3.5 text-amber-700" />
              <span>Diagnostic Contrast &amp; Lighting Controls</span>
            </span>
            {hasCustomAdjustments && (
              <button
                type="button"
                onClick={handleResetAdjustments}
                className="text-[11px] font-semibold text-amber-800 hover:underline"
              >
                Reset Controls
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Contrast Slider */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-stone-600">
                <span className="font-medium flex items-center space-x-1">
                  <Contrast className="h-3 w-3" />
                  <span>Contrast</span>
                </span>
                <span className="font-mono font-bold text-stone-900">{contrast}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="200"
                step="5"
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
                className="w-full accent-amber-600 cursor-pointer h-1.5 rounded-lg bg-stone-200"
              />
            </div>

            {/* Brightness Slider */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-stone-600">
                <span className="font-medium flex items-center space-x-1">
                  <Sun className="h-3 w-3" />
                  <span>Brightness</span>
                </span>
                <span className="font-mono font-bold text-stone-900">{brightness}%</span>
              </div>
              <input
                type="range"
                min="60"
                max="160"
                step="5"
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
                className="w-full accent-amber-600 cursor-pointer h-1.5 rounded-lg bg-stone-200"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-1.5 border-t border-stone-200/80">
            <button
              type="button"
              onClick={() => setIsRedFree(!isRedFree)}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition flex items-center space-x-1.5 ${
                isRedFree
                  ? "bg-emerald-700 text-white shadow-xs"
                  : "border border-stone-300 bg-white text-stone-700 hover:bg-stone-100"
              }`}
            >
              <span>Red-Free Filter (Green Channel)</span>
              {isRedFree && <span>✓ Active</span>}
            </button>
            <span className="text-[10px] text-stone-500">
              Enhanced vessel &amp; hemorrhage visibility
            </span>
          </div>
        </div>
      )}

      {/* Main Retinal Image Viewport (Task 3) */}
      <div
        className={`relative flex items-center justify-center overflow-hidden rounded-2xl border border-stone-200 bg-stone-950 shadow-sm transition-all duration-300 ${
          isFullscreen ? "flex-1 w-full" : "aspect-square w-full"
        }`}
      >
        <div
          className="flex h-full w-full items-center justify-center overflow-auto p-2"
          style={{ cursor: zoom > 1 ? "grab" : "default" }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageMeta.previewUrl}
            alt={`Color retinal fundus photograph: ${imageMeta.filename}`}
            className="max-h-full max-w-full object-contain transition-all duration-150"
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: "center center",
              filter: `contrast(${contrast}%) brightness(${brightness}%) ${
                isRedFree
                  ? "grayscale(100%) contrast(145%) brightness(105%)"
                  : ""
              }`,
            }}
          />
        </div>

        {/* Optical Alignment Reticle Marker (Subtle Center Target) */}
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-20"
          aria-hidden="true"
        >
          <div className="h-16 w-16 rounded-full border border-dashed border-white" />
          <div className="absolute h-4 w-0.5 bg-white" />
          <div className="absolute h-0.5 w-4 bg-white" />
        </div>
      </div>

      {/* Metadata Row (Task 3) */}
      <div className="grid grid-cols-3 gap-2 rounded-xl border border-stone-200/80 bg-stone-50/70 p-3 text-xs">
        <div className="space-y-0.5">
          <span className="flex items-center space-x-1 text-[11px] font-medium text-stone-500">
            <FileText className="h-3 w-3 text-stone-400" />
            <span>File Name</span>
          </span>
          <p
            className="truncate font-semibold text-stone-800"
            title={imageMeta.filename}
          >
            {imageMeta.filename}
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="flex items-center space-x-1 text-[11px] font-medium text-stone-500">
            <Maximize2 className="h-3 w-3 text-stone-400" />
            <span>Resolution</span>
          </span>
          <p className="font-semibold text-stone-800">
            {imageMeta.dimensions.width} &times; {imageMeta.dimensions.height} px
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="flex items-center space-x-1 text-[11px] font-medium text-stone-500">
            <HardDrive className="h-3 w-3 text-stone-400" />
            <span>File Size</span>
          </span>
          <p className="font-semibold text-stone-800">
            {imageMeta.fileSizeFormatted}
          </p>
        </div>
      </div>
    </div>
  );
};
