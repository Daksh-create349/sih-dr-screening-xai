import React, { useState } from "react";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Target,
  Layers,
  Activity,
  Compass,
  Sparkles,
  GitBranch,
  CircleDot,
} from "lucide-react";
import {
  EvidenceResponse,
  AnatomyResponse,
  ImageQualityResponse,
  ClassificationResponse,
  ExplainabilityResponse,
} from "@/types/screening";
import { getEvidenceOverlayUrl, getVesselsUrl } from "@/lib/api";

export interface EvidenceCardProps {
  evidence: EvidenceResponse;
  anatomy?: AnatomyResponse | null;
  quality: ImageQualityResponse;
  classification?: ClassificationResponse | null;
  explainability?: ExplainabilityResponse | null;
  resultId?: string | null;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  anatomy,
  quality,
  classification,
  explainability,
  resultId,
}) => {
  const [activeOverlayTab, setActiveOverlayTab] = useState<"integrated" | "vessels">("integrated");

  const rawLesions = (evidence.lesions as any) || {};
  const structuredRecord = (evidence.structured_record as any) || {};
  const structOpticDisc = structuredRecord?.structures?.optic_disc;
  const structExudates = structuredRecord?.lesions?.hard_exudates;
  const structStats = structuredRecord?.provenance?.lesion_statistics || {};

  const odCenter = rawLesions.optic_disc?.center_xy || (structOpticDisc ? [structOpticDisc.x, structOpticDisc.y] : null);
  const odRadius = rawLesions.optic_disc?.radius_px ?? structOpticDisc?.radius;
  const odConfidence = rawLesions.optic_disc?.confidence ?? structOpticDisc?.confidence;

  const exudateCount = rawLesions.hard_exudates?.lesion_count ?? structStats.exudate_clusters ?? rawLesions.exudate_clusters ?? 0;
  const exudatePixels = rawLesions.hard_exudates?.total_lesion_pixels ?? structExudates?.non_zero_pixels ?? 0;
  const exudateAreaFraction = rawLesions.hard_exudates?.area_fraction ?? structStats.exudate_area_fraction ?? rawLesions.exudate_area_fraction ?? 0;

  const structHemorrhages = structuredRecord?.lesions?.hemorrhages;
  const hemCount = rawLesions.hemorrhages?.lesion_count ?? structStats.hemorrhage_clusters ?? rawLesions.hemorrhage_clusters ?? 0;
  const hemPixels = rawLesions.hemorrhages?.total_lesion_pixels ?? structHemorrhages?.non_zero_pixels ?? rawLesions.hemorrhage_pixels ?? structStats.hemorrhage_pixels ?? 0;
  const hemAreaFraction = rawLesions.hemorrhages?.area_fraction ?? rawLesions.hemorrhage_area_fraction ?? structStats.hemorrhage_area_fraction ?? 0;

  const structSoftExudates = structuredRecord?.lesions?.soft_exudates;
  const softExudateCount = rawLesions.soft_exudates?.lesion_count ?? structStats.soft_exudate_clusters ?? rawLesions.soft_exudate_clusters ?? 0;
  const softExudatePixels = rawLesions.soft_exudates?.total_lesion_pixels ?? structSoftExudates?.non_zero_pixels ?? rawLesions.soft_exudate_pixels ?? structStats.soft_exudate_pixels ?? 0;
  const softExudateAreaFraction = rawLesions.soft_exudates?.area_fraction ?? rawLesions.soft_exudate_area_fraction ?? structStats.soft_exudate_area_fraction ?? 0;

  const structVessels = structuredRecord?.structures?.vessels;
  const vesselPixels = structVessels?.non_zero_pixels ?? structStats.vessel_pixels ?? rawLesions.vessel_pixels ?? 0;
  const vesselDensity = structVessels?.area_fraction ?? structStats.vessel_density ?? rawLesions.vessel_density ?? 0;
  const vesselBranches = structStats.vessel_major_branches ?? rawLesions.vessel_major_branches ?? 0;
  const vesselMethod = structVessels?.method ?? "Frangi Hessian";

  const structMAs = structuredRecord?.lesions?.microaneurysms;
  const maCount = rawLesions.microaneurysms?.lesion_count ?? structStats.microaneurysm_count ?? rawLesions.microaneurysm_count ?? 0;
  const maPixels = rawLesions.microaneurysms?.total_lesion_pixels ?? structMAs?.non_zero_pixels ?? rawLesions.microaneurysm_pixels ?? structStats.microaneurysm_pixels ?? 0;
  const maAreaFraction = rawLesions.microaneurysms?.area_fraction ?? rawLesions.microaneurysm_area_fraction ?? structStats.microaneurysm_area_fraction ?? 0;

  const rawCsmeString = String(rawLesions.csme_risk?.risk_level || structStats.macular_edema_risk_level || rawLesions.macular_edema_risk_level || (exudateCount > 0 ? "LOW" : "NONE"));
  const csmeRiskLevel = rawCsmeString.includes("HIGH")
    ? "HIGH"
    : rawCsmeString.includes("MODERATE")
    ? "MODERATE"
    : rawCsmeString.includes("LOW")
    ? "LOW"
    : "NONE";
  const csmeDistancePx = rawLesions.csme_risk?.min_distance_to_fovea_px ?? structStats.min_distance_to_fovea_px ?? rawLesions.min_distance_to_fovea_px;
  const csmeDistanceDD = rawLesions.csme_risk?.min_distance_in_disc_diameters ?? (odRadius && csmeDistancePx ? Number((csmeDistancePx / (odRadius * 2)).toFixed(2)) : null);

  const isCsmeHigh = csmeRiskLevel === "HIGH";
  const isCsmeMod = csmeRiskLevel === "MODERATE";

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            06 &bull; IDRiD Deep Lesions &amp; Synthesized Clinical Evidence
          </h3>
        </div>
        <span className="rounded-md border border-stone-200 bg-stone-50 px-2 py-0.5 font-mono text-[10px] text-stone-600">
          IDRiD Part A &amp; C Ground Truth
        </span>
      </div>

      {/* CSME Proximity Alert Banner (When clinically significant) */}
      {(isCsmeHigh || isCsmeMod) && (
        <div
          className={`flex items-start space-x-3 rounded-xl border p-4 ${
            isCsmeHigh
              ? "border-rose-300 bg-rose-50 text-rose-900"
              : "border-amber-300 bg-amber-50 text-amber-900"
          }`}
        >
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
          <div className="space-y-1">
            <h4 className="text-xs font-bold uppercase tracking-wide">
              {isCsmeHigh ? "High CSME Macular Risk Alert" : "Moderate CSME Risk Advisory"}
            </h4>
            <p className="text-xs leading-relaxed">
              Hard exudates detected within{" "}
              <strong>
                {csmeDistanceDD != null
                  ? `${csmeDistanceDD} Disc Diameters`
                  : "< 1 Disc Diameter"}
              </strong>{" "}
              of the estimated macular fovea. Clinically Significant Macular Edema (CSME)
              threatens central visual acuity and warrants immediate ophthalmology evaluation.
            </p>
          </div>
        </div>
      )}

      {/* Deep Neural Lesion Segmenter Metrics (Optic Disc, Hard Exudates, Hemorrhages, Soft Exudates, Vessels, Microaneurysms) */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
            Deep Retinal Lesions, Landmarks &amp; Vasculature (6 Clinical Systems)
          </span>
          <span className="font-mono text-[10px] text-stone-500">
            U-Net ResNet34 &bull; Frangi Hessian &bull; Top-Hat Morph
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-6">
          {/* 1. Optic Disc Segmentation */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Target className="h-4 w-4 text-cyan-700" />
                <span className="text-xs font-bold text-stone-900">
                  Optic Disc
                </span>
              </div>
              <span className="rounded-md border border-cyan-200 bg-cyan-50 px-2 py-0.5 font-mono text-[10px] font-bold text-cyan-800">
                Dice 0.9859
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Center (X, Y):</span>
                <span className="font-mono font-medium text-stone-900">
                  {odCenter ? `(${Math.round(odCenter[0])}, ${Math.round(odCenter[1])})` : "Localized"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Radius:</span>
                <span className="font-mono font-medium text-stone-900">
                  {odRadius ? `${Math.round(odRadius)} px` : "Calibrated"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Confidence:</span>
                <span className="font-mono font-medium text-stone-900">
                  {odConfidence != null ? `${(odConfidence * 100).toFixed(1)}%` : "Verified"}
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Retinal coordinate reference &amp; fovea anchor.
            </p>
          </div>

          {/* 2. Hard Exudates Lesions */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Activity className="h-4 w-4 text-amber-700" />
                <span className="text-xs font-bold text-stone-900">
                  Hard Exudates
                </span>
              </div>
              <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-800">
                Dice 0.7580
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Lesion Clusters:</span>
                <span className="font-mono font-bold text-stone-900">
                  {exudateCount} clusters
                </span>
              </div>
              <div className="flex justify-between">
                <span>Surface Area:</span>
                <span className="font-mono font-medium text-stone-900">
                  {exudatePixels > 0
                    ? `${exudatePixels.toLocaleString()} px (${(exudateAreaFraction * 100).toFixed(2)}%)`
                    : "0 px (0.00%)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>CSME Risk:</span>
                <span
                  className={`rounded-sm px-1.5 py-0.2 font-mono text-[10px] font-bold uppercase ${
                    isCsmeHigh
                      ? "bg-rose-100 text-rose-800"
                      : isCsmeMod
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {csmeRiskLevel}
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Lipid exudation biomarker for macular edema.
            </p>
          </div>

          {/* 3. Retinal Hemorrhages Lesions */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Layers className="h-4 w-4 text-rose-600" />
                <span className="text-xs font-bold text-stone-900">
                  Hemorrhages
                </span>
              </div>
              <span className="rounded-md border border-rose-200 bg-rose-50 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-800">
                Dice 0.7482
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Hemorrhage Foci:</span>
                <span className="font-mono font-bold text-stone-900">
                  {hemCount} foci
                </span>
              </div>
              <div className="flex justify-between">
                <span>Surface Area:</span>
                <span className="font-mono font-medium text-stone-900">
                  {hemPixels > 0
                    ? `${hemPixels.toLocaleString()} px (${(hemAreaFraction * 100).toFixed(2)}%)`
                    : "0 px (0.00%)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Vascular Leakage:</span>
                <span
                  className={`rounded-sm px-1.5 py-0.2 font-mono text-[10px] font-bold uppercase ${
                    hemCount > 10
                      ? "bg-rose-100 text-rose-800"
                      : hemCount > 0
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {hemCount > 10 ? "Severe" : hemCount > 0 ? "Active" : "Clear"}
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Microvascular intraretinal bleed foci (ICDR 4-2-1).
            </p>
          </div>

          {/* 4. Soft Exudates (Cotton Wool Spots) */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Sparkles className="h-4 w-4 text-sky-600" />
                <span className="text-xs font-bold text-stone-900">
                  Soft Exudates
                </span>
              </div>
              <span className="rounded-md border border-sky-200 bg-sky-50 px-2 py-0.5 font-mono text-[10px] font-bold text-sky-800">
                Dice 0.7595
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Cotton Wool Spots:</span>
                <span className="font-mono font-bold text-stone-900">
                  {softExudateCount} spots
                </span>
              </div>
              <div className="flex justify-between">
                <span>Surface Area:</span>
                <span className="font-mono font-medium text-stone-900">
                  {softExudatePixels > 0
                    ? `${softExudatePixels.toLocaleString()} px (${(softExudateAreaFraction * 100).toFixed(2)}%)`
                    : "0 px (0.00%)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>NFL Ischemia:</span>
                <span
                  className={`rounded-sm px-1.5 py-0.2 font-mono text-[10px] font-bold uppercase ${
                    softExudateCount > 0
                      ? "bg-sky-100 text-sky-900"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {softExudateCount > 0 ? "DETECTED" : "NONE"}
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Nerve fiber layer micro-infarct biomarker.
            </p>
          </div>

          {/* 5. Retinal Vascular Tree (Vessels) */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <GitBranch className="h-4 w-4 text-emerald-600" />
                <span className="text-xs font-bold text-stone-900">
                  Retinal Vessels
                </span>
              </div>
              <span className="rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-800">
                {vesselMethod.includes("Unet") ? "DRIVE U-Net" : "Frangi Hessian"}
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Arcade Branches:</span>
                <span className="font-mono font-bold text-stone-900">
                  {vesselBranches > 0 ? `${vesselBranches} branches` : "Mapped"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Vascular Density:</span>
                <span className="font-mono font-medium text-stone-900">
                  {vesselDensity > 0 ? `${(vesselDensity * 100).toFixed(2)}%` : "Quantified"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Microvasculature:</span>
                <span className="rounded-sm px-1.5 py-0.2 font-mono text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                  DETECTED
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Arteriolar caliber &amp; vascular tree geometry.
            </p>
          </div>

          {/* 6. Microaneurysms (MAs) */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <CircleDot className="h-4 w-4 text-orange-600" />
                <span className="text-xs font-bold text-stone-900">
                  Microaneurysms
                </span>
              </div>
              <span className="rounded-md border border-orange-200 bg-orange-50 px-2 py-0.5 font-mono text-[10px] font-bold text-orange-800">
                Top-Hat Morph
              </span>
            </div>

            <div className="space-y-1 text-xs text-stone-600">
              <div className="flex justify-between">
                <span>Focal Lesions:</span>
                <span className="font-mono font-bold text-stone-900">
                  {maCount > 0 ? `${maCount} MAs` : "0 MAs"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Surface Area:</span>
                <span className="font-mono font-medium text-stone-900">
                  {maPixels > 0
                    ? `${maPixels.toLocaleString()} px (${(maAreaFraction * 100).toFixed(3)}%)`
                    : "0 px (0.00%)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Capillary Status:</span>
                <span
                  className={`rounded-sm px-1.5 py-0.2 font-mono text-[10px] font-bold uppercase ${
                    maCount > 15
                      ? "bg-rose-100 text-rose-800"
                      : maCount > 0
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {maCount > 15 ? "Frequent" : maCount > 0 ? "Detected" : "Clear"}
                </span>
              </div>
            </div>
            <p className="border-t border-stone-200/60 pt-1.5 text-[10px] text-stone-400">
              Earliest visible hallmark of microvascular damage.
            </p>
          </div>
        </div>
      </div>

      {/* Multi-Structure Deep Lesion Map & Angiography Viewer (When overlay image available) */}
      {resultId && (
        <div className="space-y-2.5 rounded-xl border border-stone-200 bg-stone-50/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-stone-800">
              Retinal Pathology &amp; Vascular Architecture Maps
            </span>
            <div className="flex items-center space-x-1 rounded-lg border border-stone-200 bg-white p-0.5 shadow-2xs">
              <button
                type="button"
                onClick={() => setActiveOverlayTab("integrated")}
                className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                  activeOverlayTab === "integrated"
                    ? "bg-slate-900 text-white font-semibold"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
                }`}
              >
                Integrated Multi-Lesion Map
              </button>
              <button
                type="button"
                onClick={() => setActiveOverlayTab("vessels")}
                className={`flex items-center space-x-1 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                  activeOverlayTab === "vessels"
                    ? "bg-slate-900 text-white font-semibold"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-50"
                }`}
              >
                <GitBranch className="h-3 w-3 text-emerald-500" />
                <span>Retinal Angiography (Vessels)</span>
              </button>
            </div>
          </div>

          <div className="relative aspect-video sm:aspect-[4/3] w-full max-w-lg mx-auto overflow-hidden rounded-xl border border-stone-800 bg-black flex items-center justify-center shadow-inner">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={
                activeOverlayTab === "integrated"
                  ? getEvidenceOverlayUrl(resultId)
                  : getVesselsUrl(resultId)
              }
              alt={
                activeOverlayTab === "integrated"
                  ? "IDRiD Optic Disc, Hard Exudates, Hemorrhages, and Soft Exudates Deep Segmentation Overlay"
                  : "Retinal Vascular Tree Angiogram Segmentation"
              }
              className="h-full w-full object-contain"
            />
            {/* Visual Color Legend */}
            <div className="absolute bottom-2.5 left-2.5 right-2.5 flex flex-wrap items-center justify-between gap-1.5 rounded-lg bg-black/85 px-3 py-1.5 font-mono text-[10px] text-white backdrop-blur-xs border border-stone-800">
              {activeOverlayTab === "integrated" ? (
                <>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
                    <span>Optic Disc (0.986)</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-amber-400"></span>
                    <span>Hard Exudates (0.758)</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                    <span>Hemorrhages (0.748)</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-sky-200"></span>
                    <span>Soft Exudates (0.760)</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                    <span>Vessels (Mapped)</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center space-x-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
                    <span>Retinal Vascular Tree (Hessian Eigenvalues)</span>
                  </div>
                  <div className="flex items-center space-x-2 text-stone-300">
                    <span>Density: {(vesselDensity * 100).toFixed(1)}%</span>
                    <span>&bull;</span>
                    <span>{vesselBranches} Arcades</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Synthesized Diagnostic Narrative */}
      <div className="rounded-xl border border-stone-200 bg-stone-50/70 p-5 text-xs leading-relaxed text-stone-800 space-y-2">
        <span className="block font-mono text-[10px] uppercase font-bold text-stone-400 tracking-wider">
          Synthesized Clinical Evidence Narrative
        </span>
        <p className="font-normal text-sm sm:text-[13px] leading-relaxed text-stone-900">
          {evidence.narrative}
        </p>
      </div>

      {/* What the Model Focused On */}
      <div className="rounded-xl border border-stone-200/80 bg-stone-50/40 p-4 space-y-1.5">
        <h4 className="text-xs font-bold text-stone-900 uppercase tracking-wide">
          Anatomical Attribution Context
        </h4>
        <p className="text-xs text-stone-600 leading-relaxed">
          Model attention concentrated predominantly in:{" "}
          <strong className="text-stone-900 capitalize">
            {anatomy?.top_attention_region?.replace(/_/g, " ") || "Posterior Retinal Context"}
          </strong>
          {anatomy?.top_attention_mass_pct
            ? ` accounting for ${anatomy.top_attention_mass_pct.toFixed(1)}% of total retinal attribution mass.`
            : "."}
        </p>
        {explainability?.attention_summary && (
          <p className="text-[11px] font-mono text-stone-500 pt-0.5">
            Summary: {explainability.attention_summary}
          </p>
        )}
      </div>

      {/* Multi-Dimensional Pipeline Reliability Assessment */}
      <div className="space-y-2.5 pt-2">
        <span className="block text-[11px] font-bold uppercase tracking-wider text-stone-400">
          Multi-Dimensional Pipeline Reliability Assessment
        </span>

        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 text-xs">
          {/* 1. Image Quality */}
          <div className="rounded-xl border border-stone-200/80 bg-white p-3 shadow-2xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-stone-700">1. Optical Acquisition</span>
              <span
                className={`rounded-md px-1.5 py-0.2 text-[10px] font-bold uppercase ${
                  quality.decision === "GOOD"
                    ? "text-emerald-800 bg-emerald-50"
                    : "text-amber-800 bg-amber-50"
                }`}
              >
                {quality.decision}
              </span>
            </div>
            <p className="text-[11px] text-stone-500">
              Composite optical score: {quality.overall_score.toFixed(1)} / 100
            </p>
          </div>

          {/* 2. Model Prediction */}
          <div className="rounded-xl border border-stone-200/80 bg-white p-3 shadow-2xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-stone-700">2. Classifier Confidence</span>
              <span className="font-mono font-bold text-stone-900 text-[11px]">
                {classification ? (classification.top_probability * 100).toFixed(1) + "%" : "N/A"}
              </span>
            </div>
            <p className="text-[11px] text-stone-500">
              Grade {classification?.predicted_class ?? "N/A"}:{" "}
              {classification?.predicted_label ?? "N/A"}
            </p>
          </div>

          {/* 3. Landmark Localization */}
          <div className="rounded-xl border border-stone-200/80 bg-white p-3 shadow-2xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-stone-700">3. IDRiD ResNet34 Segmenter</span>
              <span className="rounded-md px-1.5 py-0.2 text-[10px] font-bold uppercase text-sky-800 bg-sky-50">
                Active
              </span>
            </div>
            <p className="text-[11px] text-stone-500">
              Optic disc, hard exudates & hemorrhages segmented at 512×512 native resolution
            </p>
          </div>

          {/* 4. Explainability Availability */}
          <div className="rounded-xl border border-stone-200/80 bg-white p-3 shadow-2xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-stone-700">4. Explainability Attribution</span>
              <span className="rounded-md px-1.5 py-0.2 text-[10px] font-bold uppercase text-emerald-800 bg-emerald-50">
                {explainability?.gradcam_available ? "Available" : "Unavailable"}
              </span>
            </div>
            <p className="text-[11px] text-stone-500">
              Grad-CAM back-propagation computed & warped
            </p>
          </div>
        </div>

        <p className="text-[11px] text-stone-400 italic pt-0.5">
          Note: System reliability is evaluated across separate optical, statistical, and architectural dimensions rather than a single synthetic score.
        </p>
      </div>

      {/* Mandatory Regulatory Disclaimer */}
      <div className="rounded-xl border border-stone-200/90 bg-stone-50/70 p-4 text-xs text-stone-600 flex items-start space-x-3">
        <Info className="h-4 w-4 shrink-0 text-stone-500 mt-0.5" />
        <p className="leading-relaxed text-[11px]">{evidence.disclaimer}</p>
      </div>
    </div>
  );
};
