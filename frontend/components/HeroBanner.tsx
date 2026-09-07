"use client";

import React from "react";
import {
  ShieldCheck,
  Activity,
  Users,
  Compass,
  Cpu,
  Layers,
  ChevronRight,
  Sparkles,
} from "lucide-react";

export const HeroBanner: React.FC = () => {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-stone-800 bg-[#0c1222] text-white shadow-xl">
      {/* Background Subtle Medical Grid Pattern */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `radial-gradient(#ffffff 1px, transparent 1px)`,
          backgroundSize: "24px 24px",
        }}
      />

      <div className="relative z-10 px-6 py-8 sm:px-8 sm:py-10">
        {/* Top Badges */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-800/80 pb-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center space-x-1.5 rounded-full border border-emerald-500/30 bg-emerald-950/60 px-3 py-1 text-xs font-semibold text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>SIH 2026 &bull; PS 26038</span>
            </span>
            <span className="rounded-full border border-stone-700 bg-stone-800/80 px-3 py-1 text-xs font-medium text-stone-300">
              MathWorks &bull; HealthTech / MedTech
            </span>
            <span className="rounded-full border border-sky-500/30 bg-sky-950/60 px-3 py-1 text-xs font-medium text-sky-300">
              Rural Tele-Ophthalmology Workstation
            </span>
          </div>

          <div className="flex items-center space-x-2 font-mono text-xs text-stone-400">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
            <span>IDRiD Deep Models Online</span>
          </div>
        </div>

        {/* Main Banner Heading & Clinical Mission */}
        <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-12 lg:items-center">
          <div className="space-y-4 lg:col-span-7">
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl lg:text-4xl">
              Explainable AI for Diabetic Retinopathy Screening in Rural India
            </h1>
            <p className="text-sm leading-relaxed text-stone-300 sm:text-base">
              Autonomous clinical decision support deployed for Primary Health Centres (PHCs).
              Combines automated optical quality gating, dual IDRiD ResNet34 lesion segmenters,
              and calibrated 5-class severity grading to safeguard preventable vision loss in underserved populations.
            </p>

            {/* Architecture Pipeline Pills */}
            <div className="pt-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-stone-400">
                Four-Stage Screening Pipeline
              </span>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                <div className="flex items-center space-x-1.5 rounded-lg border border-stone-700/80 bg-stone-900/90 px-3 py-1.5 text-stone-200">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                  <span>1. IQA Gatekeeper</span>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-stone-600 hidden sm:inline" />
                <div className="flex items-center space-x-1.5 rounded-lg border border-stone-700/80 bg-stone-900/90 px-3 py-1.5 text-stone-200">
                  <Layers className="h-3.5 w-3.5 text-amber-400" />
                  <span>2. IDRiD Lesions (UNet)</span>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-stone-600 hidden sm:inline" />
                <div className="flex items-center space-x-1.5 rounded-lg border border-stone-700/80 bg-stone-900/90 px-3 py-1.5 text-stone-200">
                  <Cpu className="h-3.5 w-3.5 text-sky-400" />
                  <span>3. EfficientNetB3 (ICDR 0-4)</span>
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-stone-600 hidden sm:inline" />
                <div className="flex items-center space-x-1.5 rounded-lg border border-stone-700/80 bg-stone-900/90 px-3 py-1.5 text-stone-200">
                  <Activity className="h-3.5 w-3.5 text-rose-400" />
                  <span>4. CSME & Triage</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Quantitative Telemetry Cards */}
          <div className="grid grid-cols-2 gap-3 lg:col-span-5">
            <div className="rounded-2xl border border-stone-800 bg-stone-900/70 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-stone-400 uppercase tracking-wider">
                  Target Cohort
                </span>
                <Users className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                77.2M
              </div>
              <p className="mt-1 text-[11px] text-stone-400">
                Adults living with diabetes across India requiring screening
              </p>
            </div>

            <div className="rounded-2xl border border-stone-800 bg-stone-900/70 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-stone-400 uppercase tracking-wider">
                  Specialist Ratio
                </span>
                <Compass className="h-4 w-4 text-amber-400" />
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                1 : 100k
              </div>
              <p className="mt-1 text-[11px] text-stone-400">
                Severe rural retina specialist deficit requiring PHC triage
              </p>
            </div>

            <div className="rounded-2xl border border-stone-800 bg-stone-900/70 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-stone-400 uppercase tracking-wider">
                  Optic Disc Dice
                </span>
                <Layers className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                0.9859
              </div>
              <p className="mt-1 text-[11px] text-stone-400">
                IDRiD ResNet34 UNet landmark localization benchmark
              </p>
            </div>

            <div className="rounded-2xl border border-stone-800 bg-stone-900/70 p-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-stone-400 uppercase tracking-wider">
                  Exudates Dice
                </span>
                <Activity className="h-4 w-4 text-orange-400" />
              </div>
              <div className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                0.7580
              </div>
              <p className="mt-1 text-[11px] text-stone-400">
                IDRiD ResNet34 UNet lesion segmentation benchmark
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
