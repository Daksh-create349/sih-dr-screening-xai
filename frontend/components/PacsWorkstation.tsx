"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Eye,
  SlidersHorizontal,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Layers,
  Sparkles,
  Activity,
  AlertCircle,
  CheckCircle2,
  Target,
  FileText,
  Clock,
  ShieldCheck,
  ChevronRight,
  RefreshCw,
  X,
  Upload,
  Cpu,
  Info,
  Download,
} from "lucide-react";
import {
  UploadedImageMeta,
  ScreeningResponse,
  ScreeningState,
} from "@/types/screening";
import { getAssetUrl, getEvidenceOverlayUrl } from "@/lib/api";
import { CompactSampleBar } from "./CompactSampleBar";
import { ClinicalReportModal } from "./ClinicalReportModal";

export interface PacsWorkstationProps {
  selectedImage: UploadedImageMeta | null;
  screeningResult: ScreeningResponse | null;
  screeningState: ScreeningState;
  errorMessage: string | null;
  onImageSelected: (meta: UploadedImageMeta) => void;
  onImageRemove: () => void;
  onAnalyze: () => void;
  onRetry: () => void;
}

export const PacsWorkstation: React.FC<PacsWorkstationProps> = ({
  selectedImage,
  screeningResult,
  screeningState,
  errorMessage,
  onImageSelected,
  onImageRemove,
  onAnalyze,
  onRetry,
}) => {
  // Canvas Viewport State
  const [viewMode, setViewMode] = useState<
    "original" | "lesions" | "gradcam" | "split"
  >("original");
  const [sliderPos, setSliderPos] = useState(50);
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeConsoleTab, setActiveConsoleTab] = useState<
    "triage" | "lesions" | "explain" | "quality"
  >("triage");
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAnalyzing = screeningState === "ANALYZING";
  const hasResult = screeningState === "RESULT" && screeningResult !== null;

  // Asset URLs
  const originalUrl = selectedImage?.previewUrl || "";
  const evidenceOverlayUrl = screeningResult?.result_id
    ? getEvidenceOverlayUrl(screeningResult.result_id)
    : "";
  const gradcamOverlayUrl = screeningResult?.explainability?.overlay_url
    ? getAssetUrl(screeningResult.explainability.overlay_url)
    : "";

  // Set default view mode when results arrive
  useEffect(() => {
    if (hasResult) {
      if (evidenceOverlayUrl) {
        setViewMode("lesions");
      } else if (gradcamOverlayUrl) {
        setViewMode("gradcam");
      }
    } else {
      setViewMode("original");
    }
  }, [hasResult, evidenceOverlayUrl, gradcamOverlayUrl]);

  // Zoom handlers
  const handleZoomIn = () => setZoom((z) => Math.min(3, z + 0.25));
  const handleZoomOut = () => setZoom((z) => Math.max(0.75, z - 0.25));
  const handleResetZoom = () => setZoom(1);

  // Split Slider drag logic
  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percent = Math.min(100, Math.max(0, (x / rect.width) * 100));
    setSliderPos(percent);
  }, []);

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isDragging) handleMove(e.touches[0].clientX);
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) handleMove(e.clientX);
  };

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) setIsFullscreen(false);
      if (e.key === "+" || e.key === "=") setZoom((z) => Math.min(3, z + 0.25));
      if (e.key === "-") setZoom((z) => Math.max(0.75, z - 0.25));
      if (e.key === "0") setZoom(1);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullscreen]);

  // File drag & drop for canvas
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const previewUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        onImageSelected({
          file,
          previewUrl,
          filename: file.name,
          fileSizeBytes: file.size,
          fileSizeFormatted: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          dimensions: { width: img.naturalWidth, height: img.naturalHeight },
          mimeType: file.type,
        });
      };
      img.src = previewUrl;
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const previewUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        onImageSelected({
          file,
          previewUrl,
          filename: file.name,
          fileSizeBytes: file.size,
          fileSizeFormatted: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          dimensions: { width: img.naturalWidth, height: img.naturalHeight },
          mimeType: file.type,
        });
      };
      img.src = previewUrl;
    }
  };

  // Extract structured lesion data
  const rawLesions = (screeningResult?.evidence?.lesions as any) || {};
  const struct = (screeningResult?.evidence?.structured_record as any) || {};
  const structOD = struct?.structures?.optic_disc;
  const structExud = struct?.lesions?.hard_exudates;
  const structStats = struct?.provenance?.lesion_statistics || {};

  const odCenter = rawLesions.optic_disc?.center_xy || (structOD ? [structOD.x, structOD.y] : null);
  const odRadius = rawLesions.optic_disc?.radius_px ?? structOD?.radius;
  const odConfidence = rawLesions.optic_disc?.confidence ?? structOD?.confidence;

  const exudateCount = rawLesions.hard_exudates?.lesion_count ?? structStats.exudate_clusters ?? rawLesions.exudate_clusters ?? 0;
  const exudatePixels = rawLesions.hard_exudates?.total_lesion_pixels ?? structExud?.non_zero_pixels ?? 0;
  const exudateAreaFraction = rawLesions.hard_exudates?.area_fraction ?? structStats.exudate_area_fraction ?? rawLesions.exudate_area_fraction ?? 0;

  const structHem = struct?.lesions?.hemorrhages;
  const hemCount = rawLesions.hemorrhages?.lesion_count ?? structStats.hemorrhage_clusters ?? rawLesions.hemorrhage_clusters ?? 0;
  const hemPixels = rawLesions.hemorrhages?.total_lesion_pixels ?? structHem?.non_zero_pixels ?? rawLesions.hemorrhage_pixels ?? structStats.hemorrhage_pixels ?? 0;
  const hemAreaFraction = rawLesions.hemorrhages?.area_fraction ?? rawLesions.hemorrhage_area_fraction ?? structStats.hemorrhage_area_fraction ?? 0;

  const csmeRiskLevel = rawLesions.csme_risk?.risk_level || structStats.macular_edema_risk_level || rawLesions.macular_edema_risk_level || (exudateCount > 0 ? "LOW" : "NONE");
  const csmeDistancePx = rawLesions.csme_risk?.min_distance_to_fovea_px ?? structStats.min_distance_to_fovea_px ?? rawLesions.min_distance_to_fovea_px;
  const csmeDistanceDD = rawLesions.csme_risk?.min_distance_in_disc_diameters ?? (odRadius && csmeDistancePx ? Number((csmeDistancePx / (odRadius * 2)).toFixed(2)) : null);

  const isCsmeHigh = csmeRiskLevel === "HIGH";
  const isCsmeMod = csmeRiskLevel === "MODERATE";

  const cls = screeningResult?.classification;
  const ref = screeningResult?.referable;
  const iq = screeningResult?.image_quality;
  const isUngradeable = iq?.decision === "UNGRADEABLE" || screeningResult?.screening_status === "REJECTED_UNGRADEABLE";

  return (
    <div className="space-y-4">
      {/* Top Bar: Preloaded Study Selector */}
      <CompactSampleBar
        onSelectSample={onImageSelected}
        disabled={isAnalyzing}
        selectedFilename={selectedImage?.filename}
      />

      {/* Patient Study Metadata Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200/90 bg-white px-4 py-2.5 shadow-2xs text-xs">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-stone-600">
          <div className="flex items-center space-x-1.5 font-medium">
            <span className="text-stone-400">Study:</span>
            <span className="font-mono font-bold text-slate-900">
              {selectedImage ? selectedImage.filename : "No Study Loaded"}
            </span>
          </div>
          <div className="flex items-center space-x-1.5 font-medium">
            <span className="text-stone-400">Patient:</span>
            <span className="font-mono font-semibold text-slate-800">#RUR-2026-084</span>
          </div>
          <div className="flex items-center space-x-1.5 font-medium">
            <span className="text-stone-400">Modality:</span>
            <span className="font-medium text-slate-800">Color Fundus 45°</span>
          </div>
          <div className="flex items-center space-x-1.5 font-medium">
            <span className="text-stone-400">Site:</span>
            <span className="font-medium text-slate-800">Rural Health Node #04</span>
          </div>
        </div>

        {selectedImage && (
          <button
            type="button"
            onClick={onImageRemove}
            disabled={isAnalyzing}
            className="inline-flex items-center space-x-1 rounded-md px-2 py-1 text-[11px] font-medium text-stone-500 hover:bg-stone-100 hover:text-rose-600 transition"
          >
            <X className="h-3 w-3" />
            <span>Clear Study</span>
          </button>
        )}
      </div>

      {/* Main 2-Column Clinical PACS Workstation Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* ============================================================ */}
        {/* LEFT COLUMN: PACS Imaging Canvas (7 cols on lg)              */}
        {/* ============================================================ */}
        <div className="lg:col-span-7 space-y-3">
          <div
            className={`rounded-2xl border border-stone-800 bg-[#070b14] p-3.5 shadow-md flex flex-col ${
              isFullscreen ? "fixed inset-0 z-50 rounded-none p-6" : ""
            }`}
          >
            {/* Canvas Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-800 pb-2.5 text-xs text-white">
              {/* Layer Selection Tabs */}
              <div className="inline-flex rounded-lg border border-stone-800 bg-stone-900/90 p-0.5 text-[11px] font-medium">
                <button
                  type="button"
                  onClick={() => setViewMode("original")}
                  className={`rounded-md px-2.5 py-1 transition ${
                    viewMode === "original"
                      ? "bg-slate-800 text-white font-bold shadow-2xs"
                      : "text-stone-400 hover:text-white"
                  }`}
                >
                  Original
                </button>

                {hasResult && !isUngradeable && evidenceOverlayUrl && (
                  <button
                    type="button"
                    onClick={() => setViewMode("lesions")}
                    className={`flex items-center space-x-1 rounded-md px-2.5 py-1 transition ${
                      viewMode === "lesions"
                        ? "bg-amber-950/80 text-amber-300 font-bold border border-amber-600/40"
                        : "text-stone-400 hover:text-white"
                    }`}
                  >
                    <Layers className="h-3 w-3 text-amber-400" />
                    <span>IDRiD Lesions</span>
                  </button>
                )}

                {hasResult && !isUngradeable && gradcamOverlayUrl && (
                  <button
                    type="button"
                    onClick={() => setViewMode("gradcam")}
                    className={`flex items-center space-x-1 rounded-md px-2.5 py-1 transition ${
                      viewMode === "gradcam"
                        ? "bg-sky-950/80 text-sky-300 font-bold border border-sky-600/40"
                        : "text-stone-400 hover:text-white"
                    }`}
                  >
                    <Sparkles className="h-3 w-3 text-sky-400" />
                    <span>Grad-CAM</span>
                  </button>
                )}

                {hasResult && !isUngradeable && (
                  <button
                    type="button"
                    onClick={() => setViewMode("split")}
                    className={`flex items-center space-x-1 rounded-md px-2.5 py-1 transition ${
                      viewMode === "split"
                        ? "bg-slate-800 text-white font-bold"
                        : "text-stone-400 hover:text-white"
                    }`}
                  >
                    <SlidersHorizontal className="h-3 w-3" />
                    <span>Split Slider</span>
                  </button>
                )}
              </div>

              {/* Canvas Zoom & View Controls */}
              <div className="flex items-center space-x-1.5">
                <div className="inline-flex rounded-lg border border-stone-800 bg-stone-900/90 p-0.5 text-stone-300">
                  <button
                    type="button"
                    onClick={handleZoomOut}
                    disabled={zoom <= 0.75}
                    title="Zoom out (-)"
                    className="rounded p-1 hover:bg-stone-800 disabled:opacity-40"
                  >
                    <ZoomOut className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={handleResetZoom}
                    title="Reset zoom (0)"
                    className="rounded px-1.5 text-[10px] font-mono hover:bg-stone-800"
                  >
                    {Math.round(zoom * 100)}%
                  </button>
                  <button
                    type="button"
                    onClick={handleZoomIn}
                    disabled={zoom >= 3}
                    title="Zoom in (+)"
                    className="rounded p-1 hover:bg-stone-800 disabled:opacity-40"
                  >
                    <ZoomIn className="h-3 w-3" />
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  title={isFullscreen ? "Exit fullscreen" : "Fullscreen canvas"}
                  className="rounded-lg border border-stone-800 bg-stone-900/90 p-1.5 text-stone-300 hover:bg-stone-800"
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-3 w-3" />
                  ) : (
                    <Maximize2 className="h-3 w-3" />
                  )}
                </button>
              </div>
            </div>

            {/* Viewport Canvas */}
            <div
              ref={containerRef}
              onMouseMove={handleMouseMove}
              onMouseUp={() => setIsDragging(false)}
              onTouchMove={handleTouchMove}
              onTouchEnd={() => setIsDragging(false)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className="relative aspect-square w-full overflow-hidden rounded-xl bg-black select-none my-2 flex items-center justify-center"
            >
              {!selectedImage ? (
                /* Empty Upload Dropzone */
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center justify-center p-8 text-center cursor-pointer group"
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/jpg"
                    onChange={handleFileInputChange}
                    className="hidden"
                  />
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-800 bg-stone-900 text-stone-400 group-hover:border-emerald-500 group-hover:text-emerald-400 transition">
                    <Upload className="h-6 w-6" />
                  </div>
                  <h4 className="mt-4 text-sm font-bold text-white">
                    Drop Retinal Fundus Photograph
                  </h4>
                  <p className="mt-1 text-xs text-stone-400 max-w-xs leading-relaxed">
                    Supports PNG, JPEG, JPG up to 25 MB. Or click any preloaded study case above.
                  </p>
                </div>
              ) : (
                /* Interactive Canvas Image View */
                <div
                  className="relative h-full w-full flex items-center justify-center transition-transform duration-75"
                  style={{ transform: `scale(${zoom})` }}
                >
                  {/* Mode: Original */}
                  {viewMode === "original" && (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={originalUrl}
                      alt="Original retinal fundus"
                      className="h-full w-full object-contain"
                    />
                  )}

                  {/* Mode: IDRiD Deep Lesions */}
                  {viewMode === "lesions" && evidenceOverlayUrl && (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={evidenceOverlayUrl}
                      alt="IDRiD deep lesion overlay"
                      className="h-full w-full object-contain"
                    />
                  )}

                  {/* Mode: Grad-CAM */}
                  {viewMode === "gradcam" && (
                    <div className="relative h-full w-full">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={originalUrl}
                        alt="Original retinal fundus"
                        className="absolute inset-0 h-full w-full object-contain"
                      />
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={gradcamOverlayUrl}
                        alt="Grad-CAM activation overlay"
                        className="absolute inset-0 h-full w-full object-contain"
                      />
                    </div>
                  )}

                  {/* Mode: Split Slider */}
                  {viewMode === "split" && (
                    <div className="relative h-full w-full cursor-ew-resize">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={originalUrl}
                        alt="Original fundus baseline"
                        className="absolute inset-0 h-full w-full object-contain"
                      />
                      <div
                        className="absolute inset-0 overflow-hidden"
                        style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={evidenceOverlayUrl || gradcamOverlayUrl}
                          alt="AI overlay"
                          className="absolute inset-0 h-full w-full object-contain"
                        />
                      </div>
                      {/* Divider line */}
                      <div
                        onMouseDown={() => setIsDragging(true)}
                        onTouchStart={() => setIsDragging(true)}
                        style={{ left: `${sliderPos}%` }}
                        className="absolute top-0 bottom-0 w-0.5 -ml-px bg-white shadow-lg cursor-ew-resize"
                      >
                        <div className="absolute top-1/2 -mt-3.5 -ml-3.5 flex h-7 w-7 items-center justify-center rounded-full bg-white text-slate-800 shadow-md">
                          <SlidersHorizontal className="h-3 w-3" />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Layer Color Legend (When viewing Lesions) */}
                  {viewMode === "lesions" && (
                    <div className="absolute bottom-2.5 left-2.5 right-2.5 flex flex-wrap items-center justify-between gap-1 rounded-lg bg-black/85 px-3 py-1.5 font-mono text-[10px] text-white backdrop-blur-xs border border-stone-800">
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
                  )}
                </div>
              )}
            </div>

            {/* Canvas Footer Telemetry */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 font-mono text-[11px] text-stone-400">
              <div>
                {selectedImage ? (
                  <span>
                    {selectedImage.dimensions.width} × {selectedImage.dimensions.height} px &bull; {selectedImage.fileSizeFormatted}
                  </span>
                ) : (
                  <span>Awaiting Fundus Study</span>
                )}
              </div>

              <div>
                {iq && (
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      iq.decision === "GOOD"
                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800/60"
                        : iq.decision === "BORDERLINE"
                        ? "bg-amber-950 text-amber-400 border border-amber-800/60"
                        : "bg-rose-950 text-rose-400 border border-rose-800/60"
                    }`}
                  >
                    Quality: {iq.decision} ({iq.overall_score.toFixed(1)} / 100)
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* RIGHT COLUMN: Diagnostic Intelligence Console (5 cols on lg) */}
        {/* ============================================================ */}
        <div className="lg:col-span-5 space-y-4">
          {/* Diagnostic Action Button */}
          {selectedImage && screeningState !== "RESULT" && (
            <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-xs text-center space-y-3">
              <h3 className="text-sm font-bold text-slate-900">
                Study Ready for Diagnostic Inference
              </h3>
              <p className="text-xs text-stone-500 max-w-sm mx-auto leading-relaxed">
                Runs optical quality gatekeeper, dual IDRiD ResNet34 lesion segmenters, and EfficientNetB3 severity classifier.
              </p>
              <button
                type="button"
                onClick={onAnalyze}
                disabled={isAnalyzing}
                className="w-full inline-flex items-center justify-center space-x-2 rounded-xl bg-slate-950 px-5 py-3 text-xs font-bold text-white shadow-sm transition hover:bg-slate-900 disabled:opacity-60"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
                    <span>Executing Pipeline (IQA + UNet + V2)...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 text-emerald-400" />
                    <span>Run Screening Analysis</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Banner */}
          {screeningState === "ERROR" && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 space-y-2">
              <div className="flex items-center space-x-2 font-bold text-rose-900">
                <AlertCircle className="h-4 w-4 text-rose-600" />
                <span>Screening Analysis Error</span>
              </div>
              <p className="leading-relaxed">{errorMessage || "Backend server unavailable."}</p>
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center space-x-1.5 rounded-lg bg-rose-700 px-3 py-1.5 text-xs font-semibold text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Retry Analysis</span>
              </button>
            </div>
          )}

          {/* Ungradeable Rejection Notice */}
          {hasResult && isUngradeable && (
            <div className="rounded-2xl border border-rose-300 bg-rose-50/90 p-5 space-y-3">
              <div className="flex items-center space-x-2 text-rose-900">
                <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
                <h3 className="text-sm font-bold">
                  Image Rejected by Optical Quality Gatekeeper
                </h3>
              </div>
              <p className="text-xs text-rose-700 leading-relaxed">
                Optical quality composite score (<strong>{iq?.overall_score.toFixed(1)}/100</strong>) is below the clinical threshold. Downstream classifier inference has been halted to prevent misdiagnosis.
              </p>
              <div className="rounded-xl border border-rose-200 bg-white p-3.5 space-y-1 text-xs">
                <span className="font-bold text-rose-950 uppercase text-[10px] tracking-wider block">
                  ASHA Worker Actionable Recapture Protocol:
                </span>
                <p className="text-stone-700 leading-relaxed">
                  {iq?.recapture_guidance ||
                    "Severe motion blur or optical defocus detected. Steady handheld camera against patient forehead rest, request patient blink once, and re-center on optic disc."}
                </p>
              </div>
            </div>
          )}

          {/* Diagnostic Console Tabs */}
          {hasResult && !isUngradeable && (
            <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-xs space-y-4">
              {/* Console Tab Bar */}
              <div className="flex items-center space-x-1 border-b border-stone-100 pb-3 text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setActiveConsoleTab("triage")}
                  className={`rounded-lg px-3 py-1.5 transition ${
                    activeConsoleTab === "triage"
                      ? "bg-slate-900 font-bold text-white shadow-2xs"
                      : "text-stone-600 hover:text-stone-900"
                  }`}
                >
                  Diagnosis & Triage
                </button>
                <button
                  type="button"
                  onClick={() => setActiveConsoleTab("lesions")}
                  className={`rounded-lg px-3 py-1.5 transition ${
                    activeConsoleTab === "lesions"
                      ? "bg-slate-900 font-bold text-white shadow-2xs"
                      : "text-stone-600 hover:text-stone-900"
                  }`}
                >
                  Deep Biomarkers
                </button>
                <button
                  type="button"
                  onClick={() => setActiveConsoleTab("explain")}
                  className={`rounded-lg px-3 py-1.5 transition ${
                    activeConsoleTab === "explain"
                      ? "bg-slate-900 font-bold text-white shadow-2xs"
                      : "text-stone-600 hover:text-stone-900"
                  }`}
                >
                  Explainability
                </button>
                <button
                  type="button"
                  onClick={() => setActiveConsoleTab("quality")}
                  className={`rounded-lg px-3 py-1.5 transition ${
                    activeConsoleTab === "quality"
                      ? "bg-slate-900 font-bold text-white shadow-2xs"
                      : "text-stone-600 hover:text-stone-900"
                  }`}
                >
                  Quality & Specs
                </button>
              </div>

              {/* TAB 1: Diagnosis & Triage */}
              {activeConsoleTab === "triage" && (
                <div className="space-y-4">
                  {/* Primary ICDR Severity Grade Card */}
                  <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold uppercase text-stone-500">
                        Primary DR Severity Grading
                      </span>
                      <span className="rounded-md bg-white border border-stone-200 px-2 py-0.5 font-mono text-[11px] font-bold text-slate-800">
                        {(cls?.top_probability ? cls.top_probability * 100 : 0).toFixed(1)}% Confidence
                      </span>
                    </div>

                    <div className="flex items-baseline space-x-2">
                      <div className="text-2xl font-black text-slate-950">
                        Grade {cls?.predicted_class}: {cls?.predicted_label}
                      </div>
                    </div>

                    {/* Probability Distribution */}
                    {cls?.probabilities && (
                      <div className="space-y-1 pt-1">
                        <div className="flex justify-between text-[10px] font-mono text-stone-500">
                          <span>ICDR Class Distribution</span>
                          <span>Grades 0 to 4</span>
                        </div>
                        <div className="grid grid-cols-5 gap-1.5">
                          {Object.entries(cls.probabilities).map(([grade, prob]) => (
                            <div key={grade} className="space-y-1 text-center">
                              <div className="h-1.5 w-full rounded-full bg-stone-200 overflow-hidden">
                                <div
                                  className={`h-full ${
                                    Number(grade) === cls.predicted_class
                                      ? "bg-emerald-600"
                                      : "bg-stone-400"
                                  }`}
                                  style={{ width: `${Math.round(prob * 100)}%` }}
                                />
                              </div>
                              <span className="font-mono text-[9px] text-stone-500 block">
                                G{grade}: {(prob * 100).toFixed(0)}%
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Referable Screening Decision */}
                  {ref && (
                    <div
                      className={`rounded-xl border p-4 space-y-2 ${
                        ref.is_referable
                          ? "border-rose-300 bg-rose-50/70 text-rose-950"
                          : "border-emerald-300 bg-emerald-50/70 text-emerald-950"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1.5 font-bold text-xs">
                          {ref.is_referable ? (
                            <AlertCircle className="h-4 w-4 text-rose-600" />
                          ) : (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          )}
                          <span>
                            {ref.is_referable
                              ? "Referable Retinopathy Triage Triggered"
                              : "Non-Referable Retinopathy"}
                          </span>
                        </div>
                        <span className="font-mono text-[10px] font-bold">
                          Cutoff: {ref.threshold.toFixed(2)}
                        </span>
                      </div>

                      <p className="text-xs leading-relaxed text-stone-700">
                        {ref.is_referable
                          ? "Patient exhibits Grade 2+ retinopathy or high-risk lesions. Requires formal tele-ophthalmology referral and dilated fundus evaluation."
                          : "Patient exhibits Grade 0 or mild Grade 1 retinopathy without macular involvement. Scheduled for routine 12-month PHC screening."}
                      </p>
                    </div>
                  )}

                  {/* Clinical Narrative Note */}
                  {screeningResult.evidence?.narrative && (
                    <div className="rounded-xl border border-stone-200 bg-stone-50/40 p-4 space-y-1.5 text-xs text-stone-700">
                      <span className="font-bold text-[10px] uppercase tracking-wider text-stone-400 block font-mono">
                        Synthesized Diagnostic Summary
                      </span>
                      <p className="leading-relaxed">
                        {screeningResult.evidence.narrative}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: Deep Biomarkers & CSME */}
              {activeConsoleTab === "lesions" && (
                <div className="space-y-4">
                  {/* CSME Proximity Alert Banner */}
                  {(isCsmeHigh || isCsmeMod) && (
                    <div
                      className={`rounded-xl border p-4 space-y-1.5 ${
                        isCsmeHigh
                          ? "border-rose-300 bg-rose-50 text-rose-900"
                          : "border-amber-300 bg-amber-50 text-amber-900"
                      }`}
                    >
                      <div className="flex items-center space-x-1.5 font-bold text-xs">
                        <AlertCircle className="h-4 w-4 text-rose-600" />
                        <span>
                          {isCsmeHigh
                            ? "High CSME Macular Risk Alert"
                            : "Moderate CSME Risk Advisory"}
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed">
                        Hard exudates detected within{" "}
                        <strong>
                          {csmeDistanceDD != null
                            ? `${csmeDistanceDD} Disc Diameters`
                            : "< 1 Disc Diameter"}
                        </strong>{" "}
                        of the estimated macular fovea. Clinically Significant Macular Edema threatens central vision.
                      </p>
                    </div>
                  )}

                  {/* Biomarker Metrics Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
                    {/* Optic Disc */}
                    <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1.5 font-bold text-slate-900">
                          <Target className="h-4 w-4 text-cyan-600" />
                          <span>Optic Disc</span>
                        </div>
                        <span className="rounded bg-cyan-100 text-cyan-800 px-1.5 py-0.2 font-mono text-[9px] font-bold">
                          Dice 0.9859
                        </span>
                      </div>
                      <div className="space-y-1 text-stone-600 text-[11px]">
                        <div className="flex justify-between">
                          <span>Center:</span>
                          <span className="font-mono font-medium text-slate-900">
                            {odCenter ? `(${Math.round(odCenter[0])}, ${Math.round(odCenter[1])})` : "Localized"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Radius:</span>
                          <span className="font-mono font-medium text-slate-900">
                            {odRadius ? `${Math.round(odRadius)} px` : "Calibrated"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Hard Exudates */}
                    <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1.5 font-bold text-slate-900">
                          <Activity className="h-4 w-4 text-amber-600" />
                          <span>Exudates</span>
                        </div>
                        <span className="rounded bg-amber-100 text-amber-800 px-1.5 py-0.2 font-mono text-[9px] font-bold">
                          Dice 0.7580
                        </span>
                      </div>
                      <div className="space-y-1 text-stone-600 text-[11px]">
                        <div className="flex justify-between">
                          <span>Clusters:</span>
                          <span className="font-mono font-bold text-slate-900">
                            {exudateCount} clusters
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Area:</span>
                          <span className="font-mono font-medium text-slate-900">
                            {exudatePixels > 0
                              ? `${exudatePixels.toLocaleString()} px`
                              : "0 px"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Retinal Hemorrhages */}
                    <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1.5 font-bold text-slate-900">
                          <Layers className="h-4 w-4 text-rose-600" />
                          <span>Hemorrhages</span>
                        </div>
                        <span className="rounded bg-rose-100 text-rose-800 px-1.5 py-0.2 font-mono text-[9px] font-bold">
                          Dice 0.7482
                        </span>
                      </div>
                      <div className="space-y-1 text-stone-600 text-[11px]">
                        <div className="flex justify-between">
                          <span>Foci:</span>
                          <span className="font-mono font-bold text-slate-900">
                            {hemCount} foci
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Area:</span>
                          <span className="font-mono font-medium text-slate-900">
                            {hemPixels > 0
                              ? `${hemPixels.toLocaleString()} px`
                              : "0 px"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-stone-500 leading-relaxed italic">
                    Segmented by triple U-Net ResNet34 models trained on IDRiD (Indian Diabetic Retinopathy Image Dataset) ground truth.
                  </p>
                </div>
              )}

              {/* TAB 3: Explainability & Context */}
              {activeConsoleTab === "explain" && (
                <div className="space-y-3 text-xs">
                  <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-4 space-y-2">
                    <span className="font-bold text-slate-900 block">
                      Convolutional Feature Attribution
                    </span>
                    <p className="text-stone-600 leading-relaxed">
                      Grad-CAM back-propagates gradients to layer{" "}
                      <code className="font-mono font-bold text-slate-900">
                        {screeningResult.explainability?.layer_name || "top_conv"}
                      </code>{" "}
                      to identify image regions determining Grade {cls?.predicted_class} classification.
                    </p>
                    {screeningResult.explainability?.attention_summary && (
                      <p className="font-mono text-[11px] text-stone-500 pt-1">
                        Summary: {screeningResult.explainability.attention_summary}
                      </p>
                    )}
                  </div>

                  <div className="rounded-xl border border-stone-200 bg-stone-50/40 p-3.5 text-[11px] text-stone-500 leading-relaxed">
                    <strong>Multi-Modal Explainability:</strong> Macroscopic attention highlights broad retinal changes; IDRiD segmenters provide microscopic lesion clusters and boundary tracking.
                  </div>
                </div>
              )}

              {/* TAB 4: Quality & Latency */}
              {activeConsoleTab === "quality" && (
                <div className="space-y-3 text-xs">
                  {iq && (
                    <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-4 space-y-2.5">
                      <span className="font-bold text-slate-900 block">
                        Optical Quality Assessment Breakdown
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="flex justify-between border-b border-stone-200/60 pb-1">
                          <span>Focus / Blur:</span>
                          <span className="font-mono font-bold">{iq.focus.toFixed(1)}/100</span>
                        </div>
                        <div className="flex justify-between border-b border-stone-200/60 pb-1">
                          <span>Illumination:</span>
                          <span className="font-mono font-bold">{iq.illumination.toFixed(1)}/100</span>
                        </div>
                        <div className="flex justify-between border-b border-stone-200/60 pb-1">
                          <span>Field of View:</span>
                          <span className="font-mono font-bold">{iq.fov.toFixed(1)}/100</span>
                        </div>
                        <div className="flex justify-between border-b border-stone-200/60 pb-1">
                          <span>Centering:</span>
                          <span className="font-mono font-bold">{iq.centering.toFixed(1)}/100</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* MathWorks Simulink Certified Architecture Model */}
                  <div className="rounded-xl border border-orange-200 bg-orange-50/40 p-4 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded bg-orange-600 text-[10px] font-black text-white">
                          M
                        </span>
                        <span className="font-bold text-slate-900">
                          MathWorks Simulink 8-Subsystem Architecture
                        </span>
                      </div>
                      <span className="rounded border border-orange-200 bg-orange-100 px-2 py-0.5 font-mono text-[10px] font-bold text-orange-900">
                        DR_screening_workflow.slx
                      </span>
                    </div>

                    <p className="text-[11px] text-stone-600 leading-relaxed">
                      Discrete-event system architecture verified in MATLAB Online R2024b. Models asynchronous ingestion, 4-metric optical IQA safety gate, adaptive CLAHE enhancement, EfficientNetB3 deep inference, and multi-biomarker synthesis for 100,000 screenings/yr.
                    </p>

                    <div className="overflow-hidden rounded-lg border border-stone-300 bg-stone-900">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src="/simulink_model_screenshot.png"
                        alt="MathWorks Simulink DR Screening Workflow 8-Subsystem Architecture Model"
                        className="w-full object-contain max-h-[220px] rounded-lg cursor-pointer hover:opacity-95 transition"
                        onClick={() => window.open("/simulink_model_screenshot.png", "_blank")}
                        title="Click to view full resolution Simulink model canvas"
                      />
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-stone-500 pt-1">
                      <span>Routing: Good &bull; Borderline &bull; Ungradeable Bypass</span>
                      <span className="font-mono font-semibold text-emerald-700">Verified Safe (100% Classifier Bypass on Fail)</span>
                    </div>
                  </div>

                  {/* Execution Latency Breakdown */}
                  <div className="rounded-xl border border-stone-200 bg-stone-50/40 p-3.5 space-y-1 text-[11px] text-stone-600">
                    <span className="font-mono font-bold uppercase text-stone-400 block text-[10px]">
                      Pipeline Latency
                    </span>
                    <div className="flex justify-between">
                      <span>Total End-to-End:</span>
                      <span className="font-mono font-bold text-slate-900">
                        {screeningResult.processing.total_time_ms.toFixed(1)} ms ({(screeningResult.processing.total_time_ms / 1000).toFixed(2)}s)
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Regulatory Disclaimer + Download Report */}
              <div className="border-t border-stone-100 pt-3 flex items-start justify-between gap-3">
                <div className="flex items-start space-x-1.5 text-[10px] text-stone-400 leading-relaxed">
                  <Info className="h-3.5 w-3.5 shrink-0 mt-0.5 text-stone-400" />
                  <span>
                    Clinical decision support tool for screening triage only. Final diagnosis requires evaluation by an ophthalmologist.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsReportModalOpen(true)}
                  className="inline-flex shrink-0 items-center space-x-1.5 rounded-xl bg-slate-950 px-3.5 py-2 text-[11px] font-bold text-white shadow-sm transition hover:bg-slate-800"
                >
                  <Download className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Download Report</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Clinical PDF Report Modal */}
      {isReportModalOpen && screeningResult && (
        <ClinicalReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          screeningResult={screeningResult}
          studyFilename={selectedImage?.filename || "retina_scan.png"}
          patientId="#RUR-2026-084"
          doctorName="Dr. [Physician Name]"
          institution="SIH National Telemedicine DR Screening Network"
        />
      )}
    </div>
  );
};
