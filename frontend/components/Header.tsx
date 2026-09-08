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
  systemVersion: _systemVersion,
  isBackendHealthy: _isBackendHealthy,
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
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-black text-white shadow-xs">
            <Eye className="h-5 w-5 stroke-[2.2]" aria-hidden="true" />
          </div>
          <div>
            <span className="text-base font-extrabold tracking-tight text-black">
              RetinaScan<span className="text-neutral-500 font-bold">AI</span>
            </span>
            <p className="text-[11px] font-medium text-neutral-500 hidden sm:block">
              Diabetic Retinopathy Screening
            </p>
          </div>
        </button>

        {/* Center: Main Product Navigation Tabs */}
        {onTabChange && (
          <nav className="flex items-center space-x-1 rounded-xl border border-neutral-200 bg-neutral-100 p-1 text-xs font-medium">
            <button
              type="button"
              onClick={() => onTabChange("landing")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "landing"
                  ? "bg-black font-bold text-white shadow-xs"
                  : "text-neutral-600 hover:text-black"
              }`}
            >
              <Home className={`h-3.5 w-3.5 ${activeTab === "landing" ? "text-white" : "text-neutral-500"}`} />
              <span>Overview</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("workstation")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "workstation"
                  ? "bg-black font-bold text-white shadow-xs"
                  : "text-neutral-600 hover:text-black"
              }`}
            >
              <Activity className={`h-3.5 w-3.5 ${activeTab === "workstation" ? "text-white" : "text-neutral-500"}`} />
              <span>Workstation</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("cohort")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "cohort"
                  ? "bg-black font-bold text-white shadow-xs"
                  : "text-neutral-600 hover:text-black"
              }`}
            >
              <FolderKanban className={`h-3.5 w-3.5 ${activeTab === "cohort" ? "text-white" : "text-neutral-500"}`} />
              <span>Patient Cohort</span>
            </button>
            <button
              type="button"
              onClick={() => onTabChange("benchmarks")}
              className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 transition ${
                activeTab === "benchmarks"
                  ? "bg-black font-bold text-white shadow-xs"
                  : "text-neutral-600 hover:text-black"
              }`}
            >
              <BarChart3 className={`h-3.5 w-3.5 ${activeTab === "benchmarks" ? "text-white" : "text-neutral-500"}`} />
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
        </div>
      </div>
    </header>
  );
};
