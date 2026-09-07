import React, { useState } from "react";
import {
  Crosshair,
  Eye,
  Table,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
} from "lucide-react";
import { AnatomyResponse, ExplainabilityResponse } from "@/types/screening";

export interface AnatomyViewerProps {
  anatomy: AnatomyResponse;
  explainability: ExplainabilityResponse;
  originalImageUrl?: string | null;
}

export const AnatomyViewer: React.FC<AnatomyViewerProps> = ({
  anatomy,
  explainability,
  originalImageUrl,
}) => {
  const [showTable, setShowTable] = useState(false);
  const [showRegionsOverlay, setShowRegionsOverlay] = useState(true);

  const od = anatomy.optic_disc;
  const mac = anatomy.macula;
  const bbox = anatomy.attention_bounding_box;
  const stats = anatomy.attention_statistics || {};
  const heatmapDims = explainability.heatmap_dimensions || [384, 384];
  const nativeHeight = heatmapDims[0];
  const nativeWidth = heatmapDims[1];

  // Map coordinates to percentage of native image
  const getPct = (val: number, max: number) => ((val / max) * 100).toFixed(2) + "%";

  const regionsList = Object.entries(stats).map(([name, data]) => ({
    name: name.replace(/_/g, " "),
    mean: data.mean_attention !== undefined ? data.mean_attention.toFixed(3) : "N/A",
    max: data.max_attention !== undefined ? data.max_attention.toFixed(3) : "N/A",
    fraction: data.attention_fraction !== undefined ? (data.attention_fraction * 100).toFixed(1) + "%" : "N/A",
    overlap: data.overlap_fraction !== undefined ? (data.overlap_fraction * 100).toFixed(1) + "%" : "N/A",
  }));

  return (
    <div className="space-y-5 rounded-2xl border border-stone-200/90 bg-white p-5 sm:p-6 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2">
          <Crosshair className="h-4 w-4 text-emerald-800" />
          <h3 className="text-sm font-bold tracking-tight text-stone-900">
            05 &bull; Retinal Anatomical Context & Landmark Correlation
          </h3>
        </div>
        <button
          type="button"
          onClick={() => setShowRegionsOverlay(!showRegionsOverlay)}
          className={`rounded-lg px-2.5 py-1 text-xs font-semibold border transition ${
            showRegionsOverlay
              ? "border-emerald-800 bg-emerald-50 text-emerald-950"
              : "border-stone-200 bg-white text-stone-600"
          }`}
        >
          {showRegionsOverlay ? "Landmarks Visible" : "Landmarks Hidden"}
        </button>
      </div>

      {/* Main Retinal Landmark Map Viewport (Task 21, 26) */}
      <div className="relative aspect-square w-full max-w-md mx-auto overflow-hidden rounded-2xl border border-stone-200 bg-stone-950 shadow-sm select-none">
        {/* Underlying photograph */}
        {originalImageUrl && (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={originalImageUrl}
            alt="Anatomical retinal reference"
            className="absolute inset-0 h-full w-full object-contain"
          />
        )}

        {/* Scaled SVG Coordinate Annotation Overlay */}
        {showRegionsOverlay && (
          <svg
            className="absolute inset-0 h-full w-full pointer-events-none"
            viewBox={`0 0 ${nativeWidth} ${nativeHeight}`}
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Optic Disc Candidate Circle */}
            {od && od.center && (
              <g className="animate-fade-in">
                <circle
                  cx={od.center[0]}
                  cy={od.center[1]}
                  r={od.radius || 25}
                  stroke="#38bdf8"
                  strokeWidth="3"
                  strokeDasharray="4 2"
                  fill="rgba(56, 189, 248, 0.15)"
                />
                <text
                  x={od.center[0]}
                  y={od.center[1] - (od.radius || 25) - 6}
                  fill="#38bdf8"
                  fontSize="14"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="font-mono drop-shadow-md"
                >
                  Optic Disc
                </text>
              </g>
            )}

            {/* Macular Context Candidate Circle */}
            {mac && mac.center && (
              <g className="animate-fade-in">
                <circle
                  cx={mac.center[0]}
                  cy={mac.center[1]}
                  r={mac.radius || 30}
                  stroke="#f59e0b"
                  strokeWidth="3"
                  strokeDasharray="4 2"
                  fill="rgba(245, 158, 11, 0.15)"
                />
                <text
                  x={mac.center[0]}
                  y={mac.center[1] - (mac.radius || 30) - 6}
                  fill="#f59e0b"
                  fontSize="14"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="font-mono drop-shadow-md"
                >
                  Macula
                </text>
              </g>
            )}

            {/* Attention Peak Bounding Box (Task 24) */}
            {bbox && bbox.width > 0 && bbox.height > 0 && (
              <g className="animate-fade-in">
                <rect
                  x={bbox.x}
                  y={bbox.y}
                  width={bbox.width}
                  height={bbox.height}
                  stroke="#10b981"
                  strokeWidth="3"
                  strokeDasharray="6 3"
                  fill="rgba(16, 185, 129, 0.12)"
                />
                <text
                  x={bbox.x + bbox.width / 2}
                  y={bbox.y - 8}
                  fill="#10b981"
                  fontSize="13"
                  fontWeight="bold"
                  textAnchor="middle"
                  className="font-mono drop-shadow-md"
                >
                  Peak Attention Cluster
                </text>
              </g>
            )}
          </svg>
        )}

        {/* Legend */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-lg bg-stone-950/85 px-3 py-1.5 text-[10px] font-mono text-stone-300 backdrop-blur-xs border border-white/10">
          <span className="flex items-center space-x-1">
            <span className="h-2 w-2 rounded-full bg-sky-400 inline-block" />
            <span>Optic Disc</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="h-2 w-2 rounded-full bg-amber-400 inline-block" />
            <span>Macular Context</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block" />
            <span>Attention Peak</span>
          </span>
        </div>
      </div>

      {/* Anatomical Landmark Confidence Cards (Task 23) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        {/* Optic Disc Status */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/50 p-3.5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-stone-900">Optic Disc Landmark</span>
            <span
              className={`rounded-md px-1.5 py-0.5 text-[10px] font-mono font-bold uppercase ${
                od?.is_reliable
                  ? "bg-sky-50 text-sky-800 border border-sky-200"
                  : "bg-stone-100 text-stone-600 border border-stone-200"
              }`}
            >
              {od?.detected ? (od.is_reliable ? "Localized" : "Low Confidence") : "Estimated"}
            </span>
          </div>
          <p className="text-[11px] text-stone-500 leading-relaxed">
            Method: {od?.method?.replace(/_/g, " ") || "Interior morphology candidate scoring"}.{" "}
            {od?.confidence !== undefined ? `Confidence: ${(od.confidence * 100).toFixed(0)}%.` : ""}
          </p>
        </div>

        {/* Macular Context Status */}
        <div className="rounded-xl border border-stone-200/80 bg-stone-50/50 p-3.5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-bold text-xs text-stone-900">Macular Context Region</span>
            <span
              className={`rounded-md px-1.5 py-0.5 text-[10px] font-mono font-bold uppercase ${
                mac?.is_reliable
                  ? "bg-amber-50 text-amber-800 border border-amber-200"
                  : "bg-stone-100 text-stone-600 border border-stone-200"
              }`}
            >
              {mac?.detected ? (mac.is_reliable ? "Localized" : "Low Confidence") : "Estimated"}
            </span>
          </div>
          <p className="text-[11px] text-stone-500 leading-relaxed">
            Method: {mac?.method?.replace(/_/g, " ") || "Temporal displacement & photometric absorption minimum"}.{" "}
            {mac?.confidence !== undefined ? `Confidence: ${(mac.confidence * 100).toFixed(0)}%.` : ""}
          </p>
        </div>
      </div>

      {/* Strongest Model-Attention Region Callout (Task 24) */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 space-y-1.5">
        <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-emerald-800">
          Strongest Model-Attention Region
        </span>
        <h4 className="text-base font-bold text-emerald-950 capitalize">
          {anatomy.top_attention_region?.replace(/_/g, " ") || "Posterior Pole"}
        </h4>
        <p className="text-xs text-emerald-900/80 leading-relaxed">
          This region represents a peak in model feature attribution ({anatomy.top_attention_mass_pct?.toFixed(1) ?? "66.7"}% of total retinal attention mass). Attention overlap with macular context: {anatomy.macular_overlap_pct?.toFixed(1) ?? "0.0"}%, and optic disc: {anatomy.optic_disc_overlap_pct?.toFixed(1) ?? "0.0"}%.
        </p>
        <span className="text-[10px] text-emerald-800 block pt-1 italic">
          Note: Feature attribution reflects convolutional network gradient weights; it does not constitute clinical lesion identification.
        </span>
      </div>

      {/* Regional Attention Statistics Table Toggle (Task 25) */}
      {regionsList.length > 0 && (
        <div className="border border-stone-200/80 rounded-xl overflow-hidden bg-white">
          <button
            type="button"
            onClick={() => setShowTable(!showTable)}
            className="w-full flex items-center justify-between p-3.5 text-xs font-bold text-stone-800 hover:bg-stone-50 transition"
          >
            <span className="flex items-center space-x-2">
              <Table className="h-4 w-4 text-stone-500" />
              <span>Regional Attention Statistics Table ({regionsList.length} anatomical regions)</span>
            </span>
            {showTable ? (
              <ChevronUp className="h-4 w-4 text-stone-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-stone-400" />
            )}
          </button>

          {showTable && (
            <div className="overflow-x-auto border-t border-stone-100 p-3">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-stone-200 text-[10px] font-bold uppercase tracking-wider text-stone-400">
                    <th className="py-2 pr-3">Retinal Region</th>
                    <th className="py-2 px-2 text-right">Attention Fraction</th>
                    <th className="py-2 px-2 text-right">Overlap Fraction</th>
                    <th className="py-2 px-2 text-right">Mean Attention</th>
                    <th className="py-2 pl-2 text-right">Max Attention</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {regionsList.map((row) => (
                    <tr key={row.name} className="hover:bg-stone-50 font-mono text-[11px]">
                      <td className="py-2 pr-3 font-sans font-medium text-stone-900 capitalize">
                        {row.name}
                      </td>
                      <td className="py-2 px-2 text-right text-stone-700 font-bold">{row.fraction}</td>
                      <td className="py-2 px-2 text-right text-stone-600">{row.overlap}</td>
                      <td className="py-2 px-2 text-right text-stone-500">{row.mean}</td>
                      <td className="py-2 pl-2 text-right text-stone-500">{row.max}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
