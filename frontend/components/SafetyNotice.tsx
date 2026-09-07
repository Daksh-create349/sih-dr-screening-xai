import React from "react";
import { Info } from "lucide-react";

export interface SafetyNoticeProps {
  className?: string;
}

export const SafetyNotice: React.FC<SafetyNoticeProps> = ({ className = "" }) => {
  return (
    <div
      role="note"
      aria-label="Clinical safety notice"
      className={`rounded-2xl border border-stone-200/90 bg-stone-50/70 p-4 text-stone-600 shadow-2xs ${className}`}
    >
      <div className="flex items-start space-x-2.5">
        <Info
          className="mt-0.5 h-4 w-4 shrink-0 text-stone-500"
          aria-hidden="true"
        />
        <p className="text-xs leading-relaxed">
          <strong className="font-semibold text-stone-800">Clinical Safety Notice:</strong>{" "}
          This system provides automated AI-assisted technical decision support only. It does not replace a comprehensive dilated eye examination by a qualified ophthalmologist or optometrist.
        </p>
      </div>
    </div>
  );
};
