"use client";

import React from "react";
import {
  Eye,
  CheckCircle2,
  Printer,
  Layers,
  FolderKanban,
  BarChart3,
  Activity,
  Home,
} from "lucide-react";

export type AppTab = "landing" | "workstation" | "cohort" | "benchmarks";

export interface HeaderProps {
  systemVersion?: string;
  isBackendHealthy?: boolean;
  onPrint?: () => void;
  canPrint?: boolean;
  activeTab?: AppTab;
  onTabChange?: (tab: AppTab) => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemVersion = "v2.1 PACS",
  isBackendHealthy = true,
  onPrint,
  canPrint = false,
  activeTab = "workstation",
  onTabChange,
}) => {
  return (
    <header className="sticky top-0 z-40 border-b border-stone-200/90 bg-white/95 backdrop-blur-md shadow-2xs no-print">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
        {/* Brand & Title (clickable to home) */}
        <button
          type="button"
          onClick={() => onTabChange && onTabChange("landing")}
          className="flex items-center space-x-3 text-left focus:outline-hidden"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-emerald-400 shadow-xs">
            <Eye className="h-5 w-5 stroke-[2.2]" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-extrabold tracking-tight text-slate-950">
                RetinaGuard<span className="text-emerald-700">AI</span>
              </span>
              <span className="rounded-md border border-stone-200 bg-stone-100/80 px-1.5 py-0.2 font-mono text-[10px] font-semibold text-stone-600">
                {systemVersion}
              </span>
            </div>
            <p className="text-[11px] font-medium text-stone-500 hidden sm:block">
              Clinical Retinal Diagnostic & Lesion Workstation
            </p>
          </div>
        </button>

        {/* Center: Main Product Navigation Tabs */}
        {onTabChange && (
          <nav className="flex items-center space-x-1 rounded-xl border border-stone-200 bg-stone-100/80 p-1 text-xs font-medium">
            <button
              type="button"
              onClick={() => onTabChange("landing")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "landing"
                  ? "bg-white font-bold text-slate-900 shadow-2xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Home className="h-3.5 w-3.5 text-stone-700" />
              <span>Overview</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("workstation")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "workstation"
                  ? "bg-white font-bold text-slate-900 shadow-2xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Activity className="h-3.5 w-3.5 text-emerald-700" />
              <span>Workstation</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("cohort")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "cohort"
                  ? "bg-white font-bold text-slate-900 shadow-2xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <FolderKanban className="h-3.5 w-3.5 text-sky-700" />
              <span>Patient Cohort</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("benchmarks")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "benchmarks"
                  ? "bg-white font-bold text-slate-900 shadow-2xs"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5 text-amber-700" />
              <span>Validation & Models</span>
            </button>
          </nav>
        )}

        {/* Right Status & Actions */}
        <div className="flex items-center space-x-2.5">
          {canPrint && onPrint && (
            <button
              type="button"
              onClick={onPrint}
              aria-label="Print clinical summary report"
              className="inline-flex items-center space-x-1.5 rounded-lg border border-stone-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-stone-700 shadow-2xs transition hover:bg-stone-50 hover:text-stone-900"
            >
              <Printer className="h-3.5 w-3.5 text-stone-500" />
              <span className="hidden sm:inline">Export Report</span>
            </button>
          )}

          <div
            className="flex items-center space-x-1.5 rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs text-stone-600"
            role="status"
            aria-label="System status"
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isBackendHealthy ? "bg-emerald-600" : "bg-amber-500"
              }`}
            />
            <span className="font-mono text-[10px] font-bold uppercase text-stone-700">
              {isBackendHealthy ? "Engine 8000 Ready" : "Connecting"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
