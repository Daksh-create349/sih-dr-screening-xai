"use client";

import React, { useState } from "react";
import { CLINICAL_SAMPLE_CASES, ClinicalSampleCase } from "./ClinicalSampleSelector";
import { UploadedImageMeta } from "@/types/screening";
import { formatBytes } from "@/lib/validation";
import { Sparkles, Loader2, Check } from "lucide-react";

export interface CompactSampleBarProps {
  onSelectSample: (meta: UploadedImageMeta) => void;
  disabled?: boolean;
  selectedFilename?: string | null;
}

export const CompactSampleBar: React.FC<CompactSampleBarProps> = ({
  onSelectSample,
  disabled = false,
  selectedFilename,
}) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleSelect = async (sample: ClinicalSampleCase) => {
    if (disabled || loadingId) return;
    setLoadingId(sample.id);

    try {
      const response = await fetch(sample.imagePath);
      if (!response.ok) throw new Error("Failed to load sample image");
      const blob = await response.blob();
      const mimeType = sample.filename.endsWith(".jpg") ? "image/jpeg" : "image/png";
      const file = new File([blob], sample.filename, { type: mimeType });
      const previewUrl = URL.createObjectURL(blob);
      const img = new Image();

      await new Promise<void>((resolve, reject) => {
        img.onload = () => resolve();
        img.onerror = () => reject(new Error("Failed to decode sample"));
        img.src = previewUrl;
      });

      const meta: UploadedImageMeta = {
        file,
        previewUrl,
        filename: sample.filename,
        fileSizeBytes: file.size,
        fileSizeFormatted: formatBytes(file.size),
        dimensions: {
          width: img.naturalWidth || 512,
          height: img.naturalHeight || 512,
        },
        mimeType,
      };

      onSelectSample(meta);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="flex items-center space-x-2 overflow-x-auto rounded-2xl border border-stone-200/90 bg-white px-3.5 py-2 shadow-xs scrollbar-none no-print">
      <div className="flex shrink-0 items-center space-x-1.5 text-xs font-bold text-slate-800">
        <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
        <span className="hidden sm:inline">Preloaded Cases:</span>
      </div>

      <div className="flex shrink-0 items-center space-x-1.5">
        {CLINICAL_SAMPLE_CASES.map((sample) => {
          const isSelected = selectedFilename === sample.filename;
          const isLoading = loadingId === sample.id;

          return (
            <button
              key={sample.id}
              type="button"
              onClick={() => handleSelect(sample)}
              disabled={disabled || !!loadingId}
              className={`inline-flex items-center space-x-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                isSelected
                  ? "border-emerald-600 bg-emerald-50 text-emerald-900 ring-1 ring-emerald-500/30 font-bold"
                  : "border-stone-200 bg-stone-50/70 text-stone-700 hover:border-stone-300 hover:bg-stone-100"
              } disabled:cursor-not-allowed disabled:opacity-50`}
            >
              {isLoading ? (
                <Loader2 className="h-3 w-3 animate-spin text-stone-500" />
              ) : isSelected ? (
                <Check className="h-3 w-3 text-emerald-600" />
              ) : null}
              <span>{sample.title}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
