import { facilityTypeLabel } from '@/lib/facilityTypes';
import type { FacilityType } from '@/api/types';
import {
  CONGESTION_COLORS,
  CONGESTION_LABELS,
  formatMinutes,
} from '@/features/triage/congestion';
import type { PlanOption } from '@/features/triage/types';

type PlanOptionCardProps = {
  option: PlanOption;
  selected: boolean;
  onSelect: () => void;
};

export function PlanOptionCard({ option, selected, onSelect }: PlanOptionCardProps) {
  const cssVar = CONGESTION_COLORS[option.congestion_level];

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`w-full rounded-2xl border bg-surface p-4 text-left transition-colors ${
        selected ? 'border-accent' : 'border-line hover:border-accent/40'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold text-ink">{option.name}</p>
          <p className="mt-0.5 text-xs text-faint">
            {facilityTypeLabel(option.type as FacilityType)}
            {option.municipality ? ` · ${option.municipality}` : ''}
          </p>
        </div>
        {option.recommended && (
          <span className="shrink-0 rounded-full bg-accent-soft px-2.5 py-1 text-[11px] font-medium text-accent-ink">
            consigliata
          </span>
        )}
      </div>

      <div className="tabular mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
        <span className="font-semibold text-ink">{formatMinutes(option.total_minutes)}</span>
        <span className="text-xs text-muted">
          {option.travel_minutes} min di viaggio · {option.distance_km} km
        </span>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span
          className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium"
          style={{ color: `rgb(var(${cssVar}))`, backgroundColor: `rgb(var(${cssVar}) / 0.12)` }}
        >
          <span
            aria-hidden="true"
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: `rgb(var(${cssVar}))` }}
          />
          {CONGESTION_LABELS[option.congestion_level]} · attesa {option.waiting_minutes} min
        </span>
        {option.route_source === 'stimato' && (
          <span className="text-[11px] text-faint" title="OSRM non ha risposto: distanza in linea d'aria">
            tragitto stimato
          </span>
        )}
      </div>
    </button>
  );
}
