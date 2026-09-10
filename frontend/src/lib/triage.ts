/**
 * Scala dei codici di triage e soglie di pressione.
 *
 * Utility pura e condivisa: entrambe le feature ancora da assegnare dovrebbero
 * partire da qui invece di ridefinire colori o etichette. I colori sono variabili CSS
 * (vedi `styles/theme.css`), mai valori hardcodati.
 */

export const TRIAGE_CODES = ['bianco', 'verde', 'azzurro', 'arancione', 'rosso'] as const;

export type TriageCode = (typeof TRIAGE_CODES)[number];

export type TriageDefinition = {
  code: TriageCode;
  label: string;
  /** Etichetta ufficiale del modello a 5 codici in uso nel Lazio. */
  priority: string;
  description: string;
  /** Se il caso può essere gestito fuori dal pronto soccorso. */
  lowIntensity: boolean;
  cssVar: string;
};

export const TRIAGE_SCALE: Record<TriageCode, TriageDefinition> = {
  bianco: {
    code: 'bianco',
    label: 'Bianco',
    priority: 'Non urgente',
    description: 'Problema che può essere gestito dal medico di base o in farmacia.',
    lowIntensity: true,
    cssVar: '--triage-bianco',
  },
  verde: {
    code: 'verde',
    label: 'Verde',
    priority: 'Urgenza minore',
    description: 'Nessun rischio evolutivo: adatto alle strutture territoriali.',
    lowIntensity: true,
    cssVar: '--triage-verde',
  },
  azzurro: {
    code: 'azzurro',
    label: 'Azzurro',
    priority: 'Urgenza differibile',
    description: 'Va valutato, ma può attendere. Spesso gestibile in casa della comunità.',
    lowIntensity: true,
    cssVar: '--triage-azzurro',
  },
  arancione: {
    code: 'arancione',
    label: 'Arancione',
    priority: 'Urgenza indifferibile',
    description: 'Rischio di peggioramento: pronto soccorso.',
    lowIntensity: false,
    cssVar: '--triage-arancione',
  },
  rosso: {
    code: 'rosso',
    label: 'Rosso',
    priority: 'Emergenza',
    description: 'Funzioni vitali compromesse: chiama il 118.',
    lowIntensity: false,
    cssVar: '--triage-rosso',
  },
};

/** Colore del codice come stringa CSS, pronta per `style`. */
export function triageColor(code: TriageCode): string {
  return `rgb(var(${TRIAGE_SCALE[code].cssVar}))`;
}

export const LOW_INTENSITY_CODES = TRIAGE_CODES.filter((code) => TRIAGE_SCALE[code].lowIntensity);

export type PressureLevel = 'basso' | 'medio' | 'alto';

/** Traduce una saturazione 0–1 in un livello di pressione, con lo stesso vocabolario cromatico. */
export function pressureFromRatio(ratio: number): { level: PressureLevel; cssVar: string } {
  if (ratio < 0.6) return { level: 'basso', cssVar: '--triage-verde' };
  if (ratio < 0.85) return { level: 'medio', cssVar: '--triage-arancione' };
  return { level: 'alto', cssVar: '--triage-rosso' };
}
