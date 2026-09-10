import type { PlanOption } from '@/features/triage/types';

export type CongestionLevel = PlanOption['congestion_level'];

/** Il congestionamento riusa la scala cromatica del triage: un solo vocabolario di colori. */
export const CONGESTION_COLORS: Record<CongestionLevel, string> = {
  basso: '--triage-verde',
  medio: '--triage-arancione',
  alto: '--triage-rosso',
};

/**
 * Colori per i marker della mappa.
 *
 * Leaflet scrive i colori come attributi SVG, dove `var(--token)` non viene risolto:
 * qui servono valori espliciti. Sono comunque gli stessi della scala triage in tema
 * chiaro, ed è corretto che non seguano il tema scuro perché le tile OpenStreetMap
 * restano chiare in entrambi i casi.
 */
export const MAP_COLORS: Record<CongestionLevel, string> = {
  basso: '#168a5c',
  medio: '#be600c',
  alto: '#be2a2a',
};

export const MAP_ORIGIN_COLOR = '#0d766e';

export const CONGESTION_LABELS: Record<CongestionLevel, string> = {
  basso: 'poco affollato',
  medio: 'affollato',
  alto: 'molto affollato',
};

/** Minuti in formato leggibile: 95 → "1h 35min". */
export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest === 0 ? `${hours}h` : `${hours}h ${rest}min`;
}
