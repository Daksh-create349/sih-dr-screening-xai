import React from "react";
import { StatusBadge, BadgeVariant } from "./StatusBadge";

export interface ResultSectionProps {
  title: string;
  description?: string;
  statusLabel?: string;
  statusVariant?: BadgeVariant;
  icon?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const ResultSection: React.FC<ResultSectionProps> = ({
  title,
  description,
  statusLabel,
  statusVariant = "neutral",
  icon,
  children,
  className = "",
}) => {
  return (
    <section
      aria-labelledby={`section-${title.toLowerCase().replace(/\s+/g, "-")}`}
      className={`rounded-2xl border border-stone-200/90 bg-white p-4.5 sm:p-5 shadow-xs transition-all duration-200 hover:border-stone-300 ${className}`}
    >
      <div className="mb-3.5 flex items-start justify-between gap-3 border-b border-stone-100 pb-3">
        <div className="flex items-center space-x-2.5">
          {icon && (
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-stone-100 text-stone-700">
              {icon}
            </div>
          )}
          <div>
            <h3
              id={`section-${title.toLowerCase().replace(/\s+/g, "-")}`}
              className="text-sm font-bold tracking-tight text-stone-900"
            >
              {title}
            </h3>
            {description && (
              <p className="text-xs text-stone-500">{description}</p>
            )}
          </div>
        </div>

        {statusLabel && (
          <StatusBadge label={statusLabel} variant={statusVariant} dot />
        )}
      </div>

      <div className="text-xs text-stone-600">{children}</div>
    </section>
  );
};
