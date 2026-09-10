import { useSystemStatus } from '@/lib/useSystemStatus';
import { formatNumber } from '@/lib/format';

/** Indicatore compatto: dice a colpo d'occhio se i dataset sono caricati. */
export function DataStatusPill() {
  const { data, isPending, isError } = useSystemStatus();

  const { cssVar, text } = (() => {
    if (isPending) return { cssVar: '--triage-bianco', text: 'Verifica dati…' };
    if (isError) return { cssVar: '--triage-rosso', text: 'Backend offline' };
    if (!data?.data_loaded) return { cssVar: '--triage-arancione', text: 'Dataset assenti' };
    return { cssVar: '--triage-verde', text: `${formatNumber(data.facilities_count)} presidi` };
  })();

  return (
    <span
      className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-medium text-muted"
      title="Stato dei dataset caricati dal backend"
    >
      <span
        aria-hidden="true"
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: `rgb(var(${cssVar}))` }}
      />
      <span className="tabular">{text}</span>
    </span>
  );
}
