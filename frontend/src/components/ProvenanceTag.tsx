import type { Provenance } from '@/features/operatore/types';

/**
 * Etichetta di provenienza del dato.
 *
 * Su una console che orienta decisioni organizzative, sapere se un numero è osservato,
 * storico, derivato o simulato conta quanto il numero stesso: uno snapshot del 2021
 * presentato come tempo reale sarebbe fuorviante.
 */
const LABELS: Record<Provenance, { text: string; cssVar: string; title: string }> = {
  OBSERVED: {
    text: 'osservato',
    cssVar: '--triage-verde',
    title: 'Dato dichiarato dalla struttura adesso',
  },
  HISTORICAL: {
    text: 'storico',
    cssVar: '--triage-azzurro',
    title: 'Dato reale ma riferito a una data passata',
  },
  OFFICIAL_FORECAST: {
    text: 'previsione ufficiale',
    cssVar: '--triage-azzurro',
    title: 'Previsione pubblicata da una fonte istituzionale',
  },
  DERIVED: {
    text: 'derivato',
    cssVar: '--triage-arancione',
    title: 'Calcolato da HealthPulse a partire da altri dati',
  },
  SIMULATED: {
    text: 'simulato',
    cssVar: '--triage-arancione',
    title: 'Dato inventato per la demo, non reale',
  },
  SYNTHETIC: {
    text: 'sintetico',
    cssVar: '--triage-arancione',
    title: 'Identità o profilo generati, nessuna persona reale',
  },
  UNAVAILABLE: {
    text: 'non disponibile',
    cssVar: '--triage-bianco',
    title: 'Il dato non è presente nelle fonti',
  },
  UNVERIFIED: {
    text: 'non verificato',
    cssVar: '--triage-rosso',
    title: 'Non è stato possibile confermare questo dato',
  },
};

export function ProvenanceTag({ value }: { value: Provenance }) {
  const entry = LABELS[value] ?? LABELS.UNVERIFIED;

  return (
    <span
      title={entry.title}
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide"
      style={{
        color: `rgb(var(${entry.cssVar}))`,
        backgroundColor: `rgb(var(${entry.cssVar}) / 0.12)`,
      }}
    >
      {entry.text}
    </span>
  );
}
