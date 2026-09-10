type ProviderBadgeProps = {
  provider: string;
};

const LABELS: Record<string, { text: string; cssVar: string }> = {
  locale: { text: 'modello locale', cssVar: '--triage-verde' },
  groq: { text: 'Groq', cssVar: '--triage-azzurro' },
  regole: { text: 'regole di sicurezza', cssVar: '--triage-arancione' },
};

/** Dice sempre chi ha prodotto la risposta: su un consiglio sanitario la provenienza conta. */
export function ProviderBadge({ provider }: ProviderBadgeProps) {
  const entry = LABELS[provider] ?? { text: provider, cssVar: '--triage-bianco' };

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] text-faint"
      title="Da dove arriva questa risposta"
    >
      <span
        aria-hidden="true"
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: `rgb(var(${entry.cssVar}))` }}
      />
      {entry.text}
    </span>
  );
}
