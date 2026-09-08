/**
 * ClinicalReportModal — generates and downloads a formal clinical PDF report
 * for a completed DR screening session. No server round-trip; pure jsPDF canvas.
 */

"use client";

import React, { useState, useCallback } from "react";
import {
  X,
  Download,
  FileText,
  Loader2,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Printer,
} from "lucide-react";
import { ScreeningResponse } from "@/types/screening";
import { getAssetUrl, getEvidenceOverlayUrl } from "@/lib/api";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatTimestamp(): string {
  const now = new Date();
  return now.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "long",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDate(): string {
  return new Date().toLocaleDateString("en-IN", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "long",
    day: "2-digit",
  });
}

async function imageToBase64(url: string): Promise<string | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) { resolve(null); return; }
      ctx.drawImage(img, 0, 0);
      resolve(canvas.toDataURL("image/jpeg", 0.85));
    };
    img.onerror = () => resolve(null);
    setTimeout(() => resolve(null), 8000);
    img.src = url;
  });
}

// ─── PDF Generation ───────────────────────────────────────────────────────────

async function generateClinicalPDF(
  result: ScreeningResponse,
  opts: {
    patientId: string;
    doctorName: string;
    institution: string;
    studyFilename: string;
  }
): Promise<void> {
  const { jsPDF } = await import("jspdf");

  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

  const PAGE_W = 210;
  const PAGE_H = 297;
  const MARGIN = 16;
  const CONTENT_W = PAGE_W - MARGIN * 2;

  const DARK: [number, number, number]   = [15, 23, 42];
  const MED: [number, number, number]    = [71, 85, 105];
  const LIGHT: [number, number, number]  = [148, 163, 184];
  const ACCENT: [number, number, number] = [16, 185, 129];
  const WARN: [number, number, number]   = [239, 68, 68];
  const AMBE: [number, number, number]   = [245, 158, 11];
  const WHITE: [number, number, number]  = [255, 255, 255];
  const BGLIGHT: [number, number, number]= [248, 250, 252];

  let y = 0;

  const setColor  = (c: [number, number, number]) => doc.setTextColor(c[0], c[1], c[2]);
  const setFill   = (c: [number, number, number]) => doc.setFillColor(c[0], c[1], c[2]);
  const setStroke = (c: [number, number, number]) => doc.setDrawColor(c[0], c[1], c[2]);
  const hLine = (ty: number, col: [number,number,number] = LIGHT) => {
    setStroke(col); doc.setLineWidth(0.2);
    doc.line(MARGIN, ty, PAGE_W - MARGIN, ty);
  };
  const txt = (s: string, x: number, ty: number, opts?: Record<string, unknown>) =>
    doc.text(s, x, ty, opts as Parameters<typeof doc.text>[3]);

  // ── HEADER ────────────────────────────────────────────────────────────────
  setFill(DARK); doc.rect(0, 0, PAGE_W, 36, "F");
  doc.setFont("helvetica", "bold"); doc.setFontSize(13); setColor(WHITE);
  txt(opts.institution, MARGIN, 13);
  doc.setFont("helvetica", "normal"); doc.setFontSize(8); setColor(LIGHT);
  txt("AI-Assisted Diabetic Retinopathy Screening Report", MARGIN, 20);
  txt("SIH Problem Code 26038 | ICDR Classification System", MARGIN, 25.5);
  doc.setFont("helvetica", "bold"); doc.setFontSize(7.5); setColor([52, 211, 153]);
  txt("CLINICAL DECISION SUPPORT", PAGE_W - MARGIN, 13, { align: "right" });
  doc.setFont("helvetica", "normal"); doc.setFontSize(6.5); setColor(LIGHT);
  txt("FOR SCREENING USE ONLY", PAGE_W - MARGIN, 18.5, { align: "right" });
  txt(formatDate(), PAGE_W - MARGIN, 24, { align: "right" });
  y = 44;

  // ── PATIENT META STRIP ────────────────────────────────────────────────────
  setFill(BGLIGHT); setStroke([226, 232, 240]); doc.setLineWidth(0.3);
  doc.roundedRect(MARGIN, y, CONTENT_W, 20, 2, 2, "FD");
  const colW = CONTENT_W / 4;
  const meta = [
    ["Patient ID", opts.patientId],
    ["Study File", opts.studyFilename.slice(0, 20)],
    ["Result ID",  result.result_id.slice(0, 12) + "…"],
    ["Report Time",formatTimestamp().slice(0, 18)],
  ];
  meta.forEach(([label, value], i) => {
    const mx = MARGIN + i * colW + 4;
    doc.setFont("helvetica", "normal"); doc.setFontSize(6.5); setColor(LIGHT); txt(label, mx, y + 6);
    doc.setFont("helvetica", "bold");   doc.setFontSize(8);   setColor(DARK);  txt(value, mx, y + 13);
  });
  y += 26;

  // ── IQA STAMP ─────────────────────────────────────────────────────────────
  const iq = result.image_quality;
  const iqCol: [number,number,number] =
    iq.decision === "GOOD" ? ACCENT : iq.decision === "BORDERLINE" ? AMBE : WARN;
  setFill(iqCol); doc.roundedRect(MARGIN, y, CONTENT_W, 16, 2, 2, "F");
  doc.setFont("helvetica", "bold"); doc.setFontSize(9); setColor(WHITE);
  txt(`IQA STAMP: ${iq.decision}`, MARGIN + 4, y + 7);
  doc.setFont("helvetica", "normal"); doc.setFontSize(7.5);
  txt(
    `Quality Score: ${iq.overall_score.toFixed(1)}/100  |  Focus: ${iq.focus.toFixed(0)}  |  Illumination: ${iq.illumination.toFixed(0)}  |  FoV: ${iq.fov.toFixed(0)}  |  Centering: ${iq.centering.toFixed(0)}`,
    PAGE_W - MARGIN, y + 7, { align: "right" }
  );
  if (iq.enhancement_applied) txt("[ CLAHE Enhancement Applied ]", PAGE_W - MARGIN, y + 13, { align: "right" });
  y += 22;

  // ── DR GRADE ──────────────────────────────────────────────────────────────
  const cls = result.classification;
  const ref = result.referable;
  doc.setFont("helvetica", "bold"); doc.setFontSize(7.5); setColor(LIGHT);
  txt("ICDR DR SEVERITY CLASSIFICATION", MARGIN, y); y += 5; hLine(y); y += 5;

  const gradeText = cls ? `Grade ${cls.predicted_class}: ${cls.predicted_label}` : "Classification Unavailable";
  doc.setFont("helvetica", "bold"); doc.setFontSize(22); setColor(DARK); txt(gradeText, MARGIN, y + 10);
  if (cls) { doc.setFont("helvetica","bold"); doc.setFontSize(9); setColor(ACCENT); txt(`${(cls.top_probability*100).toFixed(1)}% Confidence`, PAGE_W-MARGIN, y+10, {align:"right"}); }
  y += 16;

  if (ref) {
    const refCol: [number,number,number] = ref.is_referable ? WARN : ACCENT;
    setFill(refCol); doc.roundedRect(MARGIN, y, 90, 10, 2, 2, "F");
    doc.setFont("helvetica","bold"); doc.setFontSize(7.5); setColor(WHITE);
    txt(ref.is_referable ? `REFERABLE — Prob ${(ref.probability*100).toFixed(1)}%` : `NON-REFERABLE — Prob ${(ref.probability*100).toFixed(1)}%`, MARGIN+3, y+6.5);
  }
  y += 16;

  // Probability bars
  if (cls?.probabilities) {
    doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor(MED); txt("ICDR Class Probability Distribution", MARGIN, y); y += 5;
    const barW = (CONTENT_W - 10) / 5;
    Object.entries(cls.probabilities).forEach(([grade, prob], i) => {
      const bx = MARGIN + i * barW + 1;
      const maxH = 14; const bH = Math.max(1, Math.round((prob as number) * maxH));
      const isA = Number(grade) === cls.predicted_class;
      setFill([226,232,240]); doc.rect(bx, y, barW-2, maxH, "F");
      setFill(isA ? ACCENT : [148,163,184]); doc.rect(bx, y + maxH - bH, barW-2, bH, "F");
      doc.setFont("helvetica", isA ? "bold" : "normal"); doc.setFontSize(5.5); setColor(isA ? DARK : LIGHT);
      txt(`G${grade}: ${((prob as number)*100).toFixed(0)}%`, bx+(barW-2)/2, y+maxH+4, {align:"center"});
    });
    y += 26;
  }
  hLine(y); y += 8;

  // ── GRAD-CAM + EVIDENCE IMAGES ────────────────────────────────────────────
  doc.setFont("helvetica","bold"); doc.setFontSize(7.5); setColor(LIGHT);
  txt("AI VISUAL ATTRIBUTION", MARGIN, y); y += 5;

  const gcUrl = result.explainability?.overlay_url ? getAssetUrl(result.explainability.overlay_url) : null;
  const evUrl = result.result_id ? getEvidenceOverlayUrl(result.result_id) : null;
  const [gcB64, evB64] = await Promise.all([
    gcUrl ? imageToBase64(gcUrl) : Promise.resolve(null),
    evUrl ? imageToBase64(evUrl) : Promise.resolve(null),
  ]);

  const imgH = 52; const imgW = (CONTENT_W - 4) / 2;
  setStroke([226,232,240]); doc.setLineWidth(0.3);

  if (gcB64) {
    doc.addImage(gcB64, "JPEG", MARGIN, y, imgW, imgH);
  } else {
    setFill(BGLIGHT); doc.roundedRect(MARGIN, y, imgW, imgH, 2, 2, "F");
    doc.setFont("helvetica","italic"); doc.setFontSize(7); setColor(LIGHT);
    txt("Grad-CAM Unavailable", MARGIN+imgW/2, y+imgH/2, {align:"center"});
  }
  doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor(MED);
  txt("Grad-CAM Feature Attribution", MARGIN+imgW/2, y+imgH+4, {align:"center"});
  doc.setFont("helvetica","normal"); doc.setFontSize(6); setColor(LIGHT);
  txt(`Layer: ${result.explainability?.layer_name || "top_conv"}`, MARGIN+imgW/2, y+imgH+8, {align:"center"});

  if (evB64) {
    doc.addImage(evB64, "JPEG", MARGIN+imgW+4, y, imgW, imgH);
  } else {
    setFill(BGLIGHT); doc.roundedRect(MARGIN+imgW+4, y, imgW, imgH, 2, 2, "F");
    doc.setFont("helvetica","italic"); doc.setFontSize(7); setColor(LIGHT);
    txt("Evidence Overlay Unavailable", MARGIN+imgW+4+imgW/2, y+imgH/2, {align:"center"});
  }
  doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor(MED);
  txt("IDRiD Deep Lesion Overlay", MARGIN+imgW+4+imgW/2, y+imgH+4, {align:"center"});
  doc.setFont("helvetica","normal"); doc.setFontSize(6); setColor(LIGHT);
  txt("Optic Disc · Exudates · Hemorrhages", MARGIN+imgW+4+imgW/2, y+imgH+8, {align:"center"});
  y += imgH + 14;

  hLine(y); y += 8;

  // ── 5-BIOMARKER TABLE ─────────────────────────────────────────────────────
  doc.setFont("helvetica","bold"); doc.setFontSize(7.5); setColor(LIGHT);
  txt("RETINAL BIOMARKER ANALYSIS — 6 CLINICAL SYSTEMS", MARGIN, y); y += 5;

  const rawL = (result.evidence?.lesions as Record<string,unknown>) || {};
  const strct = (result.evidence?.structured_record as Record<string,unknown>) || {};
  const sStats = ((strct?.provenance as Record<string,unknown>)?.lesion_statistics as Record<string,unknown>) || {};
  const sOD = (strct?.structures as Record<string,unknown>)?.optic_disc as Record<string,unknown>;
  const odR2 = rawL?.optic_disc as Record<string,unknown>;
  const odCtr = (odR2?.center_xy as number[]) || (sOD ? [sOD.x as number, sOD.y as number] : null);
  const odRad = (odR2?.radius_px as number) ?? (sOD?.radius as number);
  const exR = rawL?.hard_exudates as Record<string,unknown>;
  const exCnt = (exR?.lesion_count as number) ?? (sStats?.exudate_clusters as number) ?? 0;
  const exPx  = (exR?.total_lesion_pixels as number) ?? 0;
  const exFrac= (exR?.area_fraction as number) ?? (sStats?.exudate_area_fraction as number) ?? 0;
  const hmR = rawL?.hemorrhages as Record<string,unknown>;
  const hmCnt = (hmR?.lesion_count as number) ?? (sStats?.hemorrhage_clusters as number) ?? 0;
  const hmPx  = (hmR?.total_lesion_pixels as number) ?? 0;
  const hmFrac= (hmR?.area_fraction as number) ?? (sStats?.hemorrhage_area_fraction as number) ?? 0;
  const maR = rawL?.microaneurysms as Record<string,unknown>;
  const maCnt = (maR?.lesion_count as number) ?? (sStats?.microaneurysm_count as number) ?? 0;
  const maPx  = (maR?.total_lesion_pixels as number) ?? 0;
  const maFrac= (maR?.area_fraction as number) ?? (sStats?.microaneurysm_area_fraction as number) ?? 0;
  const csme = rawL?.csme_risk as Record<string,unknown>;
  const csLvl = (csme?.risk_level as string) || (sStats?.macular_edema_risk_level as string) || "NONE";
  const csDDist = (csme?.min_distance_in_disc_diameters as number) ?? null;

  type BioRow = [string,string,string,string,string];
  const HEADERS: BioRow = ["Biomarker System","Status","Key Metric","Area / Severity","Model (Dice / Method)"];
  const ROWS: BioRow[] = [
    ["Optic Disc",     odCtr?"DETECTED":"ESTIMATED", odCtr?`Center (${Math.round(odCtr[0])}, ${Math.round(odCtr[1])})` : "Localized",   odRad?`r = ${Math.round(odRad)} px`:"—",                           "U-Net ResNet34 (0.9859)"],
    ["Hard Exudates",  exCnt>0?"DETECTED":"CLEAR",   `${exCnt} clusters`,                                                                exPx>0?`${exPx.toLocaleString()} px (${(exFrac*100).toFixed(2)}%)`:"0 px","U-Net ResNet34 (0.7580)"],
    ["Hemorrhages",    hmCnt>0?"DETECTED":"CLEAR",   `${hmCnt} foci`,                                                                    hmPx>0?`${hmPx.toLocaleString()} px (${(hmFrac*100).toFixed(2)}%)`:"0 px","U-Net ResNet34 (0.7482)"],
    ["Microaneurysms", maCnt>0?"DETECTED":"CLEAR",   `${maCnt} MAs`,                                                                     maPx>0?`${maPx.toLocaleString()} px (${(maFrac*100).toFixed(3)}%)`:"0 px","Morphological Top-Hat"],
    ["CSME / Macular Risk", csLvl, csDDist!=null?`${csDDist} disc diam. from fovea`:"Proximity assessed",csLvl==="HIGH"?"URGENT: central vision":"MODERATE"===csLvl?"Monitor closely":"No macular threat","Geometric proximity"],
    ["Retinal Vessels","ANALYSED","Frangi Hessian multiscale","Vessel tree segmented","Hessian classical filter"],
  ];

  const COL_W = [38,22,40,45,33];
  const ROW_H = 8;
  const TOTAL_W = COL_W.reduce((a,b)=>a+b,0);

  // Header
  setFill(DARK); doc.rect(MARGIN, y, TOTAL_W, ROW_H, "F");
  let cx = MARGIN;
  HEADERS.forEach((h,i) => {
    doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor(WHITE); txt(h, cx+2, y+6);
    cx += COL_W[i];
  });
  y += ROW_H;

  // Data rows
  ROWS.forEach((row, ri) => {
    setFill(ri%2===0 ? WHITE : BGLIGHT); doc.rect(MARGIN, y, TOTAL_W, ROW_H, "F");
    setStroke([226,232,240]); doc.setLineWidth(0.15);
    doc.line(MARGIN, y+ROW_H, MARGIN+TOTAL_W, y+ROW_H);
    cx = MARGIN;
    row.forEach((cell, ci) => {
      const isStatus = ci === 1;
      const sc: [number,number,number] =
        cell==="DETECTED"||cell==="ANALYSED" ? ACCENT :
        cell==="CLEAR" ? [100,116,139] :
        cell==="HIGH" ? WARN : cell==="MODERATE" ? AMBE : cell==="ESTIMATED" ? AMBE : MED;
      doc.setFont("helvetica", (isStatus||ci===0)?"bold":"normal"); doc.setFontSize(6);
      setColor(isStatus ? sc : ci===0 ? DARK : MED);
      const maxC = Math.floor(COL_W[ci]/1.8);
      txt(cell.length>maxC ? cell.slice(0,maxC-1)+"…" : cell, cx+2, y+6);
      cx += COL_W[ci];
    });
    y += ROW_H;
  });
  setStroke([203,213,225]); doc.setLineWidth(0.3);
  doc.rect(MARGIN, y - ROW_H*ROWS.length - ROW_H, TOTAL_W, ROW_H*(ROWS.length+1));
  y += 8;

  // ── AI NARRATIVE ──────────────────────────────────────────────────────────
  if (result.evidence?.narrative) {
    doc.setFont("helvetica","bold"); doc.setFontSize(7.5); setColor(LIGHT);
    txt("SYNTHESIZED DIAGNOSTIC NARRATIVE", MARGIN, y); y += 5;
    setFill(BGLIGHT); setStroke([226,232,240]); doc.setLineWidth(0.2);
    doc.roundedRect(MARGIN, y, CONTENT_W, 20, 2, 2, "FD");
    doc.setFont("helvetica","italic"); doc.setFontSize(7); setColor(MED);
    const lines = doc.splitTextToSize(result.evidence.narrative, CONTENT_W-6) as string[];
    lines.slice(0,4).forEach((l,li) => txt(l, MARGIN+3, y+5.5+li*3.8));
    y += 26;
  }

  hLine(y, MED); y += 8;

  // ── SIGN-OFF BLOCK ────────────────────────────────────────────────────────
  if (y > PAGE_H - 65) { doc.addPage(); y = MARGIN + 10; }
  doc.setFont("helvetica","bold"); doc.setFontSize(7.5); setColor(LIGHT);
  txt("PHYSICIAN SIGN-OFF & VERIFICATION", MARGIN, y); y += 6;

  const SIGN_H = 44;
  setFill(BGLIGHT); setStroke([203,213,225]); doc.setLineWidth(0.3);
  doc.roundedRect(MARGIN, y, CONTENT_W, SIGN_H, 2, 2, "FD");
  doc.setFont("helvetica","bold"); doc.setFontSize(8); setColor(DARK);
  txt("Reviewing Physician / Ophthalmologist", MARGIN+4, y+8);
  doc.setFont("helvetica","normal"); doc.setFontSize(7.5); setColor(MED);
  txt(`Name: ${opts.doctorName}`, MARGIN+4, y+15);
  txt(`Institution: ${opts.institution}`, MARGIN+4, y+21);
  txt(`Date of Report: ${formatDate()}`, MARGIN+4, y+27);
  txt("Signature: ___________________________", MARGIN+4, y+36);

  // Stamp box
  const stW = 58; const stX = PAGE_W - MARGIN - stW;
  setFill([240,253,244]); setStroke(ACCENT); doc.setLineWidth(0.5);
  doc.roundedRect(stX, y+4, stW, SIGN_H-8, 2, 2, "FD");
  doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor(ACCENT);
  txt("AI SCREENING VERIFIED", stX+stW/2, y+12, {align:"center"});
  doc.setFont("helvetica","normal"); doc.setFontSize(6); setColor(MED);
  txt("EfficientNetB3 Classifier v2", stX+stW/2, y+18, {align:"center"});
  txt("IDRiD Segmentation Engine", stX+stW/2, y+23, {align:"center"});
  txt("Grad-CAM Explainability", stX+stW/2, y+28, {align:"center"});
  txt(`Result: ${result.result_id.slice(0,10)}…`, stX+stW/2, y+34, {align:"center"});
  y += SIGN_H + 8;

  // ── DISCLAIMER ────────────────────────────────────────────────────────────
  setFill([254,243,199]); setStroke([245,158,11]); doc.setLineWidth(0.3);
  doc.roundedRect(MARGIN, y, CONTENT_W, 18, 2, 2, "FD");
  doc.setFont("helvetica","bold"); doc.setFontSize(6.5); setColor([146,64,14]);
  txt("REGULATORY DISCLAIMER", MARGIN+3, y+7);
  doc.setFont("helvetica","normal"); doc.setFontSize(6); setColor([120,53,15]);
  txt("This report is generated by an AI-assisted clinical decision support system for preliminary screening triage.", MARGIN+3, y+12.5);
  txt("It does NOT constitute a standalone medical diagnosis. Final clinical decisions must be made by a qualified ophthalmologist.", MARGIN+3, y+16.5);
  y += 22;

  // ── FOOTER ────────────────────────────────────────────────────────────────
  hLine(PAGE_H-12, LIGHT);
  doc.setFont("helvetica","normal"); doc.setFontSize(6); setColor(LIGHT);
  txt(`Generated by DR Screening Workstation v2.0 | SIH-26038 | ${formatTimestamp()}`, PAGE_W/2, PAGE_H-8, {align:"center"});

  doc.save(`DR_Report_${opts.patientId.replace(/[^a-zA-Z0-9]/g,"_")}_${result.result_id.slice(0,8)}.pdf`);
}

// ─── Modal Component ──────────────────────────────────────────────────────────

export interface ClinicalReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  screeningResult: ScreeningResponse;
  studyFilename?: string;
  patientId?: string;
  doctorName?: string;
  institution?: string;
}

export const ClinicalReportModal: React.FC<ClinicalReportModalProps> = ({
  isOpen,
  onClose,
  screeningResult,
  studyFilename = "retina_scan.png",
  patientId = "#RUR-2026-084",
  doctorName = "Dr. [Physician Name]",
  institution = "SIH National Telemedicine DR Screening Network",
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [formPatientId, setFormPatientId] = useState(patientId);
  const [formDoctorName, setFormDoctorName] = useState(doctorName);
  const [formInstitution, setFormInstitution] = useState(institution);

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true); setError(null); setDone(false);
    try {
      await generateClinicalPDF(screeningResult, {
        patientId: formPatientId,
        doctorName: formDoctorName,
        institution: formInstitution,
        studyFilename,
      });
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }, [screeningResult, formPatientId, formDoctorName, formInstitution, studyFilename]);

  if (!isOpen) return null;

  const iq = screeningResult.image_quality;
  const cls = screeningResult.classification;
  const ref = screeningResult.referable;

  const iqColor =
    iq.decision === "GOOD"       ? "bg-emerald-100 text-emerald-800 border-emerald-300" :
    iq.decision === "BORDERLINE" ? "bg-amber-100 text-amber-800 border-amber-300" :
                                   "bg-rose-100 text-rose-800 border-rose-300";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 no-print">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl rounded-2xl border border-stone-200/90 bg-white shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between border-b border-stone-800 bg-slate-950 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20">
              <FileText className="h-4 w-4 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Clinical PDF Report</h2>
              <p className="text-[11px] text-stone-400">
                Hospital header · IQA stamp · DR grade · Grad-CAM · 5-biomarker table · Doctor sign-off
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose}
            className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-800 hover:text-white transition">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">

          {/* Preview badges */}
          <div className="rounded-xl border border-stone-200 bg-stone-50/60 p-4 space-y-3">
            <span className="text-[10px] font-mono font-bold uppercase text-stone-400 block">
              Report Contents Preview
            </span>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <span className="text-stone-400 text-[10px] font-mono uppercase">IQA Stamp</span>
                <div className={`inline-flex rounded-md border px-2.5 py-1 font-bold text-xs ${iqColor}`}>
                  {iq.decision} — {iq.overall_score.toFixed(1)}/100
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-stone-400 text-[10px] font-mono uppercase">DR Grade</span>
                <div className="font-bold text-slate-900">
                  {cls ? `Grade ${cls.predicted_class}: ${cls.predicted_label}` : "N/A"}
                  {cls && <span className="ml-2 text-stone-400 font-normal">{(cls.top_probability*100).toFixed(1)}%</span>}
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-stone-400 text-[10px] font-mono uppercase">Triage Decision</span>
                <div className={`inline-flex items-center space-x-1 text-xs font-bold ${ref?.is_referable ? "text-rose-700" : "text-emerald-700"}`}>
                  {ref?.is_referable ? <AlertCircle className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />}
                  <span>{ref?.is_referable ? "Referable" : "Non-Referable"}</span>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-stone-400 text-[10px] font-mono uppercase">Result ID</span>
                <div className="font-mono text-xs text-slate-700">{screeningResult.result_id.slice(0,16)}…</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {[
                "✓ Hospital Header","✓ Patient Metadata","✓ IQA Quality Stamp",
                "✓ ICDR Grade + Probabilities","✓ Grad-CAM Image","✓ IDRiD Lesion Overlay",
                "✓ 5-Biomarker Table","✓ AI Narrative","✓ Doctor Sign-Off Block","✓ Disclaimer",
              ].map(item => (
                <span key={item}
                  className="rounded-md bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* Editable metadata */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono font-bold uppercase text-stone-400 block">Report Metadata (Editable)</span>
            <div className="grid grid-cols-1 gap-3">
              {[
                { label:"Patient ID", value: formPatientId, set: setFormPatientId },
                { label:"Reviewing Physician", value: formDoctorName, set: setFormDoctorName },
                { label:"Institution / Hospital", value: formInstitution, set: setFormInstitution },
              ].map(({ label, value, set }) => (
                <div key={label}>
                  <label className="block text-[10px] font-semibold text-stone-500 mb-1 uppercase tracking-wide">
                    {label}
                  </label>
                  <input
                    type="text"
                    value={value}
                    onChange={e => set(e.target.value)}
                    className="w-full rounded-lg border border-stone-200 bg-stone-50 px-3 py-2 text-xs text-slate-900 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-200"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Status */}
          {error && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-800">
              <strong>Error:</strong> {error}
            </div>
          )}
          {done && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800 flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>PDF downloaded successfully. Check your browser&apos;s download folder.</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-stone-100 bg-stone-50 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-[10px] text-stone-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Generated locally. No patient data leaves your device.</span>
          </div>
          <div className="flex items-center space-x-2">
            <button type="button" onClick={onClose}
              className="rounded-lg border border-stone-200 bg-white px-3.5 py-2 text-xs font-medium text-stone-700 hover:bg-stone-50 transition">
              Close
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                setTimeout(() => window.print(), 150);
              }}
              className="inline-flex items-center space-x-1.5 rounded-xl border border-stone-300 bg-white px-3.5 py-2.5 text-xs font-semibold text-stone-800 shadow-2xs hover:bg-stone-50 transition"
            >
              <Printer className="h-3.5 w-3.5 text-stone-600" />
              <span>Print Preview / System PDF</span>
            </button>
            <button type="button" onClick={handleGenerate} disabled={isGenerating}
              className="inline-flex items-center space-x-2 rounded-xl bg-slate-950 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition hover:bg-slate-800 disabled:opacity-60">
              {isGenerating ? (
                <><Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-400" /><span>Building PDF…</span></>
              ) : (
                <><Download className="h-3.5 w-3.5 text-emerald-400" /><span>Download Clinical PDF</span></>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
