"use client";

import React, { useState } from "react";
import {
  FolderCheck,
  Eye,
  CheckCircle2,
  Loader2,
  ChevronRight,
} from "lucide-react";
import { UploadedImageMeta } from "@/types/screening";
import { formatBytes } from "@/lib/validation";

export interface ClinicalSampleCase {
  id: string;
  title: string;
  filename: string;
  imagePath: string;
  grade: string;
  gradeBadgeColor: string;
  pathology: string;
  clinicalNote: string;
  expectedTriage: "Referable" | "Non-Referable" | "Quality Rejection" | "Enhance";
  qualityExpected: "GOOD" | "BORDERLINE" | "UNGRADEABLE";
  isKeyDemo?: boolean;
}

export const CLINICAL_SAMPLE_CASES: ClinicalSampleCase[] = [
  {
    id: "sample-grade0",
    title: "Normal Healthy Retina",
    filename: "grade0_normal.png",
    imagePath: "/sample_images/grade0_normal.png",
    grade: "Grade 0 (No DR)",
    gradeBadgeColor: "bg-emerald-50 text-emerald-800 border-emerald-200",
    pathology: "Intact microvascular tree, healthy macula, 0 exudate lesions",
    clinicalNote: "Baseline healthy control for screening comparison. High optical clarity.",
    expectedTriage: "Non-Referable",
    qualityExpected: "GOOD",
  },
  {
    id: "sample-grade1",
    title: "Mild Non-Proliferative DR",
    filename: "grade1_mild_npdr.png",
    imagePath: "/sample_images/grade1_mild_npdr.png",
    grade: "Grade 1 (Mild NPDR)",
    gradeBadgeColor: "bg-sky-50 text-sky-800 border-sky-200",
    pathology: "Isolated microaneurysms, minimal capillary alteration",
    clinicalNote: "Early stage. Requires routine 12-month PHC follow-up.",
    expectedTriage: "Non-Referable",
    qualityExpected: "GOOD",
  },
  {
    id: "sample-grade2",
    title: "Moderate NPDR + Exudates",
    filename: "grade2_moderate_csme.png",
    imagePath: "/sample_images/grade2_moderate_csme.png",
    grade: "Grade 2 (Moderate)",
    gradeBadgeColor: "bg-amber-50 text-amber-800 border-amber-200",
    pathology: "Hard exudates & microaneurysms; CSME foveal distance evaluated",
    clinicalNote: "Referable threshold exceeded. Evaluates CSME proximity risk.",
    expectedTriage: "Referable",
    qualityExpected: "GOOD",
    isKeyDemo: true,
  },
  {
    id: "sample-grade3",
    title: "Severe NPDR (4-2-1 Rule)",
    filename: "grade3_severe_npdr.png",
    imagePath: "/sample_images/grade3_severe_npdr.png",
    grade: "Grade 3 (Severe NPDR)",
    gradeBadgeColor: "bg-orange-50 text-orange-800 border-orange-200",
    pathology: "Extensive intraretinal hemorrhages, 79 exudate clusters segmented",
    clinicalNote: "High risk of rapid progression to proliferative retinopathy.",
    expectedTriage: "Referable",
    qualityExpected: "GOOD",
    isKeyDemo: true,
  },
  {
    id: "sample-grade4",
    title: "Proliferative DR (PDR)",
    filename: "grade4_proliferative.jpg",
    imagePath: "/sample_images/grade4_proliferative.jpg",
    grade: "Grade 4 (PDR)",
    gradeBadgeColor: "bg-rose-50 text-rose-800 border-rose-200",
    pathology: "Severe neovascularization, 112 exudates, vitreo-retinal emergency",
    clinicalNote: "Urgent surgical / laser photocoagulation referral required.",
    expectedTriage: "Referable",
    qualityExpected: "GOOD",
    isKeyDemo: true,
  },
  {
    id: "sample-borderline",
    title: "Borderline Exposure Case",
    filename: "borderline_enhancement.png",
    imagePath: "/sample_images/borderline_enhancement.png",
    grade: "IQA Borderline",
    gradeBadgeColor: "bg-amber-100/70 text-amber-900 border-amber-300",
    pathology: "Sub-optimal illumination; triggers automated CLAHE + bilateral filter",
    clinicalNote: "Demonstrates automated pre-processing enhancement before inference.",
    expectedTriage: "Enhance",
    qualityExpected: "BORDERLINE",
  },
  {
    id: "sample-blur",
    title: "Defocus Motion Blur (Reject)",
    filename: "ungradeable_blur_reject.png",
    imagePath: "/sample_images/ungradeable_blur_reject.png",
    grade: "IQA Ungradeable",
    gradeBadgeColor: "bg-rose-100 text-rose-900 border-rose-300",
    pathology: "Severe optical blur (Laplacian < 15.0); triggers ASHA recapture protocol",
    clinicalNote: "Safety Gatekeeper in action: halts pipeline to prevent misdiagnosis.",
    expectedTriage: "Quality Rejection",
    qualityExpected: "UNGRADEABLE",
    isKeyDemo: true,
  },
  {
    id: "sample-aptos",
    title: "APTOS Benchmark Retinal Case",
    filename: "aptos_grade2_disc.png",
    imagePath: "/sample_images/aptos_grade2_disc.png",
    grade: "Benchmark Grade 2",
    gradeBadgeColor: "bg-indigo-50 text-indigo-800 border-indigo-200",
    pathology: "High-resolution posterior pole with sharp optic disc & macula",
    clinicalNote: "Canonical evaluation study case with dual UNet segmentation.",
    expectedTriage: "Referable",
    qualityExpected: "GOOD",
  },
];

export interface ClinicalSampleSelectorProps {
  onSelectSample: (meta: UploadedImageMeta) => void;
  disabled?: boolean;
  selectedFilename?: string | null;
}

export const ClinicalSampleSelector: React.FC<ClinicalSampleSelectorProps> = ({
  onSelectSample,
  disabled = false,
  selectedFilename,
}) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleSelect = async (sample: ClinicalSampleCase) => {
    if (disabled || loadingId) return;
    setLoadingId(sample.id);

    try {
      // Fetch sample asset from public directory
      const response = await fetch(sample.imagePath);
      if (!response.ok) {
        throw new Error(`Failed to load sample image: ${response.statusText}`);
      }
      const blob = await response.blob();
      const mimeType = sample.filename.endsWith(".jpg") ? "image/jpeg" : "image/png";
      const file = new File([blob], sample.filename, { type: mimeType });

      // Create preview and measure dimensions
      const previewUrl = URL.createObjectURL(blob);
      const img = new Image();

      await new Promise<void>((resolve, reject) => {
        img.onload = () => resolve();
        img.onerror = () => reject(new Error("Failed to decode sample image."));
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
      console.error("Error loading sample case:", err);
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="rounded-2xl border border-stone-200/90 bg-white p-5 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-stone-900 text-white">
            <FolderCheck className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-stone-900">
              Verified Clinical Test Cohort
            </h3>
            <p className="text-xs text-stone-500">
              Pre-loaded ground-truth retinal cases for instantaneous SIH evaluation
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-1.5 text-[11px] font-mono text-stone-500">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500"></span>
          <span>8 Verified Cases</span>
        </div>
      </div>

      {/* Grid of Clinical Sample Cases */}
      <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
        {CLINICAL_SAMPLE_CASES.map((sample) => {
          const isSelected = selectedFilename === sample.filename;
          const isLoading = loadingId === sample.id;

          return (
            <button
              key={sample.id}
              type="button"
              onClick={() => handleSelect(sample)}
              disabled={disabled || !!loadingId}
              className={`group relative flex flex-col justify-between rounded-xl border p-3 text-left transition duration-150 ${
                isSelected
                  ? "border-emerald-600 bg-emerald-50/40 ring-1 ring-emerald-500/30"
                  : "border-stone-200/80 bg-stone-50/30 hover:border-stone-300 hover:bg-stone-50/80"
              } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              {sample.isKeyDemo && (
                <span className="absolute -top-2 right-3 rounded-full bg-stone-900 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-white shadow-2xs">
                  Key Demo
                </span>
              )}

              <div className="space-y-2">
                {/* Header Row: Grade & Status */}
                <div className="flex items-center justify-between gap-1">
                  <span
                    className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${sample.gradeBadgeColor}`}
                  >
                    {sample.grade}
                  </span>
                  <span className="font-mono text-[9px] text-stone-400">
                    {sample.expectedTriage}
                  </span>
                </div>

                {/* Title & Pathology */}
                <div>
                  <h4 className="text-xs font-bold text-stone-900 group-hover:text-emerald-950">
                    {sample.title}
                  </h4>
                  <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-stone-500">
                    {sample.pathology}
                  </p>
                </div>
              </div>

              {/* Action Bar */}
              <div className="mt-3 flex items-center justify-between border-t border-stone-200/60 pt-2 text-[11px]">
                <span className="font-mono text-[10px] text-stone-400">
                  {sample.filename}
                </span>
                <span className="inline-flex items-center space-x-1 font-semibold text-emerald-850 group-hover:underline">
                  {isLoading ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin text-stone-600" />
                      <span>Loading...</span>
                    </>
                  ) : isSelected ? (
                    <span className="flex items-center space-x-1 text-emerald-700">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>Selected</span>
                    </span>
                  ) : (
                    <>
                      <span>Load Case</span>
                      <ChevronRight className="h-3 w-3 text-stone-400 group-hover:text-stone-700" />
                    </>
                  )}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
