"use client";

import React, { useState, useEffect } from "react";
import {
  ArrowRight,
  Activity,
  Eye,
  CheckCircle2,
  ChevronRight,
  Scan,
  Layers,
  Cpu,
  FileCheck,
  ChevronUp,
  AlertOctagon,
  ArrowDown,
  ShieldCheck,
  FileText,
  Clock,
  Sparkles,
  Target,
  BarChart3,
  BrainCircuit,
  HeartPulse,
  Search,
  Play,
  Film,
  Sliders,
  Sun,
  Crosshair,
  Flame,
  Split,
  ZoomIn,
  Info,
  AlertTriangle,
  Droplets,
  Radio,
} from "lucide-react";
import { CLINICAL_SAMPLE_CASES, ClinicalSampleCase } from "./ClinicalSampleSelector";
import { UploadedImageMeta } from "@/types/screening";
import { formatBytes } from "@/lib/validation";

export interface ProductLandingPageProps {
  onLaunchWorkstation: (meta?: UploadedImageMeta) => void;
  onNavigateTab: (tab: "cohort" | "benchmarks") => void;
}

interface FlowchartNode {
  id: string;
  stepNumber: string;
  title: string;
  type: "input" | "gate" | "segment" | "classify" | "output";
  inputLabel: string;
  outputLabel: string;
  description: string;
  keyMetric: { label: string; value: string };
  badge: string;
}

const FLOWCHART_PIPELINE: FlowchartNode[] = [
  {
    id: "step-1",
    stepNumber: "01",
    title: "Raw Fundus Capture Intake",
    type: "input",
    inputLabel: "45° Posterior Pole Fundus",
    outputLabel: "Normalized RGB Matrix (512×512)",
    description: "Ingests raw fundus images from handheld or desktop clinical fundus cameras via local USB or file transfer.",
    keyMetric: { label: "Input Format", value: "DICOM / JPEG / PNG" },
    badge: "Optical Intake",
  },
  {
    id: "step-2",
    stepNumber: "02",
    title: "Optical Quality Gating",
    type: "gate",
    inputLabel: "Normalized Fundus Tensor",
    outputLabel: "Gradeable Pass or Reject Flag",
    description: "Evaluates illumination uniformity, focus sharpness, and signal-to-noise ratio. Automatically halts degraded images to prevent false classifications.",
    keyMetric: { label: "Gating Latency", value: "< 140ms" },
    badge: "Quality Gate",
  },
  {
    id: "step-3",
    stepNumber: "03",
    title: "Anatomical Landmark Localization",
    type: "segment",
    inputLabel: "Approved Gradeable Fundus",
    outputLabel: "Optic Disc Mask + Foveal Coordinates",
    description: "Segments the optic disc boundary and projects macula center to establish standardized CSME (Macular Edema) danger zones.",
    keyMetric: { label: "Optic Disc Dice", value: "0.9859" },
    badge: "Landmark U-Net",
  },
  {
    id: "step-4",
    stepNumber: "04",
    title: "Triple IDRiD Lesion Segmentation",
    type: "segment",
    inputLabel: "Retinal Vascular Field",
    outputLabel: "4 Pixel-Level Binary Masks",
    description: "Dual decoders segment primary DR hallmarks: Microaneurysms, Hemorrhages, Lipid Hard Exudates, and Cotton Wool Spots.",
    keyMetric: { label: "Hard Exudates Dice", value: "0.7580" },
    badge: "Lesion Decoders",
  },
  {
    id: "step-5",
    stepNumber: "05",
    title: "Calibrated DR Staging (ResNet-34)",
    type: "classify",
    inputLabel: "Deep Feature Representations",
    outputLabel: "Calibrated Severity Distribution",
    description: "Multiclass residual network outputs calibrated probabilities across Grade 0 (Normal) through Grade 4 (Proliferative DR).",
    keyMetric: { label: "Referable Sensitivity", value: "> 90%" },
    badge: "Staging Engine",
  },
  {
    id: "step-6",
    stepNumber: "06",
    title: "Clinical Decision Support & Triage",
    type: "output",
    inputLabel: "Grade + Lesion Load + Foveal Distance",
    outputLabel: "Triage Window & Vector PDF Dossier",
    description: "Generates actionable referral urgency timelines (e.g. 4-week consult for CSME risk) and printable clinical audit reports.",
    keyMetric: { label: "Export Format", value: "Vector PDF / FHIR" },
    badge: "Clinical Dossier",
  },
];

export const ProductLandingPage: React.FC<ProductLandingPageProps> = ({
  onLaunchWorkstation,
  onNavigateTab,
}) => {
  const [loadingCaseId, setLoadingCaseId] = useState<string | null>(null);
  const [showScrollTop, setShowScrollTop] = useState<boolean>(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("step-2");
  const [activePillar, setActivePillar] = useState<string | null>(null);
  // Visual inspection interactive states for continuous scrolling section
  const [contrastViewMode, setContrastViewMode] = useState<"split" | "raw" | "enhanced">("split");
  const [vesselViewMode, setVesselViewMode] = useState<"map" | "overlay">("map");
  const [activeLesionFilter, setActiveLesionFilter] = useState<"all" | "hems" | "exudates" | "cws">("all");

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 400);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

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
    <div className="w-full bg-white text-neutral-900 selection:bg-black selection:text-white">
      {/* ============================================================ */}
      {/* 1. HERO SECTION: FULL SCREEN EYE VIDEO (ZERO TOP NAVBAR)      */}
      {/* ============================================================ */}
      <section className="relative h-screen w-full overflow-hidden flex flex-col justify-between bg-black">
        {/* Background Looping Eye Video (Pure Neutral Black, Zero Blue Cast) */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
          <video
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full object-cover opacity-80 scale-105"
          >
            <source
              src="https://cdn.prod.website-files.com/69706869defa1efb2ed0e3df%2F69773ae6cc7ceafc548220c1_Oculomics%20%281%29_mp4.mp4"
              type="video/mp4"
            />
          </video>
          {/* Neutral Cinematic Dark Gradients - Zero Blue Cast */}
          <div className="absolute inset-0 bg-gradient-to-r from-black/95 via-black/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/70" />
        </div>

        {/* Top Spacer - NO NAVBAR on Landing Hero (Navbar appears upon Launching Workstation) */}
        <div className="relative z-10 w-full pt-12 sm:pt-16" />

        {/* Center Minimalist Hero Typography */}
        <div className="relative z-10 w-full max-w-6xl mx-auto px-6 sm:px-10 lg:px-12 flex-1 flex flex-col justify-center">
          <div className="max-w-2xl space-y-6 text-white">
            {/* Minimal Brand & PS Badge */}
            <div className="inline-flex items-center space-x-2 rounded-lg border border-white/15 bg-white/10 px-3.5 py-1.5 text-xs font-semibold text-neutral-200 backdrop-blur-md">
              <span className="font-bold tracking-tight text-white">RetinaScan AI</span>
              <span className="text-white/40">&bull;</span>
              <span className="font-mono text-neutral-300">Smart India Hackathon PS 26038</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-[1.08] text-white">
              Diabetic Retinopathy Screening for the{" "}
              <span className="text-emerald-400">
                Next Billion
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-neutral-300 leading-relaxed font-normal max-w-xl">
              Autonomous clinical decision support, optical quality gating, and explainable
              IDRiD lesion segmentation in under 2.5 seconds on edge hardware.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                type="button"
                onClick={() => onLaunchWorkstation()}
                className="inline-flex items-center space-x-3 rounded-xl bg-emerald-500 px-7 py-4 text-sm font-bold text-black shadow-xl shadow-emerald-950/40 transition hover:bg-emerald-400 hover:scale-[1.02] active:scale-[0.98]"
              >
                <Activity className="h-4 w-4" />
                <span>Launch Workstation</span>
                <ArrowRight className="h-4 w-4" />
              </button>

              <a
                href="#pipeline-flowchart"
                className="inline-flex items-center space-x-2.5 rounded-xl border border-white/20 bg-white/10 px-6 py-4 text-sm font-semibold text-white backdrop-blur-md transition hover:bg-white/20 hover:border-white/40"
              >
                <Layers className="h-4 w-4 text-emerald-400" />
                <span>Explore Diagnostic Flowchart</span>
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Hero Metric Bar */}
        <div className="relative z-10 w-full border-t border-white/10 bg-black/50 backdrop-blur-xs py-4">
          <div className="max-w-6xl mx-auto px-6 sm:px-10 lg:px-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-neutral-400">
            <div className="flex flex-wrap items-center gap-6 sm:gap-10">
              <div>
                <span className="text-base sm:text-lg font-bold text-white">0.9859</span>
                <span className="text-[11px] text-neutral-400 ml-2">Optic Disc Dice</span>
              </div>
              <div className="h-4 w-px bg-white/15 hidden sm:block" />
              <div>
                <span className="text-base sm:text-lg font-bold text-white">0.7580</span>
                <span className="text-[11px] text-neutral-400 ml-2">Hard Exudates</span>
              </div>
              <div className="h-4 w-px bg-white/15 hidden sm:block" />
              <div>
                <span className="text-base sm:text-lg font-bold text-white">0.7482</span>
                <span className="text-[11px] text-neutral-400 ml-2">Hemorrhages</span>
              </div>
              <div className="h-4 w-px bg-white/15 hidden sm:block" />
              <div>
                <span className="text-base sm:text-lg font-bold text-emerald-400">&lt; 2.5s</span>
                <span className="text-[11px] text-neutral-400 ml-2">Edge Latency</span>
              </div>
            </div>

            <a
              href="#pipeline-flowchart"
              className="flex items-center space-x-1.5 text-neutral-400 hover:text-white transition text-[11px]"
            >
              <span>View 6-Stage Clinical Flowchart</span>
              <ArrowDown className="h-3.5 w-3.5 text-emerald-400" />
            </a>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 2. PROPER CLINICAL DIAGNOSTIC FLOW CHART                     */}
      {/* ============================================================ */}
      <section id="pipeline-flowchart" className="w-full bg-[#fafafa] py-20 lg:py-28 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-12">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-900">
              Smart India Hackathon 2026 &bull; PS 26038 Architecture Flow
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
              RetinaScan Clinical Diagnostic Flowchart
            </h2>
            <p className="text-neutral-600 text-sm sm:text-base leading-relaxed">
              Step-by-step mathematical flow from optical capture intake through quality gating,
              dual-decoder IDRiD lesion extraction, calibrated DR staging, and clinical triage.
            </p>
          </div>

          {/* Interactive Flowchart Diagram */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Visual Flowchart Stages (7 cols) */}
            <div className="lg:col-span-7 space-y-3">
              {/* STAGE 1: Optical Intake */}
              <div
                onClick={() => setSelectedNodeId("step-1")}
                className={`cursor-pointer rounded-2xl border p-5 transition duration-150 ${
                  selectedNodeId === "step-1"
                    ? "border-black bg-white shadow-md ring-2 ring-black/10"
                    : "border-neutral-200 bg-white hover:border-neutral-400 shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black font-mono text-xs font-bold text-white">
                      01
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                        Input Modality
                      </div>
                      <h4 className="text-base font-bold text-black">
                        Raw Fundus Optical Capture Intake
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-neutral-700 border border-neutral-200">
                    512×512 RGB
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs border-t border-neutral-100 pt-3">
                  <div>
                    <span className="text-[10px] text-neutral-400 uppercase font-mono block">Input Source</span>
                    <span className="font-medium text-neutral-700">Handheld / Tabletop Fundus Camera</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-neutral-400 uppercase font-mono block">Preprocessing</span>
                    <span className="font-medium text-neutral-700">CLAHE Contrast + Color Normalization</span>
                  </div>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center py-0.5">
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </div>

              {/* STAGE 2: Quality Gatekeeper with Conditional Decision Diamond */}
              <div
                onClick={() => setSelectedNodeId("step-2")}
                className={`cursor-pointer rounded-2xl border-2 p-5 transition duration-150 ${
                  selectedNodeId === "step-2"
                    ? "border-black bg-neutral-50 shadow-md ring-2 ring-black/10"
                    : "border-neutral-300 bg-white hover:border-black shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black font-mono text-xs font-bold text-white">
                      02
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                        Quality Gatekeeper &bull; Branch Decision
                      </div>
                      <h4 className="text-base font-bold text-black">
                        Optical Quality Gating (Focus &amp; Illumination SNR)
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-100 border border-neutral-300 px-2 py-0.5 font-mono text-[10px] font-bold text-black">
                    &lt; 140ms
                  </span>
                </div>

                {/* Branching Decision Box */}
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs border-t border-neutral-200 pt-3">
                  <div className="rounded-xl border border-neutral-300 bg-white p-2.5 space-y-1">
                    <div className="flex items-center space-x-1.5 text-black font-bold text-xs">
                      <CheckCircle2 className="h-3.5 w-3.5 text-black shrink-0" />
                      <span>PASS: SNR &ge; 50 dB</span>
                    </div>
                    <p className="text-[11px] text-neutral-600 leading-tight">
                      Gradeable fundus &rarr; Proceed to Anatomical &amp; Lesion Decoders.
                    </p>
                  </div>
                  <div className="rounded-xl border border-neutral-300 bg-neutral-100/70 p-2.5 space-y-1">
                    <div className="flex items-center space-x-1.5 text-neutral-900 font-bold text-xs">
                      <AlertOctagon className="h-3.5 w-3.5 text-neutral-800 shrink-0" />
                      <span>FAIL: SNR &lt; 50 dB</span>
                    </div>
                    <p className="text-[11px] text-neutral-600 leading-tight">
                      Immediate Recapture Prompt. Halts inference to stop hallucinations.
                    </p>
                  </div>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center py-0.5">
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </div>

              {/* STAGE 3: Anatomical Localization */}
              <div
                onClick={() => setSelectedNodeId("step-3")}
                className={`cursor-pointer rounded-2xl border p-5 transition duration-150 ${
                  selectedNodeId === "step-3"
                    ? "border-black bg-white shadow-md ring-2 ring-black/10"
                    : "border-neutral-200 bg-white hover:border-neutral-400 shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black font-mono text-xs font-bold text-white">
                      03
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                        Anatomical Localization
                      </div>
                      <h4 className="text-base font-bold text-black">
                        Optic Disc Boundary &amp; Foveal Zone Projector
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-100 border border-neutral-300 px-2 py-0.5 font-mono text-[10px] font-bold text-black">
                    Dice: 0.9859
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs border-t border-neutral-100 pt-3">
                  <div>
                    <span className="text-[10px] text-neutral-400 uppercase font-mono block">Landmark Model</span>
                    <span className="font-medium text-neutral-700">Optic Disc Segmentation U-Net</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-neutral-400 uppercase font-mono block">Clinical Output</span>
                    <span className="font-medium text-neutral-700">1-DD &amp; 2-DD CSME Danger Radius</span>
                  </div>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center py-0.5">
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </div>

              {/* STAGE 4: Triple IDRiD Lesion Segmentation */}
              <div
                onClick={() => setSelectedNodeId("step-4")}
                className={`cursor-pointer rounded-2xl border p-5 transition duration-150 ${
                  selectedNodeId === "step-4"
                    ? "border-black bg-white shadow-md ring-2 ring-black/10"
                    : "border-neutral-200 bg-white hover:border-neutral-400 shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black font-mono text-xs font-bold text-white">
                      04
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                        Dual U-Net Decoders
                      </div>
                      <h4 className="text-base font-bold text-black">
                        Triple IDRiD Lesion Pixel Extraction
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-100 border border-neutral-300 px-2 py-0.5 font-mono text-[10px] font-bold text-black">
                    Exudates: 0.7580
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs border-t border-neutral-100 pt-3">
                  <div className="bg-neutral-100 p-2 rounded-lg text-center border border-neutral-200">
                    <span className="text-[10px] text-neutral-400 block font-mono">MA</span>
                    <span className="font-bold text-neutral-900 text-[11px]">Microaneurysms</span>
                  </div>
                  <div className="bg-neutral-100 p-2 rounded-lg text-center border border-neutral-200">
                    <span className="text-[10px] text-neutral-400 block font-mono">HE (0.7482)</span>
                    <span className="font-bold text-neutral-900 text-[11px]">Hemorrhages</span>
                  </div>
                  <div className="bg-neutral-100 p-2 rounded-lg text-center border border-neutral-200">
                    <span className="text-[10px] text-neutral-400 block font-mono">EX (0.7580)</span>
                    <span className="font-bold text-neutral-900 text-[11px]">Hard Exudates</span>
                  </div>
                  <div className="bg-neutral-100 p-2 rounded-lg text-center border border-neutral-200">
                    <span className="text-[10px] text-neutral-400 block font-mono">SE</span>
                    <span className="font-bold text-neutral-900 text-[11px]">Cotton Wool</span>
                  </div>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center py-0.5">
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </div>

              {/* STAGE 5: Multi-Class Staging */}
              <div
                onClick={() => setSelectedNodeId("step-5")}
                className={`cursor-pointer rounded-2xl border p-5 transition duration-150 ${
                  selectedNodeId === "step-5"
                    ? "border-black bg-white shadow-md ring-2 ring-black/10"
                    : "border-neutral-200 bg-white hover:border-neutral-400 shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-black font-mono text-xs font-bold text-white">
                      05
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                        Deep Multi-Class Classifier
                      </div>
                      <h4 className="text-base font-bold text-black">
                        ResNet-34 DR Severity Staging (Grades 0 &ndash; 4)
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-100 border border-neutral-300 px-2 py-0.5 font-mono text-[10px] font-bold text-black">
                    &gt; 90% Sens.
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs border-t border-neutral-100 pt-3 font-mono">
                  <span className="text-neutral-600 text-[11px]">Grade 0: Normal</span>
                  <span className="text-neutral-300">&rarr;</span>
                  <span className="text-neutral-600 text-[11px]">Grade 1: Mild</span>
                  <span className="text-neutral-300">&rarr;</span>
                  <span className="text-neutral-600 text-[11px]">Grade 2: Mod</span>
                  <span className="text-neutral-300">&rarr;</span>
                  <span className="text-neutral-600 text-[11px]">Grade 3: Sev</span>
                  <span className="text-neutral-300">&rarr;</span>
                  <span className="text-black font-bold text-[11px] bg-neutral-200 px-1.5 py-0.5 rounded">Grade 4: PDR</span>
                </div>
              </div>

              {/* Connector */}
              <div className="flex justify-center py-0.5">
                <ArrowDown className="h-4 w-4 text-neutral-400" />
              </div>

              {/* STAGE 6: Clinical Triage Dossier */}
              <div
                onClick={() => setSelectedNodeId("step-6")}
                className={`cursor-pointer rounded-2xl border p-5 transition duration-150 ${
                  selectedNodeId === "step-6"
                    ? "border-black bg-black text-white shadow-lg ring-2 ring-black/20"
                    : "border-neutral-900 bg-neutral-950 text-white hover:border-neutral-700 shadow-md"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white font-mono text-xs font-bold text-black">
                      06
                    </span>
                    <div>
                      <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                        Clinical Decision Support
                      </div>
                      <h4 className="text-base font-bold text-white">
                        Referral Urgency Triage &amp; Vector PDF Dossier
                      </h4>
                    </div>
                  </div>
                  <span className="rounded-md bg-neutral-800 border border-neutral-700 px-2 py-0.5 font-mono text-[10px] font-bold text-neutral-200">
                    PDF / FHIR
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs border-t border-neutral-800 pt-3">
                  <span className="text-neutral-400 text-xs">
                    Structured Referral Timeline + CSME Proximity Alert
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onLaunchWorkstation();
                    }}
                    className="inline-flex items-center space-x-1.5 rounded-lg bg-white px-3 py-1 text-xs font-bold text-black hover:bg-neutral-200 transition"
                  >
                    <span>Launch Workstation</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Right Column: Node Detailed Inspector Panel (5 cols) */}
            <div className="lg:col-span-5 lg:sticky lg:top-24 space-y-4">
              {(() => {
                const node = FLOWCHART_PIPELINE.find((n) => n.id === selectedNodeId) || FLOWCHART_PIPELINE[1];
                return (
                  <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm space-y-5">
                    <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-white bg-black px-2 py-0.5 rounded">
                          STAGE {node.stepNumber}
                        </span>
                        <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                          Technical Inspector
                        </span>
                      </div>
                      <span className="rounded-full bg-neutral-100 px-2.5 py-0.5 text-[11px] font-semibold text-neutral-700 border border-neutral-200">
                        {node.badge}
                      </span>
                    </div>

                    <div className="space-y-2">
                      <h3 className="text-xl font-extrabold text-black">
                        {node.title}
                      </h3>
                      <p className="text-xs sm:text-sm text-neutral-600 leading-relaxed">
                        {node.description}
                      </p>
                    </div>

                    <div className="space-y-3 bg-neutral-50 p-4 rounded-xl border border-neutral-200 text-xs">
                      <div>
                        <span className="text-[10px] font-mono uppercase text-neutral-400 font-bold block">
                          Tensor Input
                        </span>
                        <span className="font-medium text-neutral-900">
                          {node.inputLabel}
                        </span>
                      </div>

                      <div className="border-t border-neutral-200 pt-2">
                        <span className="text-[10px] font-mono uppercase text-neutral-400 font-bold block">
                          Diagnostic Output
                        </span>
                        <span className="font-medium text-neutral-900">
                          {node.outputLabel}
                        </span>
                      </div>

                      <div className="border-t border-neutral-200 pt-2 flex items-center justify-between">
                        <span className="text-[10px] font-mono uppercase text-neutral-400 font-bold">
                          {node.keyMetric.label}
                        </span>
                        <span className="font-mono font-bold text-black bg-white px-2 py-0.5 rounded border border-neutral-300">
                          {node.keyMetric.value}
                        </span>
                      </div>
                    </div>

                    {/* Step-specific Clinical Guidance */}
                    <div className="rounded-xl border border-neutral-200 bg-neutral-100/60 p-3.5 text-xs text-neutral-800 space-y-1">
                      <span className="font-bold flex items-center space-x-1.5 text-black text-[11px]">
                        <ShieldCheck className="h-3.5 w-3.5 text-black" />
                        <span>Clinical Safety Protocol</span>
                      </span>
                      <p className="text-[11px] text-neutral-600 leading-relaxed">
                        {node.id === "step-1" && "Supports raw uncompressed DICOM and 8-bit RGB camera streams. Zero lossy compression applied prior to inference."}
                        {node.id === "step-2" && "Catches out-of-focus, low-SNR, or cataract-obscured captures instantly. Guarantees zero downstream diagnostic hallucinations."}
                        {node.id === "step-3" && "Establishes anatomical coordinate frame. Prevents normal optic disc physiological cup from being confused with cotton wool spots."}
                        {node.id === "step-4" && "Trained specifically on IDRiD pixel annotations to resolve punctate microaneurysms under 10 microns diameter."}
                        {node.id === "step-5" && "Temperature scaling aligns network confidence with clinical empirical risk, avoiding overconfident misclassifications."}
                        {node.id === "step-6" && "Generates reproducible audit trails compliant with tele-ophthalmology screening guidelines and rural PHC triage workflows."}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => onLaunchWorkstation()}
                      className="w-full inline-flex items-center justify-center space-x-2 rounded-xl bg-black py-3 text-xs font-bold text-white hover:bg-neutral-800 transition shadow-xs active:scale-[0.99]"
                    >
                      <Activity className="h-3.5 w-3.5 text-white" />
                      <span>Execute Full Pipeline in Workstation</span>
                    </button>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 3. IMPACT & OCULOMICS: PREVENTING DIABETIC BLINDNESS         */}
      {/* ============================================================ */}
      <section className="w-full bg-white py-20 lg:py-28 border-b border-neutral-200 overflow-hidden">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-16">
          {/* Section Header Tailored to RetinaScan AI Project Context */}
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-black tracking-tight leading-[1.18]">
              Preventing Diabetic Blindness,<br />
              <span className="font-medium text-neutral-800">Enabling Rural Eye Care Through </span>
              <span className="text-black font-extrabold">AI.</span>
            </h2>
            <p className="text-neutral-600 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
              Addressing India&apos;s 77M+ diabetic population and 1:100,000 rural specialist gap &mdash;
              RetinaScan AI equips frontline ASHA and PHC staff with offline edge inference,
              4-metric optical safety gating, and explainable IDRiD lesion mapping.
            </p>
          </div>

          {/* Desktop Interactive Graphic (md: and up) */}
          <div className="relative max-w-5xl mx-auto hidden md:block">
            {/* Background Connector & Eye Graphic SVG */}
            <div className="relative w-full aspect-[2/1] max-h-[440px]">
              <svg
                viewBox="0 0 900 440"
                className="w-full h-full"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <linearGradient id="eyeEyelidGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#18181b" />
                    <stop offset="50%" stopColor="#27272a" />
                    <stop offset="100%" stopColor="#18181b" />
                  </linearGradient>
                </defs>

                {/* Radiating Eyelashes / Tick Marks */}
                <g stroke="#cbd5e1" strokeWidth="5" strokeLinecap="round" opacity="0.8">
                  {/* Top ticks */}
                  <line x1="410" y1="135" x2="400" y2="105" />
                  <line x1="450" y1="130" x2="450" y2="95" />
                  <line x1="490" y1="135" x2="500" y2="105" />
                  {/* Bottom ticks */}
                  <line x1="410" y1="305" x2="400" y2="335" />
                  <line x1="450" y1="310" x2="450" y2="345" />
                  <line x1="490" y1="305" x2="500" y2="335" />
                  {/* Diagonal ticks */}
                  <line x1="355" y1="165" x2="335" y2="145" />
                  <line x1="545" y1="165" x2="565" y2="145" />
                  <line x1="355" y1="275" x2="335" y2="295" />
                  <line x1="545" y1="275" x2="565" y2="295" />
                </g>

                {/* Connecting Pointer Lines to Callouts */}
                {/* 1. Top-Left: AI-Driven DR Detection */}
                <path
                  d="M 435 150 L 360 70 L 220 70"
                  stroke={activePillar === "dr-detection" ? "#000000" : "#cbd5e1"}
                  strokeWidth={activePillar === "dr-detection" ? "2.5" : "1.5"}
                  className="transition-all duration-200"
                />
                {/* 2. Bottom-Left: Retinal Imaging at Scale */}
                <path
                  d="M 315 235 L 260 300 L 220 300"
                  stroke={activePillar === "imaging-scale" ? "#000000" : "#cbd5e1"}
                  strokeWidth={activePillar === "imaging-scale" ? "2.5" : "1.5"}
                  className="transition-all duration-200"
                />
                {/* 3. Top-Right: Explainable Lesion Mapping */}
                <path
                  d="M 585 235 L 635 170 L 680 170"
                  stroke={activePillar === "lesion-mapping" ? "#000000" : "#cbd5e1"}
                  strokeWidth={activePillar === "lesion-mapping" ? "2.5" : "1.5"}
                  className="transition-all duration-200"
                />
                {/* 4. Bottom-Right: Rural Health Impact */}
                <path
                  d="M 510 280 L 565 350 L 680 350"
                  stroke={activePillar === "rural-health" ? "#000000" : "#cbd5e1"}
                  strokeWidth={activePillar === "rural-health" ? "2.5" : "1.5"}
                  className="transition-all duration-200"
                />

                {/* Stylized Eye Eyelid Curves (Clinical Charcoal) */}
                {/* Upper Arc */}
                <path
                  d="M 305 220 C 355 115, 545 115, 595 220"
                  stroke="url(#eyeEyelidGrad)"
                  strokeWidth="11"
                  strokeLinecap="round"
                />
                {/* Lower Arc */}
                <path
                  d="M 305 220 C 355 325, 545 325, 595 220"
                  stroke="url(#eyeEyelidGrad)"
                  strokeWidth="11"
                  strokeLinecap="round"
                />

                {/* Central AI Iris & Pupil */}
                <circle
                  cx="450"
                  cy="220"
                  r="50"
                  stroke="#000000"
                  strokeWidth="8.5"
                  fill="#ffffff"
                  className="shadow-sm"
                />
                <text
                  x="450"
                  y="232"
                  textAnchor="middle"
                  fill="#000000"
                  fontSize="32"
                  fontWeight="800"
                  fontFamily="sans-serif"
                >
                  AI
                </text>

                {/* 4 Characteristic Anchor Nodes on the Eye */}
                {/* Node 1: Top-Left */}
                <g
                  className="cursor-pointer transition-transform duration-200"
                  onMouseEnter={() => setActivePillar("dr-detection")}
                  onMouseLeave={() => setActivePillar(null)}
                >
                  <circle
                    cx="435"
                    cy="150"
                    r={activePillar === "dr-detection" ? "11" : "8.5"}
                    fill="#ffffff"
                    stroke="#000000"
                    strokeWidth="3.5"
                    className="shadow-md"
                  />
                  <circle cx="435" cy="150" r="3.5" fill="#000000" />
                </g>

                {/* Node 2: Bottom-Left */}
                <g
                  className="cursor-pointer transition-transform duration-200"
                  onMouseEnter={() => setActivePillar("imaging-scale")}
                  onMouseLeave={() => setActivePillar(null)}
                >
                  <circle
                    cx="315"
                    cy="235"
                    r={activePillar === "imaging-scale" ? "11" : "8.5"}
                    fill="#ffffff"
                    stroke="#000000"
                    strokeWidth="3.5"
                    className="shadow-md"
                  />
                  <circle cx="315" cy="235" r="3.5" fill="#000000" />
                </g>

                {/* Node 3: Top-Right */}
                <g
                  className="cursor-pointer transition-transform duration-200"
                  onMouseEnter={() => setActivePillar("lesion-mapping")}
                  onMouseLeave={() => setActivePillar(null)}
                >
                  <circle
                    cx="585"
                    cy="235"
                    r={activePillar === "lesion-mapping" ? "11" : "8.5"}
                    fill="#ffffff"
                    stroke="#000000"
                    strokeWidth="3.5"
                    className="shadow-md"
                  />
                  <circle cx="585" cy="235" r="3.5" fill="#000000" />
                </g>

                {/* Node 4: Bottom-Right */}
                <g
                  className="cursor-pointer transition-transform duration-200"
                  onMouseEnter={() => setActivePillar("rural-health")}
                  onMouseLeave={() => setActivePillar(null)}
                >
                  <circle
                    cx="510"
                    cy="280"
                    r={activePillar === "rural-health" ? "11" : "8.5"}
                    fill="#ffffff"
                    stroke="#000000"
                    strokeWidth="3.5"
                    className="shadow-md"
                  />
                  <circle cx="510" cy="280" r="3.5" fill="#000000" />
                </g>
              </svg>

              {/* Callout Cards Positioned Over / Beside the Graphic */}
              {/* Callout 1: Top-Left (AI-Driven DR Detection) */}
              <div
                onMouseEnter={() => setActivePillar("dr-detection")}
                onMouseLeave={() => setActivePillar(null)}
                className={`absolute left-0 top-0 max-w-[270px] p-3.5 rounded-2xl transition duration-200 cursor-pointer ${
                  activePillar === "dr-detection"
                    ? "bg-white shadow-lg ring-2 ring-black"
                    : "bg-white/95 hover:bg-white shadow-xs border border-neutral-200"
                }`}
              >
                <div className="flex items-center space-x-3 mb-1.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <BrainCircuit className="h-5 w-5 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black leading-tight">
                      AI-Driven DR Detection
                    </h4>
                    <span className="font-mono text-[10px] font-semibold text-neutral-600">
                      5-Class ICDR &bull; &gt;90% Sens.
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-neutral-600 leading-snug">
                  Our deep residual model stages Grade 0 (None) through Grade 4 (PDR) with calibrated probabilities in under 2.5s on edge hardware.
                </p>
              </div>

              {/* Callout 2: Bottom-Left (Retinal Imaging at Scale) */}
              <div
                onMouseEnter={() => setActivePillar("imaging-scale")}
                onMouseLeave={() => setActivePillar(null)}
                className={`absolute left-0 bottom-2 max-w-[270px] p-3.5 rounded-2xl transition duration-200 cursor-pointer ${
                  activePillar === "imaging-scale"
                    ? "bg-white shadow-lg ring-2 ring-black"
                    : "bg-white/95 hover:bg-white shadow-xs border border-neutral-200"
                }`}
              >
                <div className="flex items-center space-x-3 mb-1.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <Scan className="h-5 w-5 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black leading-tight">
                      Retinal Imaging at Scale
                    </h4>
                    <span className="font-mono text-[10px] font-semibold text-neutral-600">
                      4-Metric IQA &bull; &lt;140ms Gating
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-neutral-600 leading-snug">
                  Upstream optical safety gate evaluates focus, illumination, and FOV aperture to halt degraded images and guide immediate ASHA worker recapture.
                </p>
              </div>

              {/* Callout 3: Top-Right (Explainable Lesion Mapping) */}
              <div
                onMouseEnter={() => setActivePillar("lesion-mapping")}
                onMouseLeave={() => setActivePillar(null)}
                className={`absolute right-0 top-6 max-w-[270px] p-3.5 rounded-2xl transition duration-200 cursor-pointer ${
                  activePillar === "lesion-mapping"
                    ? "bg-white shadow-lg ring-2 ring-black"
                    : "bg-white/95 hover:bg-white shadow-xs border border-neutral-200"
                }`}
              >
                <div className="flex items-center space-x-3 mb-1.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <Search className="h-5 w-5 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black leading-tight">
                      Explainable Lesion Mapping
                    </h4>
                    <span className="font-mono text-[10px] font-semibold text-neutral-600">
                      Dual XAI &bull; IDRiD Ground Truth
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-neutral-600 leading-snug">
                  Dual-decoder U-Nets extract Hard Exudates (0.7580 Dice), Hemorrhages (0.7482 Dice), and Optic Disc (0.9859 Dice) with CSME foveal clearance.
                </p>
              </div>

              {/* Callout 4: Bottom-Right (Rural Health Impact) */}
              <div
                onMouseEnter={() => setActivePillar("rural-health")}
                onMouseLeave={() => setActivePillar(null)}
                className={`absolute right-0 bottom-0 max-w-[270px] p-3.5 rounded-2xl transition duration-200 cursor-pointer ${
                  activePillar === "rural-health"
                    ? "bg-white shadow-lg ring-2 ring-black"
                    : "bg-white/95 hover:bg-white shadow-xs border border-neutral-200"
                }`}
              >
                <div className="flex items-center space-x-3 mb-1.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <HeartPulse className="h-5 w-5 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black leading-tight">
                      Rural Health Impact
                    </h4>
                    <span className="font-mono text-[10px] font-semibold text-neutral-600">
                      Simulink Verified &bull; 100k+ / Year
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-neutral-600 leading-snug">
                  MathWorks Simulink 8-subsystem discrete-event model verifies throughput for 100,000+ rural screenings annually with zero cloud dependence.
                </p>
              </div>
            </div>
          </div>

          {/* Mobile Layout (sm: and down) */}
          <div className="block md:hidden space-y-6">
            {/* Centered Minimal Eye Graphic */}
            <div className="max-w-[300px] mx-auto">
              <svg
                viewBox="0 0 400 240"
                className="w-full h-auto"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <defs>
                  <linearGradient id="eyeMobileGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#18181b" />
                    <stop offset="50%" stopColor="#27272a" />
                    <stop offset="100%" stopColor="#18181b" />
                  </linearGradient>
                </defs>
                <g stroke="#cbd5e1" strokeWidth="4" strokeLinecap="round" opacity="0.8">
                  <line x1="200" y1="40" x2="200" y2="15" />
                  <line x1="160" y1="45" x2="150" y2="20" />
                  <line x1="240" y1="45" x2="250" y2="20" />
                  <line x1="200" y1="200" x2="200" y2="225" />
                  <line x1="160" y1="195" x2="150" y2="220" />
                  <line x1="240" y1="195" x2="250" y2="220" />
                </g>
                <path
                  d="M 60 120 C 110 30, 290 30, 340 120"
                  stroke="url(#eyeMobileGrad)"
                  strokeWidth="10"
                  strokeLinecap="round"
                />
                <path
                  d="M 60 120 C 110 210, 290 210, 340 120"
                  stroke="url(#eyeMobileGrad)"
                  strokeWidth="10"
                  strokeLinecap="round"
                />
                <circle cx="200" cy="120" r="44" stroke="#000000" strokeWidth="8" fill="#ffffff" />
                <text
                  x="200"
                  y="131"
                  textAnchor="middle"
                  fill="#000000"
                  fontSize="28"
                  fontWeight="800"
                >
                  AI
                </text>
              </svg>
            </div>

            {/* 4 Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-xs space-y-2">
                <div className="flex items-center space-x-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <BrainCircuit className="h-4 w-4 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black">AI-Driven DR Detection</h4>
                    <span className="font-mono text-[10px] text-neutral-600 font-semibold">5-Class ICDR</span>
                  </div>
                </div>
                <p className="text-xs text-neutral-600">
                  Calibrated ResNet-34 classification staging Grade 0 to 4 in &lt;2.5s on edge hardware with &gt;90% sensitivity.
                </p>
              </div>

              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-xs space-y-2">
                <div className="flex items-center space-x-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <Scan className="h-4 w-4 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black">Retinal Imaging at Scale</h4>
                    <span className="font-mono text-[10px] text-neutral-600 font-semibold">4-Metric IQA</span>
                  </div>
                </div>
                <p className="text-xs text-neutral-600">
                  Optical safety interlock halts blurry or dark images in &lt;140ms and triggers real-time ASHA recapture prompts.
                </p>
              </div>

              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-xs space-y-2">
                <div className="flex items-center space-x-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <Search className="h-4 w-4 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black">Explainable Lesion Mapping</h4>
                    <span className="font-mono text-[10px] text-neutral-600 font-semibold">IDRiD Dual XAI</span>
                  </div>
                </div>
                <p className="text-xs text-neutral-600">
                  U-Net decoders extract exudates (0.7580 Dice), hemorrhages (0.7482 Dice), and Optic Disc (0.9859 Dice).
                </p>
              </div>

              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-xs space-y-2">
                <div className="flex items-center space-x-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-neutral-100 border border-neutral-300 text-black shrink-0">
                    <HeartPulse className="h-4 w-4 stroke-[2.2]" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-black">Rural Health Impact</h4>
                    <span className="font-mono text-[10px] text-neutral-600 font-semibold">Simulink 100k+ / Year</span>
                  </div>
                </div>
                <p className="text-xs text-neutral-600">
                  MathWorks Simulink 8-subsystem verified architecture proving 100,000+ rural screenings annually offline.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. LIVE WORKSTATION VIDEO DEMONSTRATION                      */}
      {/* ============================================================ */}
      <section id="system-demo" className="w-full bg-[#fafafa] py-20 lg:py-28 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-12">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-900">
              Live System Runthrough &bull; Workstation Demo
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
              See RetinaScan AI in Action
            </h2>
            <p className="text-neutral-600 text-sm sm:text-base leading-relaxed">
              Complete end-to-end clinical screening runthrough &mdash; from optical quality gating
              and 5-class ICDR severity staging through IDRiD pixel lesion segmentation and signed PDF dossier compilation.
            </p>
          </div>

          {/* Video Player Display Container */}
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Clean, Modern Video Player Frame (No fake browser chrome or nested window dots) */}
            <div className="overflow-hidden rounded-2xl sm:rounded-3xl border border-neutral-300 bg-black shadow-2xl shadow-neutral-200/60">
              <video
                controls
                playsInline
                preload="metadata"
                poster="/videos/demo_poster.jpg"
                className="w-full aspect-video block bg-black object-contain"
              >
                <source src="/videos/demo.mp4" type="video/mp4" />
                <source src="/videos/demo.mov" type="video/quicktime" />
                Your browser does not support HTML5 video.
              </video>
            </div>

            {/* Workflow Step Highlights Below Video */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="rounded-xl border border-neutral-200 bg-white p-3.5 shadow-2xs space-y-1">
                <span className="font-mono text-[10px] font-bold text-black block uppercase">Phase 01</span>
                <h4 className="font-bold text-black text-xs">Optical IQA Gate</h4>
                <p className="text-[11px] text-neutral-500 leading-snug">
                  4-metric focus and illumination SNR gating in &lt;140ms.
                </p>
              </div>
              <div className="rounded-xl border border-neutral-200 bg-white p-3.5 shadow-2xs space-y-1">
                <span className="font-mono text-[10px] font-bold text-black block uppercase">Phase 02</span>
                <h4 className="font-bold text-black text-xs">5-Class DR Staging</h4>
                <p className="text-[11px] text-neutral-500 leading-snug">
                  Calibrated ResNet-34 severity probabilities in &lt;2.5s.
                </p>
              </div>
              <div className="rounded-xl border border-neutral-200 bg-white p-3.5 shadow-2xs space-y-1">
                <span className="font-mono text-[10px] font-bold text-black block uppercase">Phase 03</span>
                <h4 className="font-bold text-black text-xs">IDRiD Lesion Masks</h4>
                <p className="text-[11px] text-neutral-500 leading-snug">
                  Microaneurysms, hemorrhages, and hard exudate overlays.
                </p>
              </div>
              <div className="rounded-xl border border-neutral-200 bg-white p-3.5 shadow-2xs space-y-1">
                <span className="font-mono text-[10px] font-bold text-black block uppercase">Phase 04</span>
                <h4 className="font-bold text-black text-xs">Vector PDF Dossier</h4>
                <p className="text-[11px] text-neutral-500 leading-snug">
                  Instant clinical sign-off report with referral triage window.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. VISUAL EXPLAINABILITY: HOW THE AI SEES YOUR EYE           */}
      {/* ============================================================ */}
      <section id="how-it-works-visual" className="w-full bg-white py-20 lg:py-28 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-16">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-900">
              Explainable AI Vision &bull; Continuous Step-by-Step Scroll
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-black tracking-tight">
              How the AI Analyzes Your Retina
            </h2>
            <p className="text-neutral-600 text-sm sm:text-base leading-relaxed">
              Ever wonder how an AI model spots diabetic disease inside the eye?
              As you scroll down, discover our complete diagnostic pipeline broken down in plain English &mdash;
              from clearing camera fog and mapping blood vessel highways to pinpointing microscopic leaks and defending central vision.
            </p>
          </div>

          {/* Continuous Step-by-Step Vertical Inspection Flow */}
          <div className="space-y-12">
            {/* ---------------------------------------------------- */}
            {/* STAGE 01: HUE & CONTRAST (CLAHE)                     */}
            {/* ---------------------------------------------------- */}
            <div className="rounded-3xl border border-neutral-200 bg-[#fbfcfd] p-6 sm:p-8 lg:p-10 shadow-xs space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 pb-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center space-x-2 rounded-full bg-neutral-100 border border-neutral-300 px-3 py-1 text-[11px] font-mono font-bold text-black">
                    <Sliders className="h-3.5 w-3.5 text-black" />
                    <span>STEP 01 OF 05 &bull; PRE-PROCESSING &bull; LATENCY: 82MS</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-black">
                    1. Clearing Camera Fog: Hue &amp; Contrast Balancing
                  </h3>
                </div>

                {/* Interactive Mode Switcher for Stage 1 */}
                <div className="inline-flex items-center rounded-xl bg-neutral-100 p-1 border border-neutral-200 text-xs font-semibold text-neutral-700">
                  <button
                    type="button"
                    onClick={() => setContrastViewMode("split")}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      contrastViewMode === "split"
                        ? "bg-black text-white shadow-xs font-bold"
                        : "hover:text-black"
                    }`}
                  >
                    Split Comparison
                  </button>
                  <button
                    type="button"
                    onClick={() => setContrastViewMode("raw")}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      contrastViewMode === "raw"
                        ? "bg-black text-white shadow-xs font-bold"
                        : "hover:text-black"
                    }`}
                  >
                    Raw Flash (Dim)
                  </button>
                  <button
                    type="button"
                    onClick={() => setContrastViewMode("enhanced")}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      contrastViewMode === "enhanced"
                        ? "bg-black text-white shadow-xs font-bold"
                        : "hover:text-black"
                    }`}
                  >
                    CLAHE Enhanced
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Image Showcase */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="relative aspect-square sm:aspect-[4/3] w-full overflow-hidden rounded-2xl bg-black border border-neutral-800 shadow-xl">
                    {contrastViewMode === "split" && (
                      <div className="grid grid-cols-2 h-full w-full relative">
                        <div className="relative h-full w-full border-r border-neutral-700 overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src="/visual_inspection/original.png"
                            alt="Raw fundus before CLAHE"
                            className="h-full w-full object-cover"
                          />
                          <div className="absolute top-3 left-3 rounded-md bg-black/85 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs border border-white/10">
                            Raw Capture &bull; Dim &amp; Muddy
                          </div>
                        </div>
                        <div className="relative h-full w-full overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src="/visual_inspection/enhanced.png"
                            alt="Enhanced fundus after CLAHE"
                            className="h-full w-full object-cover"
                          />
                          <div className="absolute top-3 right-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                            CLAHE Enhanced &bull; Shadows Lifted
                          </div>
                        </div>
                        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center justify-center pointer-events-none">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-black border border-neutral-600 text-white shadow-lg">
                            <Split className="h-3.5 w-3.5 text-white" />
                          </div>
                        </div>
                      </div>
                    )}

                    {contrastViewMode === "raw" && (
                      <div className="relative h-full w-full">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src="/visual_inspection/original.png"
                          alt="Raw fundus unprocessed"
                          className="h-full w-full object-contain bg-black"
                        />
                        <div className="absolute top-3 left-3 rounded-md bg-black/85 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs border border-white/10">
                          Unprocessed 45° Posterior Pole Fundus
                        </div>
                      </div>
                    )}

                    {contrastViewMode === "enhanced" && (
                      <div className="relative h-full w-full">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src="/visual_inspection/enhanced.png"
                          alt="CLAHE Enhanced Fundus"
                          className="h-full w-full object-contain bg-black"
                        />
                        <div className="absolute top-3 left-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                          Contrast-Limited Adaptive Histogram Balanced
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-xs text-neutral-500 font-mono gap-2 px-1">
                    <span className="text-black font-semibold">Local Contrast Gain: +64%</span>
                    <span>Signal-to-Noise: +6.8 dB (Pass SNR &ge; 50 dB)</span>
                    <span>Tile Grid: 8&times;8</span>
                  </div>
                </div>

                {/* Layman Terms Explanation */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                      Plain-English Breakdown
                    </span>
                    <h4 className="text-xl font-extrabold text-black tracking-tight leading-snug">
                      Turning dim clinic scans into high-contrast diagnostic maps.
                    </h4>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Sun className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Like Smart Fog Lights</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Cuts through cataract haze and poor clinic flash without blinding glare.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Sliders className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">8&times;8 Local Grid Equalization</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Lifts pitch-black shadow corners while protecting bright retinal tissue.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Eye className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Exposes Hidden Micro-Bleeds</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Tiny bleeding dots smaller than a pencil tip pop out immediately for the doctor.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">+64%</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Shadow Lift</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">+6.8 dB</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">SNR Gain</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">82ms</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Latency</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Downward Scroll Connector 1 -> 2 */}
            <div className="flex flex-col items-center justify-center py-2 space-y-1">
              <div className="h-8 w-0.5 bg-neutral-300 rounded-full" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                Scroll Down &bull; Next Layer: Vascular Tree
              </span>
              <ArrowDown className="h-4 w-4 text-black" />
            </div>

            {/* ---------------------------------------------------- */}
            {/* STAGE 02: BLOOD VESSELS (GREEN BAND EXTRACTION)      */}
            {/* ---------------------------------------------------- */}
            <div className="rounded-3xl border border-neutral-200 bg-[#fbfcfd] p-6 sm:p-8 lg:p-10 shadow-xs space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 pb-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center space-x-2 rounded-full bg-neutral-100 border border-neutral-300 px-3 py-1 text-[11px] font-mono font-bold text-black">
                    <Scan className="h-3.5 w-3.5 text-black" />
                    <span>STEP 02 OF 05 &bull; VASCULAR RECONSTRUCTION &bull; GREEN CHANNEL</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-black">
                    2. Mapping the Eye&apos;s Plumbing Highway
                  </h3>
                </div>

                {/* Interactive Mode Switcher for Stage 2 */}
                <div className="inline-flex items-center rounded-xl bg-neutral-100 p-1 border border-neutral-200 text-xs font-semibold text-neutral-700">
                  <button
                    type="button"
                    onClick={() => setVesselViewMode("map")}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      vesselViewMode === "map"
                        ? "bg-black text-white shadow-xs font-bold"
                        : "hover:text-black"
                    }`}
                  >
                    Isolated Vascular Tree
                  </button>
                  <button
                    type="button"
                    onClick={() => setVesselViewMode("overlay")}
                    className={`rounded-lg px-3 py-1.5 transition ${
                      vesselViewMode === "overlay"
                        ? "bg-black text-white shadow-xs font-bold"
                        : "hover:text-black"
                    }`}
                  >
                    Vessels &amp; Fundus Dual View
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Image Showcase */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="relative aspect-square sm:aspect-[4/3] w-full overflow-hidden rounded-2xl bg-black border border-neutral-800 shadow-xl">
                    {vesselViewMode === "map" ? (
                      <div className="relative h-full w-full">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src="/visual_inspection/vessels.png"
                          alt="Isolated retinal blood vessels"
                          className="h-full w-full object-contain bg-black"
                        />
                        <div className="absolute top-3 left-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                          Green-Spectrum Vascular Tree (10&ndash;18&mu;m Caliber)
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 h-full w-full relative">
                        <div className="relative h-full w-full border-r border-neutral-700 overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src="/visual_inspection/enhanced.png"
                            alt="Fundus image"
                            className="h-full w-full object-cover"
                          />
                          <div className="absolute top-3 left-3 rounded-md bg-black/85 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs border border-white/10">
                            Enhanced Fundus Field
                          </div>
                        </div>
                        <div className="relative h-full w-full overflow-hidden">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src="/visual_inspection/vessels.png"
                            alt="Segmented vessels"
                            className="h-full w-full object-cover bg-black"
                          />
                          <div className="absolute top-3 right-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                            Vascular Segmentation
                          </div>
                        </div>
                        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center justify-center pointer-events-none">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-black border border-neutral-600 text-white shadow-lg">
                            <Scan className="h-3.5 w-3.5 text-white" />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-xs text-neutral-500 font-mono gap-2 px-1">
                    <span className="text-black font-semibold">Micro-Capillary Caliber: 10&ndash;18&mu;m</span>
                    <span>Spectral Band: 540&ndash;570nm Green</span>
                    <span>Coverage: 14.8% Area</span>
                  </div>
                </div>

                {/* Layman Terms Explanation */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                      Plain-English Breakdown
                    </span>
                    <h4 className="text-xl font-extrabold text-black tracking-tight leading-snug">
                      Tracing the eye&apos;s plumbing to spot pressure damage early.
                    </h4>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Droplets className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Like Aging Water Pipes</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          High blood sugar acts like rust and high water pressure, causing pipes to bulge and leak.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Scan className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">The Green Spectrum Trick</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Red blood absorbs green light; AI wipes away background to trace vessels down to 10&mu;m.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <ShieldCheck className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Catches Silent Damage</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Detects narrowed arteries and pinched crossings years before vision blurs.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">10&ndash;18&mu;m</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Caliber</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">560nm</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Green Band</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">14.8%</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Vascular Area</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Downward Scroll Connector 2 -> 3 */}
            <div className="flex flex-col items-center justify-center py-2 space-y-1">
              <div className="h-8 w-0.5 bg-neutral-300 rounded-full" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                Scroll Down &bull; Next Layer: Microscopic Lesions
              </span>
              <ArrowDown className="h-4 w-4 text-black" />
            </div>

            {/* ---------------------------------------------------- */}
            {/* STAGE 03: LESIONS (DUAL IDRiD U-NET MASKS)           */}
            {/* ---------------------------------------------------- */}
            <div className="rounded-3xl border border-neutral-200 bg-[#fbfcfd] p-6 sm:p-8 lg:p-10 shadow-xs space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 pb-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center space-x-2 rounded-full bg-neutral-100 border border-neutral-300 px-3 py-1 text-[11px] font-mono font-bold text-black">
                    <Crosshair className="h-3.5 w-3.5 text-black" />
                    <span>STEP 03 OF 05 &bull; DUAL U-NET LESION DECISION &bull; IDRiD GROUND TRUTH</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-black">
                    3. Spotting Pinhole Leaks &amp; Warning Stains
                  </h3>
                </div>

                {/* Interactive Lesion Filter Chips */}
                <div className="flex flex-wrap items-center gap-1.5 text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => setActiveLesionFilter("all")}
                    className={`rounded-lg px-3 py-1.5 transition border ${
                      activeLesionFilter === "all"
                        ? "bg-black text-white border-black shadow-xs font-bold"
                        : "bg-white text-neutral-700 border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    All Detected Lesions
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveLesionFilter("hems")}
                    className={`rounded-lg px-3 py-1.5 transition border ${
                      activeLesionFilter === "hems"
                        ? "bg-black text-white border-black shadow-xs font-bold"
                        : "bg-white text-neutral-800 border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    🔴 Red Bleeds
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveLesionFilter("exudates")}
                    className={`rounded-lg px-3 py-1.5 transition border ${
                      activeLesionFilter === "exudates"
                        ? "bg-black text-white border-black shadow-xs font-bold"
                        : "bg-white text-neutral-800 border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    🟡 Yellow Fat Pools
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveLesionFilter("cws")}
                    className={`rounded-lg px-3 py-1.5 transition border ${
                      activeLesionFilter === "cws"
                        ? "bg-black text-white border-black shadow-xs font-bold"
                        : "bg-white text-neutral-800 border-neutral-300 hover:bg-neutral-50"
                    }`}
                  >
                    ⚪ White Nerve Strokes
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Image Showcase */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="relative aspect-square sm:aspect-[4/3] w-full overflow-hidden rounded-2xl bg-black border border-neutral-800 shadow-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/visual_inspection/overlay.png"
                      alt="Segmented diabetic lesions overlay"
                      className="h-full w-full object-contain bg-black"
                    />
                    <div className="absolute top-3 left-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                      Dual U-Net Lesion Overlay &bull; Pixel-Level Multi-Class
                    </div>

                    {/* Active Filter Callout Badge */}
                    <div className="absolute bottom-3 left-3 right-3 rounded-xl bg-black/85 border border-white/15 p-2.5 backdrop-blur-md text-xs">
                      {activeLesionFilter === "all" && (
                        <span className="text-neutral-200 font-mono text-[11px]">
                          <strong className="text-white">Clinical Summary:</strong> Multi-class pixel masks segmented across 262,144 grid cells.
                        </span>
                      )}
                      {activeLesionFilter === "hems" && (
                        <span className="text-neutral-200 font-mono text-[11px]">
                          <strong className="text-white">🔴 Hemorrhages:</strong> Micro-bleeding points detected where delicate capillary walls ruptured.
                        </span>
                      )}
                      {activeLesionFilter === "exudates" && (
                        <span className="text-neutral-200 font-mono text-[11px]">
                          <strong className="text-white">🟡 Hard Exudates:</strong> Waxy lipid pools left behind by leaking plasma fluid.
                        </span>
                      )}
                      {activeLesionFilter === "cws" && (
                        <span className="text-neutral-200 font-mono text-[11px]">
                          <strong className="text-white">⚪ Cotton Wool Spots:</strong> Ischemic nerve fiber swelling starved of oxygen blood flow.
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-xs text-neutral-500 font-mono gap-2 px-1">
                    <span className="text-black font-semibold">IDRiD Exudate Dice: 0.7580</span>
                    <span>False Negative Rate: &lt; 3.2%</span>
                    <span>Pixel Audit Trail: 512&times;512 Grid</span>
                  </div>
                </div>

                {/* Layman Terms Explanation */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                      Plain-English Breakdown
                    </span>
                    <h4 className="text-xl font-extrabold text-black tracking-tight leading-snug">
                      Dual neural networks circle every leak and waxy deposit.
                    </h4>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <AlertTriangle className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Like Ceiling Water Leaks</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Starts with damp bleeds, forms waxy lipid stains, and ends in rotting nerve death.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Crosshair className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Dual U-Net Decoders</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Classifies 262,144 pixels to map exact micro-bleeds and plasma fat pools.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <HeartPulse className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Finds Silent Blindness</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Patients have 20/20 vision and zero pain while lesions multiply; AI provides physical proof.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">0.7580</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Exudate Dice</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">&lt; 3.2%</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">False Neg</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">IDRiD</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Benchmark</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Downward Scroll Connector 3 -> 4 */}
            <div className="flex flex-col items-center justify-center py-2 space-y-1">
              <div className="h-8 w-0.5 bg-neutral-300 rounded-full" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                Scroll Down &bull; Next Layer: Central Vision Radar
              </span>
              <ArrowDown className="h-4 w-4 text-black" />
            </div>

            {/* ---------------------------------------------------- */}
            {/* STAGE 04: MACULA & CSME DANGER ZONE                  */}
            {/* ---------------------------------------------------- */}
            <div className="rounded-3xl border border-neutral-200 bg-[#fbfcfd] p-6 sm:p-8 lg:p-10 shadow-xs space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 pb-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center space-x-2 rounded-full bg-neutral-100 border border-neutral-300 px-3 py-1 text-[11px] font-mono font-bold text-black">
                    <Target className="h-3.5 w-3.5 text-black" />
                    <span>STEP 04 OF 05 &bull; MACULA RADAR &bull; CLINICALLY SIGNIFICANT MACULAR EDEMA</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-black">
                    4. Defending Your Reading Bullseye (CSME Threat Zone)
                  </h3>
                </div>

                <div className="rounded-lg bg-neutral-100 border border-neutral-300 px-3 py-1 text-xs font-bold text-black">
                  Critical Sight Alert Zone
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Image Showcase */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="relative aspect-square sm:aspect-[4/3] w-full overflow-hidden rounded-2xl bg-black border border-neutral-800 shadow-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/visual_inspection/evidence_overlay.png"
                      alt="Optic Disc and Macular CSME threat zone overlay"
                      className="h-full w-full object-contain bg-black"
                    />
                    <div className="absolute top-3 left-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                      Optic Disc Boundary &bull; 1-Disc-Diameter Safety Perimeter
                    </div>
                    <div className="absolute top-3 right-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                      CSME Incursion Detection
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-xs text-neutral-500 font-mono gap-2 px-1">
                    <span className="text-black font-semibold">Optic Disc Dice: 0.9859</span>
                    <span>Disc-to-Fovea: 2.5 Disc Diameters (~4.5mm)</span>
                    <span className="text-black font-bold">1-DD CSME Radar</span>
                  </div>
                </div>

                {/* Layman Terms Explanation */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                      Plain-English Breakdown
                    </span>
                    <h4 className="text-xl font-extrabold text-black tracking-tight leading-snug">
                      Drawing a safety perimeter around your reading bullseye.
                    </h4>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Target className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">The Reading Bullseye</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          The center macula gives 90% of sharp vision &mdash; reading phones, driving, and seeing faces.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <BrainCircuit className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">1-Disc-Diameter Radar</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          AI measures 2.5 diameters from optic disc, projecting a ~1.5mm protective cordon.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-300 bg-neutral-100/80 p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-black text-white flex items-center justify-center shrink-0 mt-0.5">
                        <AlertOctagon className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Urgent CSME Alert</h5>
                        <p className="text-[11px] text-neutral-700 leading-normal">
                          Fluid touching this ring causes sudden legal blindness; triggers urgent 7&ndash;14 day referral.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">0.9859</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Disc Dice</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">1-DD</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Safety Zone</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">Level 1</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Priority</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Downward Scroll Connector 4 -> 5 */}
            <div className="flex flex-col items-center justify-center py-2 space-y-1">
              <div className="h-8 w-0.5 bg-neutral-300 rounded-full" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-400">
                Scroll Down &bull; Final Layer: Inside the AI Brain
              </span>
              <ArrowDown className="h-4 w-4 text-black" />
            </div>

            {/* ---------------------------------------------------- */}
            {/* STAGE 05: GRAD-CAM (NEURAL ATTENTION HEATMAP)        */}
            {/* ---------------------------------------------------- */}
            <div className="rounded-3xl border border-neutral-200 bg-[#fbfcfd] p-6 sm:p-8 lg:p-10 shadow-xs space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-200 pb-4">
                <div className="space-y-1">
                  <div className="inline-flex items-center space-x-2 rounded-full bg-neutral-100 border border-neutral-300 px-3 py-1 text-[11px] font-mono font-bold text-black">
                    <Flame className="h-3.5 w-3.5 text-black" />
                    <span>STEP 05 OF 05 &bull; EXPLAINABLE AI (XAI) &bull; TRUST AUDITING</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-black">
                    5. Seeing What the AI Brain Focuses On (Grad-CAM)
                  </h3>
                </div>

                <div className="rounded-lg bg-neutral-100 border border-neutral-300 px-3 py-1 text-xs font-bold text-black">
                  Zero Black-Box Guesswork
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                {/* Image Showcase */}
                <div className="lg:col-span-7 space-y-3">
                  <div className="relative aspect-square sm:aspect-[4/3] w-full overflow-hidden rounded-2xl bg-black border border-neutral-800 shadow-xl">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/visual_inspection/gradcam.png"
                      alt="Grad-CAM activation heatmap"
                      className="h-full w-full object-contain bg-black"
                    />
                    <div className="absolute top-3 left-3 rounded-md bg-black/90 border border-white/20 px-2.5 py-1 text-[10px] font-mono font-bold text-white backdrop-blur-xs">
                      Grad-CAM Class Activation Map (Conv_5x Layer)
                    </div>

                    {/* Thermal Scale Indicator */}
                    <div className="absolute bottom-3 left-3 right-3 rounded-xl bg-black/85 border border-white/15 p-2.5 backdrop-blur-md text-xs">
                      <div className="flex items-center justify-between text-[10px] font-mono text-neutral-300 mb-1">
                        <span>Low Weight (Normal Tissue)</span>
                        <span className="text-white font-bold">Clinical Focus (Pathology)</span>
                        <span className="text-white font-bold">Max Weight (Lesions)</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-gradient-to-r from-blue-600 via-emerald-400 via-amber-400 to-red-600" />
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-xs text-neutral-500 font-mono gap-2 px-1">
                    <span className="text-black font-semibold">Backprop Target: ResNet-34 Conv5x</span>
                    <span>Clinical Concordance: 94.2%</span>
                    <span>Artifact Dependency: 0%</span>
                  </div>
                </div>

                {/* Layman Terms Explanation */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-neutral-500">
                      Plain-English Breakdown
                    </span>
                    <h4 className="text-xl font-extrabold text-black tracking-tight leading-snug">
                      Thermal heat signature proving why the AI made its diagnosis.
                    </h4>
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <Flame className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Surgeon&apos;s Pointer Finger</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Shows the exact pixels that convinced the AI, eliminating black-box mystery.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <BrainCircuit className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Gradient Attention</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Neural backpropagation glows fiery red over actual medical lesions.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3 rounded-2xl border border-neutral-200 bg-white p-3.5 shadow-2xs">
                      <div className="h-7 w-7 rounded-lg bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center shrink-0 mt-0.5">
                        <ShieldCheck className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <h5 className="text-xs font-bold text-black">Kills False Alarms</h5>
                        <p className="text-[11px] text-neutral-600 leading-normal">
                          Verifies AI ignores dust, eyelashes, and glare, guaranteeing 100% clinician trust.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">94.2%</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Concordance</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">Conv_5x</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Backprop Layer</div>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-white p-2.5 text-center">
                      <div className="text-xs font-extrabold text-black">0%</div>
                      <div className="text-[10px] text-neutral-500 uppercase font-mono">Artifact Bias</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section Conclusion & Next Action */}
          <div className="rounded-3xl bg-black p-8 sm:p-10 text-white text-center space-y-6 border border-neutral-800">
            <div className="max-w-3xl mx-auto space-y-3">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">
                End-to-End Autonomous Pipeline &bull; Offline Edge Execution
              </span>
              <h3 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight">
                5 Stages. Under 2.5 Seconds. 100% Offline.
              </h3>
              <p className="text-neutral-400 text-sm sm:text-base leading-relaxed">
                From image intake to final clinical dossier, the entire pipeline executes on local edge hardware without transmitting sensitive patient fundus data across the internet.
              </p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <button
                type="button"
                onClick={() => onLaunchWorkstation()}
                className="inline-flex items-center space-x-2 rounded-xl bg-white px-6 py-3.5 text-xs sm:text-sm font-bold text-black shadow-sm transition hover:bg-neutral-200 active:scale-95"
              >
                <Activity className="h-4 w-4 text-black" />
                <span>Launch Interactive Workstation</span>
              </button>
              <a
                href="#cohort-cases"
                className="inline-flex items-center space-x-2 rounded-xl border border-neutral-700 bg-neutral-900 px-6 py-3.5 text-xs sm:text-sm font-bold text-neutral-300 shadow-sm transition hover:bg-neutral-800 hover:text-white"
              >
                <span>Test Live Sample Cases Below</span>
                <ArrowDown className="h-4 w-4 text-neutral-300" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 6. CLINICAL CASE TEST DRIVE: REAL SAMPLES FROM LOCAL COHORT  */}
      {/* ============================================================ */}
      <section id="cohort-cases" className="w-full bg-white py-20 lg:py-28 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-3 max-w-2xl">
              <span className="text-xs font-bold uppercase tracking-wider text-neutral-900">
                Verified Clinical Cohort &bull; Grades 0–4
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
                One-Click Clinical Verification
              </h2>
              <p className="text-neutral-600 text-sm sm:text-base leading-relaxed">
                Test RetinaScan directly against benchmark cases representing each clinical severity grade.
                Clicking any case loads the fundus image into the active workspace for real-time model execution.
              </p>
            </div>

            <button
              type="button"
              onClick={() => onNavigateTab("cohort")}
              className="inline-flex items-center space-x-2 rounded-xl border border-neutral-200 bg-white px-4 py-2.5 text-xs font-bold text-neutral-900 hover:bg-neutral-50 transition shadow-2xs shrink-0"
            >
              <span>View All Cohort Cases</span>
              <ChevronRight className="h-3.5 w-3.5 text-neutral-400" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {CLINICAL_SAMPLE_CASES.slice(0, 4).map((sample) => {
              const isLoading = loadingCaseId === sample.id;
              return (
                <div
                  key={sample.id}
                  className="group relative flex flex-col justify-between rounded-2xl border border-neutral-200 bg-[#fbfcfd] p-5 shadow-xs transition duration-200 hover:-translate-y-1 hover:border-black hover:shadow-lg hover:bg-white"
                >
                  <div className="space-y-4">
                    <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-black flex items-center justify-center border border-neutral-200">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={sample.imagePath}
                        alt={sample.title}
                        className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                        loading="lazy"
                      />
                      <div className="absolute top-2 left-2 rounded-md bg-black/80 px-2 py-1 text-[10px] font-bold text-white backdrop-blur-xs font-mono">
                        {sample.grade}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <h3 className="text-base font-bold text-black group-hover:text-black transition">
                        {sample.title}
                      </h3>
                      <p className="text-xs text-neutral-500 line-clamp-2 leading-relaxed">
                        {sample.pathology}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 mt-4 border-t border-neutral-200 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-neutral-500">
                      {sample.expectedTriage}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleLaunchCase(sample)}
                      disabled={isLoading}
                      className="inline-flex items-center space-x-1.5 rounded-lg bg-black px-3 py-1.5 text-xs font-bold text-white shadow-2xs transition hover:bg-neutral-800 active:scale-95 disabled:opacity-50"
                    >
                      {isLoading ? (
                        <span>Loading...</span>
                      ) : (
                        <>
                          <span>Grade Case</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 4. TECHNICAL RIGOR: MATHWORKS PS 26038 ARCHITECTURE          */}
      {/* ============================================================ */}
      <section className="w-full bg-[#fafafa] py-20 lg:py-28 border-b border-neutral-200">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-neutral-900">
              Computational Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-black tracking-tight">
              Engineered for Offline Health Centres
            </h2>
            <p className="text-neutral-600 text-sm sm:text-base">
              Zero cloud telemetry required. Model pipelines run fully on local edge hardware with
              sub-2.5 second inference, safeguarding patient privacy under strict medical data standards.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-xs space-y-3">
              <div className="h-10 w-10 rounded-xl bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center">
                <Layers className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-black">Dual IDRiD U-Net Decoders</h3>
              <p className="text-xs text-neutral-600 leading-relaxed">
                Trained on the Indian Diabetic Retinopathy Image Dataset (IDRiD) to segment fine
                microaneurysms and subtle soft exudate margins where single-stage classifiers routinely fail.
              </p>
            </div>

            <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-xs space-y-3">
              <div className="h-10 w-10 rounded-xl bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center">
                <Cpu className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-black">Edge Quantization &amp; Privacy</h3>
              <p className="text-xs text-neutral-600 leading-relaxed">
                Inference executes in-memory via PyTorch CPU/Metal backends. No patient fundus imagery
                or metadata ever leaves the screening clinic, ensuring complete patient data sovereignty.
              </p>
            </div>

            <div className="rounded-2xl border border-neutral-200 bg-white p-6 shadow-xs space-y-3">
              <div className="h-10 w-10 rounded-xl bg-neutral-100 text-black border border-neutral-200 flex items-center justify-center">
                <FileCheck className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-black">FHIR &amp; DICOM-Ready Triage</h3>
              <p className="text-xs text-neutral-600 leading-relaxed">
                Auto-generates structured diagnostic dossiers with calibrated referral windows, CSME
                proximity markers, and verifiable clinician sign-off fields for tele-consultation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 5. CALL TO ACTION                                            */}
      {/* ============================================================ */}
      <section className="w-full bg-white py-20 lg:py-24 border-b border-neutral-200">
        <div className="mx-auto max-w-4xl px-6 sm:px-8 text-center space-y-6">
          <h2 className="text-3xl sm:text-5xl font-extrabold text-black tracking-tight leading-tight">
            Ready to Begin Screening?
          </h2>
          <p className="text-base sm:text-lg text-neutral-600 max-w-2xl mx-auto leading-relaxed">
            Upload patient fundus photographs or explore our pre-loaded clinical cohort directly in
            the interactive diagnostic workstation.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              type="button"
              onClick={() => onLaunchWorkstation()}
              className="inline-flex items-center space-x-2 rounded-xl bg-black px-8 py-4 text-sm font-bold text-white shadow-xs transition hover:bg-neutral-800 active:scale-95"
            >
              <Activity className="h-4 w-4 text-white" />
              <span>Launch Diagnostic Workstation</span>
            </button>

            <button
              type="button"
              onClick={() => onNavigateTab("benchmarks")}
              className="inline-flex items-center space-x-2 rounded-xl border border-neutral-300 bg-white px-7 py-4 text-sm font-bold text-black shadow-2xs transition hover:bg-neutral-100"
            >
              <BarChart3 className="h-4 w-4 text-black" />
              <span>Inspect Validation Benchmarks</span>
            </button>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/* 6. CLEAN, REFINED FOOTER                                     */}
      {/* ============================================================ */}
      <footer className="w-full bg-[#fbfcfd] py-12 text-xs text-neutral-500">
        <div className="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-black text-white">
              <Eye className="h-4 w-4 stroke-[2.2]" />
            </div>
            <span className="font-bold text-black">
              RetinaScan<span className="text-neutral-500 font-bold">AI</span>
            </span>
            <span className="text-neutral-400">&bull;</span>
            <span>Smart India Hackathon 2026 PS 26038</span>
          </div>

          <div className="flex items-center space-x-6">
            <button
              type="button"
              onClick={() => onLaunchWorkstation()}
              className="hover:text-black transition"
            >
              Workstation
            </button>
            <button
              type="button"
              onClick={() => onNavigateTab("cohort")}
              className="hover:text-black transition"
            >
              Cohort Library
            </button>
            <button
              type="button"
              onClick={() => onNavigateTab("benchmarks")}
              className="hover:text-black transition"
            >
              Model Benchmarks
            </button>
          </div>
        </div>
      </footer>

      {/* Scroll to Top Floating Button */}
      {showScrollTop && (
        <button
          type="button"
          onClick={scrollToTop}
          aria-label="Scroll to top"
          className="fixed bottom-6 right-6 z-50 flex h-10 w-10 items-center justify-center rounded-full border border-neutral-300 bg-white text-neutral-800 shadow-md hover:bg-neutral-100 transition active:scale-95"
        >
          <ChevronUp className="h-5 w-5" />
        </button>
      )}
    </div>
  );
};
