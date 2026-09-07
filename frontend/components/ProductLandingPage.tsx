"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  ShieldCheck,
  Activity,
  Layers,
  Cpu,
  Eye,
  CheckCircle2,
  AlertTriangle,
  FolderKanban,
  BarChart3,
  Sparkles,
  Target,
  Clock,
  Compass,
  ChevronRight,
  SlidersHorizontal,
  Users,
} from "lucide-react";
import { CLINICAL_SAMPLE_CASES, ClinicalSampleCase } from "./ClinicalSampleSelector";
import { UploadedImageMeta } from "@/types/screening";
import { formatBytes } from "@/lib/validation";

export interface ProductLandingPageProps {
  onLaunchWorkstation: (meta?: UploadedImageMeta) => void;
  onNavigateTab: (tab: "cohort" | "benchmarks") => void;
}

export const ProductLandingPage: React.FC<ProductLandingPageProps> = ({
  onLaunchWorkstation,
  onNavigateTab,
}) => {
  const [loadingCaseId, setLoadingCaseId] = useState<string | null>(null);

  const handleLaunchCase = async (sample: ClinicalSampleCase) => {
    setLoadingCaseId(sample.id);
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

      onLaunchWorkstation(meta);
    } catch (err) {
      console.error(err);
      onLaunchWorkstation();
    } finally {
      setLoadingCaseId(null);
    }
  };

  return (
    <div className="space-y-16 pb-12 animate-fade-in">
      {/* ============================================================ */}
      {/* 1. HERO SECTION                                              */}
      {/* ============================================================ */}
      <section className="relative overflow-hidden rounded-3xl border border-stone-200/80 bg-gradient-to-b from-white via-[#f8fafc] to-[#f1f5f9] p-8 sm:p-12 lg:p-16 shadow-sm">
        {/* Subtle Background Mesh Grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage: `radial-gradient(#0f172a 1px, transparent 1px)`,
            backgroundSize: "28px 28px",
          }}
        />

        <div className="relative z-10 max-w-4xl mx-auto text-center space-y-6">
          {/* Eyebrow Badge */}
          <div className="inline-flex items-center space-x-2 rounded-full border border-emerald-500/30 bg-emerald-50 px-3.5 py-1 text-xs font-semibold text-emerald-800 shadow-2xs">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>SIH 2026 PS 26038 &bull; Autonomous Clinical Retinal Diagnostic Station</span>
          </div>

          {/* Main Title */}
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-950 sm:text-5xl sm:leading-[1.15]">
            Explainable AI for Diabetic Retinopathy Screening in Rural India
          </h1>

          {/* Description */}
          <p className="text-base text-stone-600 sm:text-lg leading-relaxed max-w-2xl mx-auto">
            A state-of-the-art clinical screening platform uniting autonomous optical quality gating,
            dual IDRiD ResNet34 lesion segmenters, and calibrated DR severity grading — engineered for
            Primary Health Centres (PHCs) with zero retina specialist coverage.
          </p>

          {/* CTA Button Group */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              type="button"
              onClick={() => onLaunchWorkstation()}
              className="inline-flex items-center space-x-2 rounded-xl bg-slate-950 px-6 py-3.5 text-sm font-bold text-white shadow-sm transition duration-200 hover:bg-slate-850 hover:shadow-md"
            >
              <Activity className="h-4 w-4 text-emerald-400" />
              <span>Launch Diagnostic Workstation</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={() => onNavigateTab("cohort")}
              className="inline-flex items-center space-x-2 rounded-xl border border-stone-300 bg-white px-5 py-3.5 text-sm font-semibold text-slate-800 shadow-2xs transition hover:bg-stone-50"
            >
              <FolderKanban className="h-4 w-4 text-sky-700" />
              <span>Browse 8 Patient Studies</span>
            </button>
          </div>

          {/* Trust Metrics Pill Bar */}
          <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-stone-500 border-t border-stone-200/60 font-medium">
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <span>Optic Disc Dice: <strong>0.9859</strong></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-amber-600" />
              <span>Hard Exudates Dice: <strong>0.7580</strong></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-rose-600" />
              <span>Hemorrhages Dice: <strong>0.7482</strong></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-cyan-600" />
              <span>Soft Exudates Dice: <strong>0.7595</strong></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-sky-600" />
              <span>Referable DR Sens: <strong>&gt;90%</strong></span>
            </div>
            <div className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-slate-700" />
              <span>Zero Mock Data</span>
            </div>
          </div>
        </div>

        {/* Interactive Clinical Workstation Preview Mockup */}
        <div className="relative mt-12 max-w-5xl mx-auto rounded-2xl border border-stone-800 bg-[#080d1a] p-3 shadow-2xl">
          {/* Mockup Window Bar */}
          <div className="flex items-center justify-between border-b border-stone-800 px-3 pb-2.5 text-xs text-stone-400 font-mono">
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1.5">
                <div className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <div className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
              </div>
              <span className="text-[11px] text-stone-300 font-semibold pl-2">
                RetinaGuard PACS &bull; Patient Study #RUR-084 &bull; OD 45°
              </span>
            </div>
            <div className="flex items-center space-x-2 text-[10px]">
              <span className="rounded bg-emerald-950 px-1.5 py-0.5 font-bold text-emerald-400">
                ACTIVE INFERENCE
              </span>
            </div>
          </div>

          {/* Mockup Screen Split Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 items-center">
            {/* Left Fundus Simulation */}
            <div className="md:col-span-7 relative aspect-video rounded-xl overflow-hidden bg-black flex items-center justify-center border border-stone-800">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/sample_images/grade2_moderate_csme.png"
                alt="Retina fundus sample"
                className="h-full w-full object-contain"
              />
              <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between rounded bg-black/80 px-2.5 py-1 text-[10px] text-white font-mono">
                <span className="text-cyan-400">● Optic Disc (Localized)</span>
                <span className="text-amber-400">● Hard Exudates (2 clusters)</span>
                <span className="text-rose-400">● CSME Risk: Moderate</span>
              </div>
            </div>

            {/* Right Diagnostic Console Simulation */}
            <div className="md:col-span-5 rounded-xl border border-stone-800 bg-[#0e1628] p-4 space-y-3 text-xs text-stone-300">
              <div className="flex items-center justify-between border-b border-stone-800 pb-2">
                <span className="font-bold text-white uppercase text-[10px] tracking-wider">
                  Diagnostic Findings
                </span>
                <span className="rounded bg-amber-900/60 border border-amber-600/60 px-2 py-0.5 text-[10px] font-bold text-amber-300">
                  Grade 2 &bull; Moderate DR
                </span>
              </div>

              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-stone-400">Triage Decision:</span>
                  <span className="font-bold text-rose-400">Referable Retinopathy</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-400">Optical Quality:</span>
                  <span className="font-bold text-emerald-400">Pass (Score 69.6)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-400">CSME Proximity:</span>
                  <span className="font-bold text-amber-300">1.82 Disc Diameters</span>
                </div>
              </div>

              <div className="rounded-lg bg-stone-900/90 border border-stone-800 p-2.5 text-[10px] text-stone-400 leading-relaxed">
                Lipid hard exudates detected in posterior pole. Macular fovea within secondary margin. Formal ophthalmologist consult advised within 4 weeks.
              </div>

              <button
                type="button"
                onClick={() => onLaunchWorkstation()}
                className="w-full inline-flex items-center justify-center space-x-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-bold text-white hover:bg-emerald-500 transition"
              >
                <span>Interactive Live Mode</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 2. DEMOGRAPHIC REALITY (WHY THIS EXISTS)                     */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-700">
            The Rural Health Crisis
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
            Why Autonomous AI Screening is Vital in India
          </h2>
          <p className="text-xs text-stone-500 sm:text-sm">
            Addressing severe healthcare access disparities between metropolitan medical hubs and Primary Health Centres.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-stone-400 uppercase">Diabetic Cohort</span>
              <Users className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="text-3xl font-black text-slate-950">77.2 Million</div>
            <p className="text-xs text-stone-500 leading-relaxed">
              Adults in India currently living with diabetes, requiring mandatory annual retinal screening.
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-stone-400 uppercase">Doctor Deficit</span>
              <Compass className="h-5 w-5 text-amber-600" />
            </div>
            <div className="text-3xl font-black text-slate-950">1 : 100,000</div>
            <p className="text-xs text-stone-500 leading-relaxed">
              Ratio of ophthalmologists to population in rural regions, creating acute screening bottlenecks.
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-stone-400 uppercase">Preventability</span>
              <ShieldCheck className="h-5 w-5 text-sky-600" />
            </div>
            <div className="text-3xl font-black text-slate-950">80%+</div>
            <p className="text-xs text-stone-500 leading-relaxed">
              Of diabetic retinopathy blindness can be prevented with early diagnosis and timely referral.
            </p>
          </div>

          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-stone-400 uppercase">Edge Latency</span>
              <Clock className="h-5 w-5 text-indigo-600" />
            </div>
            <div className="text-3xl font-black text-slate-950">&lt; 2.5s</div>
            <p className="text-xs text-stone-500 leading-relaxed">
              End-to-end execution latency on standard commodity hardware, enabling instant point-of-care feedback.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 3. FOUR CORE ARCHITECTURAL PILLARS                           */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700">
            Engineered for Clinical Safety
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
            Four-Stage Autonomous Screening Pipeline
          </h2>
          <p className="text-xs text-stone-500 sm:text-sm">
            Rigorous multi-model architecture preventing false negative diagnoses from poor capture quality.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Pillar 1: IQA Gatekeeper */}
          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-3">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-800">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-950">
                  1. Optical Quality Gatekeeper (IQA)
                </h3>
                <span className="text-[11px] font-mono text-stone-400">
                  Laplacian Focus + ITU-R Illumination + FOV
                </span>
              </div>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed">
              Evaluates incoming fundus captures against hard optical floors. Severe motion blur or underexposure
              is halted immediately before inference, providing rural health workers with actionable recapture protocols.
            </p>
          </div>

          {/* Pillar 2: IDRiD Deep Segmenters */}
          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-3">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-800">
                <Layers className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-950">
                  2. Triple Deep Lesion Segmenters
                </h3>
                <span className="text-[11px] font-mono text-stone-400">
                  ResNet34 U-Nets (0.986 OD &bull; 0.758 Exudates &bull; 0.748 Hemorrhages)
                </span>
              </div>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed">
              Trained on high-resolution patches from the Indian Diabetic Retinopathy Image Dataset.
              Localizes optic disc landmarks, lipid hard exudates, and intraretinal microvascular bleed foci at native 512×512 resolution.
            </p>
          </div>

          {/* Pillar 3: CSME Proximity */}
          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-3">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-800">
                <Target className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-950">
                  3. CSME Macular Edema Risk Engine
                </h3>
                <span className="text-[11px] font-mono text-stone-400">
                  Foveal Displacement Vector &bull; Disc Diameter Scale
                </span>
              </div>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed">
              Translates anatomical optic disc coordinates to estimate the foveal avascular zone.
              Calculates exact Euclidean distance of hard exudates to detect Clinically Significant Macular Edema.
            </p>
          </div>

          {/* Pillar 4: Calibrated Referable Triage */}
          <div className="rounded-2xl border border-stone-200/90 bg-white p-6 shadow-xs space-y-3">
            <div className="flex items-center space-x-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-800">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-950">
                  4. Calibrated DR Severity Triage
                </h3>
                <span className="text-[11px] font-mono text-stone-400">
                  EfficientNetB3 (ICDR 0-4) &bull; Threshold 0.33
                </span>
              </div>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed">
              Frozen V2 classifier predicts 5-class distribution with a tuned referable cutoff ensuring &gt;90%
              sensitivity on sight-threatening Grade 2, 3, and 4 disease to prevent missed diagnoses.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. PRELOADED CLINICAL COHORT PREVIEW                         */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber-700">
              Verified Clinical Studies
            </span>
            <h2 className="text-2xl font-bold tracking-tight text-slate-950">
              Test Cohort Gallery
            </h2>
            <p className="text-xs text-stone-500">
              Click any verified clinical case to launch straight into the PACS diagnostic workstation.
            </p>
          </div>

          <button
            type="button"
            onClick={() => onNavigateTab("cohort")}
            className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-800 hover:text-emerald-700 transition"
          >
            <span>View All in Cohort Explorer</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* 4 Selected Sample Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {CLINICAL_SAMPLE_CASES.slice(0, 4).map((sample) => (
            <div
              key={sample.id}
              className="flex flex-col justify-between overflow-hidden rounded-2xl border border-stone-200/90 bg-white shadow-xs transition hover:border-stone-300 hover:shadow-md"
            >
              <div>
                <div className="relative aspect-video w-full overflow-hidden bg-slate-950">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={sample.imagePath}
                    alt={sample.title}
                    className="h-full w-full object-contain"
                  />
                  <div className="absolute top-2 left-2">
                    <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${sample.gradeBadgeColor}`}>
                      {sample.grade}
                    </span>
                  </div>
                </div>

                <div className="p-4 space-y-1.5">
                  <h4 className="text-xs font-bold text-slate-900">{sample.title}</h4>
                  <p className="text-[11px] text-stone-500 line-clamp-2">{sample.pathology}</p>
                </div>
              </div>

              <div className="border-t border-stone-100 p-3 bg-stone-50/50 flex items-center justify-between">
                <span className="font-mono text-[10px] text-stone-400">{sample.expectedTriage}</span>
                <button
                  type="button"
                  onClick={() => handleLaunchCase(sample)}
                  disabled={!!loadingCaseId}
                  className="inline-flex items-center space-x-1 rounded-lg bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white hover:bg-slate-800 transition"
                >
                  <span>{loadingCaseId === sample.id ? "Loading..." : "Test Case"}</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. BOTTOM CTA BANNER                                         */}
      {/* ============================================================ */}
      <section className="rounded-3xl border border-stone-800 bg-[#0c1220] p-8 sm:p-12 text-center text-white space-y-5 shadow-lg">
        <div className="max-w-2xl mx-auto space-y-3">
          <h3 className="text-2xl font-extrabold sm:text-3xl tracking-tight text-white">
            Experience Autonomous Point-of-Care Retinal Triage
          </h3>
          <p className="text-xs sm:text-sm text-stone-300 leading-relaxed">
            Launch the clinical workstation to evaluate real-time image quality gating,
            IDRiD deep lesion biomarkers, and explainable feature attributions.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => onLaunchWorkstation()}
            className="inline-flex items-center space-x-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-bold text-white shadow-xs hover:bg-emerald-500 transition"
          >
            <Activity className="h-4 w-4" />
            <span>Open Diagnostic Workstation</span>
            <ArrowRight className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={() => onNavigateTab("benchmarks")}
            className="inline-flex items-center space-x-2 rounded-xl border border-stone-700 bg-stone-850 px-5 py-3 text-sm font-semibold text-stone-200 hover:bg-stone-800 transition"
          >
            <BarChart3 className="h-4 w-4 text-amber-400" />
            <span>View IDRiD Model Benchmarks</span>
          </button>
        </div>
      </section>
    </div>
  );
};
