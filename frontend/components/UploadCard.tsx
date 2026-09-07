import React, { useRef, useState } from "react";
import { UploadCloud, AlertCircle, FileUp, Sparkles } from "lucide-react";
import {
  validateRetinalImageFile,
  extractImageDimensions,
  formatBytes,
} from "@/lib/validation";
import { UploadedImageMeta } from "@/types/screening";

export interface UploadCardProps {
  onImageSelected: (meta: UploadedImageMeta) => void;
  onError: (msg: string) => void;
  disabled?: boolean;
}

export const UploadCard: React.FC<UploadCardProps> = ({
  onImageSelected,
  onError,
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file?: File | null) => {
    setValidationError(null);

    const validation = validateRetinalImageFile(file);
    if (!validation.isValid || !file) {
      const err = validation.errorMessage || "Invalid file.";
      setValidationError(err);
      onError(err);
      return;
    }

    try {
      const dimensions = await extractImageDimensions(file);
      const previewUrl = URL.createObjectURL(file);

      const meta: UploadedImageMeta = {
        file,
        previewUrl,
        filename: file.name,
        fileSizeBytes: file.size,
        fileSizeFormatted: formatBytes(file.size),
        dimensions,
        mimeType: file.type || "image/png",
      };

      onImageSelected(meta);
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "Corrupted image file. Unable to decode photograph.";
      setValidationError(msg);
      onError(msg);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    processFile(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    processFile(file);
  };

  const triggerFileInput = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      triggerFileInput();
    }
  };

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload color retinal fundus image"
        aria-disabled={disabled}
        onClick={triggerFileInput}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`group relative flex min-h-[340px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300 focus:outline-hidden focus:ring-2 focus:ring-emerald-800/40 focus:ring-offset-2 ${
          isDragOver
            ? "border-emerald-800 bg-emerald-50/40 shadow-md scale-[1.005]"
            : "border-stone-300/80 bg-stone-50/40 hover:border-emerald-800/50 hover:bg-white hover:shadow-xs"
        } ${disabled ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,image/png,image/jpeg"
          onChange={handleFileChange}
          className="hidden"
          disabled={disabled}
          aria-hidden="true"
        />

        {/* Minimal Clinical Retinal Motif (SVG Aperture) */}
        <div className="relative mb-5 flex h-20 w-20 items-center justify-center">
          {/* Subtle concentric guidance rings */}
          <div className="absolute inset-0 rounded-full border border-stone-200 transition-transform duration-300 group-hover:scale-105 group-hover:border-emerald-200" />
          <div className="absolute inset-2 rounded-full border border-dashed border-stone-200 transition-transform duration-300 group-hover:scale-95 group-hover:border-emerald-300" />

          {/* Central Icon Container */}
          <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-white text-stone-700 shadow-xs border border-stone-200/90 transition-all duration-300 group-hover:bg-emerald-950 group-hover:text-white group-hover:shadow-sm">
            <UploadCloud className="h-6 w-6 stroke-[1.8] transition-transform duration-300 group-hover:-translate-y-0.5" aria-hidden="true" />
          </div>
        </div>

        {/* Heading & Subtext (Task 4) */}
        <h3 className="mb-1 text-base font-bold tracking-tight text-stone-900 group-hover:text-emerald-950 transition-colors">
          Analyze a retinal fundus image
        </h3>

        <p className="mb-5 max-w-xs text-xs leading-relaxed text-stone-500">
          Upload a color fundus photograph to begin AI-assisted screening and image-quality assessment.
        </p>

        {/* Action Button */}
        <button
          type="button"
          tabIndex={-1}
          disabled={disabled}
          className="inline-flex items-center space-x-2 rounded-xl bg-emerald-950 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition duration-200 group-hover:bg-emerald-900 group-hover:shadow-sm focus:outline-hidden"
        >
          <FileUp className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Upload fundus image</span>
        </button>

        {/* Secondary Format Hint */}
        <span className="mt-4 font-mono text-[11px] font-medium tracking-wide text-stone-400">
          PNG &bull; JPG &bull; JPEG (up to 25 MB)
        </span>
      </div>

      {validationError && (
        <div
          role="alert"
          aria-live="polite"
          className="flex items-start space-x-2.5 rounded-xl border border-rose-200 bg-rose-50/90 p-3.5 text-xs text-rose-800 animate-slide-up"
        >
          <AlertCircle
            className="mt-0.5 h-4 w-4 shrink-0 text-rose-600"
            aria-hidden="true"
          />
          <div className="space-y-0.5">
            <span className="font-semibold text-rose-900">Validation Error</span>
            <p className="text-rose-700">{validationError}</p>
          </div>
        </div>
      )}
    </div>
  );
};
