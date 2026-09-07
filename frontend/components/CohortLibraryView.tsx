"use client";

import React, { useState } from "react";
import { CLINICAL_SAMPLE_CASES, ClinicalSampleCase } from "./ClinicalSampleSelector";
import { UploadedImageMeta } from "@/types/screening";
import { formatBytes } from "@/lib/validation";
import {
  FolderKanban,
  Search,
  Filter,
  ArrowUpRight,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
} from "lucide-react";

export interface CohortLibraryViewProps {
  onLoadCase: (meta: UploadedImageMeta) => void;
  disabled?: boolean;
}

export const CohortLibraryView: React.FC<CohortLibraryViewProps> = ({
  onLoadCase,
  disabled = false,
}) => {
  const [filter, setFilter] = useState<"ALL" | "REFERABLE" | "NON_REFERABLE" | "IQA">("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const filteredCases = CLINICAL_SAMPLE_CASES.filter((c) => {
    if (filter === "REFERABLE" && c.expectedTriage !== "Referable") return false;
    if (filter === "NON_REFERABLE" && c.expectedTriage !== "Non-Referable") return false;
    if (filter === "IQA" && c.expectedTriage !== "Quality Rejection" && c.expectedTriage !== "Enhance") return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        c.title.toLowerCase().includes(q) ||
        c.grade.toLowerCase().includes(q) ||
        c.pathology.toLowerCase().includes(q) ||
        c.filename.toLowerCase().includes(q)
      );
    }
    return true;
  });

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

      onLoadCase(meta);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-stone-200/90 bg-white p-5 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <FolderKanban className="h-5 w-5 text-sky-700" />
            <h2 className="text-base font-bold text-slate-900">
              Verified Patient Cohort Repository
            </h2>
          </div>
          <p className="text-xs text-stone-500 mt-0.5">
            Curated clinical studies spanning ICDR Grades 0 to 4, CSME risks, and optical edge cases
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 rounded-xl border border-stone-200 bg-stone-50 p-1 text-xs font-medium">
          <button
            type="button"
            onClick={() => setFilter("ALL")}
            className={`rounded-lg px-3 py-1.5 transition ${
              filter === "ALL"
                ? "bg-white font-bold text-slate-900 shadow-2xs"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            All Studies (8)
          </button>
          <button
            type="button"
            onClick={() => setFilter("REFERABLE")}
            className={`rounded-lg px-3 py-1.5 transition ${
              filter === "REFERABLE"
                ? "bg-white font-bold text-slate-900 shadow-2xs"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            Referable (4)
          </button>
          <button
            type="button"
            onClick={() => setFilter("NON_REFERABLE")}
            className={`rounded-lg px-3 py-1.5 transition ${
              filter === "NON_REFERABLE"
                ? "bg-white font-bold text-slate-900 shadow-2xs"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            Non-Referable (2)
          </button>
          <button
            type="button"
            onClick={() => setFilter("IQA")}
            className={`rounded-lg px-3 py-1.5 transition ${
              filter === "IQA"
                ? "bg-white font-bold text-slate-900 shadow-2xs"
                : "text-stone-600 hover:text-stone-900"
            }`}
          >
            Quality Edge Cases (2)
          </button>
        </div>
      </div>

      {/* Cohort Study Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {filteredCases.map((sample, idx) => {
          const isLoading = loadingId === sample.id;

          return (
            <div
              key={sample.id}
              className="flex flex-col justify-between overflow-hidden rounded-2xl border border-stone-200/90 bg-white shadow-xs transition duration-200 hover:border-stone-300 hover:shadow-md"
            >
              <div>
                {/* Image Thumbnail Header */}
                <div className="relative aspect-video w-full overflow-hidden bg-slate-950">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={sample.imagePath}
                    alt={sample.title}
                    className="h-full w-full object-contain transition duration-300 hover:scale-105"
                  />
                  <div className="absolute top-2.5 left-2.5">
                    <span
                      className={`rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase shadow-xs ${sample.gradeBadgeColor}`}
                    >
                      {sample.grade}
                    </span>
                  </div>
                  <div className="absolute top-2.5 right-2.5 rounded-md bg-black/70 px-2 py-0.5 font-mono text-[9px] text-white backdrop-blur-xs">
                    #RUR-0{idx + 1}
                  </div>
                </div>

                {/* Case Info */}
                <div className="p-4 space-y-2">
                  <h3 className="text-sm font-bold text-slate-900">
                    {sample.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-stone-600 line-clamp-2">
                    {sample.pathology}
                  </p>
                  <p className="text-[11px] text-stone-400 italic">
                    {sample.clinicalNote}
                  </p>
                </div>
              </div>

              {/* Action Bar */}
              <div className="border-t border-stone-100 bg-stone-50/60 p-3 flex items-center justify-between">
                <span className="font-mono text-[10px] text-stone-500">
                  {sample.expectedTriage}
                </span>

                <button
                  type="button"
                  onClick={() => handleSelect(sample)}
                  disabled={disabled || !!loadingId}
                  className="inline-flex items-center space-x-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white shadow-xs transition hover:bg-slate-800 disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Loading...</span>
                    </>
                  ) : (
                    <>
                      <span>Open in Workstation</span>
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
