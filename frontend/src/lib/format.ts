const NUMBER_FORMAT = new Intl.NumberFormat('it-IT');

const DATE_TIME_FORMAT = new Intl.DateTimeFormat('it-IT', {
  day: '2-digit',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});

export function formatNumber(value: number): string {
  return NUMBER_FORMAT.format(value);
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '—' : DATE_TIME_FORMAT.format(date);
}

/** Unisce i pezzi di un indirizzo saltando quelli mancanti. */
export function joinParts(parts: (string | null | undefined)[], separator = ' · '): string {
  return parts.filter((part): part is string => Boolean(part && part.trim())).join(separator);
}
