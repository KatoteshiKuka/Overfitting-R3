import type { FacilityType } from '@/api/types';

export type FacilityTypeDefinition = {
  value: FacilityType;
  label: string;
  /** Cosa ci si può fare: è l'informazione che serve al cittadino, non la sigla burocratica. */
  hint: string;
};

/** Ordine di presentazione nei filtri: dal territorio verso l'ospedale. */
export const FACILITY_TYPES: FacilityTypeDefinition[] = [
  { value: 'farmacia', label: 'Farmacia', hint: 'Consigli, test rapidi, farmaci senza ricetta' },
  {
    value: 'casa-comunita',
    label: 'Casa della Comunità',
    hint: 'Medici e infermieri di prossimità, senza appuntamento',
  },
  { value: 'ambulatorio', label: 'Ambulatorio', hint: 'Visite e prestazioni su prenotazione' },
  { value: 'pronto-soccorso', label: 'Pronto Soccorso', hint: 'Urgenze e emergenze' },
  { value: 'ospedale', label: 'Ospedale', hint: 'Ricoveri e reparti specialistici' },
  { value: 'altro', label: 'Altro', hint: 'Struttura non classificata' },
];

const BY_VALUE = new Map(FACILITY_TYPES.map((type) => [type.value, type]));

export function facilityTypeLabel(value: FacilityType): string {
  return BY_VALUE.get(value)?.label ?? 'Altro';
}

export function facilityTypeHint(value: FacilityType): string {
  return BY_VALUE.get(value)?.hint ?? '';
}

/** Le strutture territoriali: l'alternativa da suggerire per i codici a bassa intensità. */
export const TERRITORIAL_TYPES: FacilityType[] = ['farmacia', 'casa-comunita', 'ambulatorio'];

export function isTerritorial(value: FacilityType): boolean {
  return TERRITORIAL_TYPES.includes(value);
}
