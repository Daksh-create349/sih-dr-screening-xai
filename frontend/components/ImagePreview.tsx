import React from "react";
import { X, CheckCircle2, FileText, Maximize2 } from "lucide-react";
import { UploadedImageMeta } from "@/types/screening";

export interface ImagePreviewProps {
  imageMeta: UploadedImageMeta;
  onRemove: () => void;
  disabled?: boolean;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  imageMeta,
  onRemove,
  disabled = false,
}) => {
  return (
    <div className="space-y-4 animate-fade-in">
      {/* Image Viewport Container */}
      <div className="group relative flex aspect-square w-full items-center justify-center overflow-hidden rounded-2xl border border-stone-200/90 bg-stone-950 shadow-sm transition-all duration-300">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageMeta.previewUrl}
          alt={`Retinal fundus photograph: ${imageMeta.filename}`}
          className="max-h-full max-w-full object-contain animate-slide-up"
        />

        {/* Remove Button */}
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          aria-label="Remove uploaded image"
          className="absolute top-3.5 right-3.5 flex h-8 w-8 items-center justify-center rounded-full bg-stone-900/80 text-white backdrop-blur-xs transition duration-200 hover:bg-stone-900 hover:scale-105 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>

        {/* Status Chip */}
        <div className="absolute bottom-3.5 left-3.5 flex items-center space-x-1.5 rounded-lg bg-stone-900/85 px-3 py-1 text-xs text-stone-200 backdrop-blur-xs border border-white/10 shadow-xs">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
          <span className="font-medium">Fundus Photograph Verified</span>
        </div>
      </div>

      {/* Metadata Info Panel */}
      <div className="grid grid-cols-3 gap-2 rounded-xl border border-stone-200/80 bg-stone-50/70 p-3 text-xs animate-stagger-1">
        <div className="space-y-0.5">
          <span className="text-[11px] font-medium text-stone-500">File Name</span>
          <p
            className="truncate font-semibold text-stone-800"
            title={imageMeta.filename}
          >
            {imageMeta.filename}
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="text-[11px] font-medium text-stone-500">Resolution</span>
          <p className="flex items-center space-x-1 font-semibold text-stone-800">
            <Maximize2 className="h-3 w-3 text-stone-400" aria-hidden="true" />
            <span>
              {imageMeta.dimensions.width} &times; {imageMeta.dimensions.height}
            </span>
          </p>
        </div>

        <div className="space-y-0.5">
          <span className="text-[11px] font-medium text-stone-500">File Size</span>
          <p className="flex items-center space-x-1 font-semibold text-stone-800">
            <FileText className="h-3 w-3 text-stone-400" aria-hidden="true" />
            <span>{imageMeta.fileSizeFormatted}</span>
          </p>
        </div>
      </div>
    </div>
  );
};
