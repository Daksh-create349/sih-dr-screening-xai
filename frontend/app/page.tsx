"use client";

import React, { useState, useEffect } from "react";
import { Header, AppTab } from "@/components/Header";
import { ProductLandingPage } from "@/components/ProductLandingPage";
import { ClinicalSampleSelector } from "@/components/ClinicalSampleSelector";
import { UploadCard } from "@/components/UploadCard";
import { FundusWorkspace } from "@/components/FundusWorkspace";
import { AnalysisPanel } from "@/components/AnalysisPanel";
import { SafetyNotice } from "@/components/SafetyNotice";
import { CohortLibraryView } from "@/components/CohortLibraryView";
import { BenchmarkView } from "@/components/BenchmarkView";
import { PrintableSummary } from "@/components/PrintableSummary";
import { ClinicalReportModal } from "@/components/ClinicalReportModal";
import {
  ScreeningResponse,
  ScreeningState,
  UploadedImageMeta,
} from "@/types/screening";
import { screenRetinalImage, getBackendHealth } from "@/lib/api";

export default function ScreeningPage() {
  const [activeTab, setActiveTab] = useState<AppTab>("landing");
  const [screeningState, setScreeningState] = useState<ScreeningState>("EMPTY");
  const [selectedImage, setSelectedImage] = useState<UploadedImageMeta | null>(
    null
  );
  const [screeningResult, setScreeningResult] =
    useState<ScreeningResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);

  useEffect(() => {
    // Check backend health on initial load
    getBackendHealth()
      .then(() => setIsBackendHealthy(true))
      .catch(() => setIsBackendHealthy(false));
  }, []);

  const handleImageSelected = (meta: UploadedImageMeta) => {
    setSelectedImage(meta);
    setScreeningResult(null);
    setErrorMessage(null);
    setScreeningState("READY_TO_ANALYZE");
  };

  const handleImageRemove = () => {
    if (selectedImage?.previewUrl) {
      URL.revokeObjectURL(selectedImage.previewUrl);
    }
    setSelectedImage(null);
    setScreeningResult(null);
    setErrorMessage(null);
    setScreeningState("EMPTY");
  };

  const handleUploadError = (message?: string) => {
    setErrorMessage(message || "Invalid image file uploaded.");
    setScreeningState("ERROR");
  };

  const handleAnalyze = async () => {
    if (!selectedImage) return;

    setScreeningState("ANALYZING");
    setErrorMessage(null);

    try {
      const result = await screenRetinalImage(selectedImage.file);
      setScreeningResult(result);
      setScreeningState("RESULT");
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Screening analysis failed.";
      setErrorMessage(msg);
      setScreeningState("ERROR");
    }
  };

  const handleLaunchWorkstation = (meta?: UploadedImageMeta) => {
    if (meta) {
      handleImageSelected(meta);
    }
    setActiveTab("workstation");
  };

  const handleLoadCaseFromCohort = (meta: UploadedImageMeta) => {
    handleImageSelected(meta);
    setActiveTab("workstation");
  };

  const handlePrint = () => {
    setIsReportModalOpen(true);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#fbfbf9] text-stone-900">
      {/* Product Global Header with Navigation Tabs (Shown in Workstation, Cohort, Benchmark views) */}
      {activeTab !== "landing" && (
        <Header
          isBackendHealthy={isBackendHealthy}
          onPrint={handlePrint}
          canPrint={screeningState === "RESULT" && screeningResult !== null}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
      )}

      <main
        className={
          activeTab === "landing"
            ? "w-full flex-1"
            : "mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8"
        }
      >
        {activeTab === "landing" && (
          <ProductLandingPage
            onLaunchWorkstation={handleLaunchWorkstation}
            onNavigateTab={setActiveTab}
          />
        )}

        {activeTab === "workstation" && (
          <div className="space-y-6">
            {/* Top Bar: Clinical Sample Selector for instant test-case switching */}
            <ClinicalSampleSelector
              onSelectSample={handleImageSelected}
              disabled={screeningState === "ANALYZING"}
              selectedFilename={selectedImage?.filename}
            />

            {/* 12-Column Responsive Clinical Workspace */}
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12 items-start">
              {/* Left Column: Fundus Image Inspection & Controls (5 cols) */}
              <div className="lg:col-span-5 space-y-6 lg:sticky lg:top-24">
                {!selectedImage ? (
                  <UploadCard
                    onImageSelected={handleImageSelected}
                    onError={handleUploadError}
                    disabled={screeningState === "ANALYZING"}
                  />
                ) : (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
                      <FundusWorkspace
                        imageMeta={selectedImage}
                        onRemove={handleImageRemove}
                        disabled={screeningState === "ANALYZING"}
                      />
                    </div>

                    <div className="flex items-center justify-between rounded-xl border border-stone-200 bg-white px-4 py-2.5 shadow-2xs">
                      <span className="text-xs text-stone-500">
                        Selected:{" "}
                        <strong className="text-stone-800">
                          {selectedImage.filename}
                        </strong>
                      </span>
                      <button
                        type="button"
                        onClick={handleImageRemove}
                        disabled={screeningState === "ANALYZING"}
                        className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-semibold text-stone-700 hover:bg-stone-100 transition disabled:opacity-50"
                      >
                        Change Image
                      </button>
                    </div>
                  </div>
                )}

                <SafetyNotice />
              </div>

              {/* Right Column: Order-wise Analysis & Results Workstation (7 cols) */}
              <div className="lg:col-span-7">
                <AnalysisPanel
                  state={screeningState}
                  result={screeningResult}
                  onAnalyze={handleAnalyze}
                  canAnalyze={screeningState === "READY_TO_ANALYZE"}
                  errorMessage={errorMessage}
                  onRetry={handleAnalyze}
                  onReset={handleImageRemove}
                  originalImageUrl={selectedImage?.previewUrl}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === "cohort" && (
          <CohortLibraryView
            onLoadCase={handleLoadCaseFromCohort}
            disabled={screeningState === "ANALYZING"}
          />
        )}

        {activeTab === "benchmarks" && <BenchmarkView />}
      </main>

      {/* Printable Clinical Report (Hidden on screen, active on @media print) */}
      {screeningResult && (
        <PrintableSummary
          result={screeningResult}
          patientId="#RUR-2026-084"
          doctorName="Dr. [Physician Name]"
          institution="SIH National Telemedicine DR Screening Network"
        />
      )}

      {/* Clinical PDF Report Modal with Direct Vector Download & Print Preview */}
      {isReportModalOpen && screeningResult && (
        <ClinicalReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          screeningResult={screeningResult}
          studyFilename={selectedImage?.filename || "retina_scan.png"}
          patientId="#RUR-2026-084"
          doctorName="Dr. [Physician Name]"
          institution="SIH National Telemedicine DR Screening Network"
        />
      )}

      {activeTab !== "landing" && (
        <footer className="border-t border-stone-200/80 bg-white py-4 text-center text-xs text-stone-500 no-print">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <span className="font-semibold text-slate-800">
              RetinaScan AI Workstation
            </span>
            <span className="text-[11px] text-stone-400">
              Explainable AI Retinal Screening &bull; MathWorks HealthTech PS 26038
            </span>
            <span className="font-mono text-[11px] text-stone-400">
              Triple IDRiD U-Net ResNet34
            </span>
          </div>
        </footer>
      )}
    </div>
  );
}
