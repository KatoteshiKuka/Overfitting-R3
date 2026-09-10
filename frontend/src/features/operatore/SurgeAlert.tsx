import type { ConsoleOverview, PressureLevel } from '@/features/operatore/types';

const STYLE: Record<PressureLevel, { cssVar: string; label: string }> = {
  LOW: { cssVar: '--triage-verde', label: 'Situazione gestibile' },
  MODERATE: { cssVar: '--triage-azzurro', label: 'Pressione in aumento' },
  HIGH: { cssVar: '--triage-arancione', label: 'Pressione alta' },
  VERY_HIGH: { cssVar: '--triage-rosso', label: 'Pressione molto alta' },
};

/**
 * Avviso che compare quando gli arrivi attesi cambiano il quadro.
 *
 * Sta in cima perché è l'unica cosa che chiede una decisione: tutto il resto della
 * console si consulta, questo si legge e si agisce. Resta però una **proposta** — il
 * numero di turni suggeriti non parte da solo, lo approva una persona.
 */
export function SurgeAlert({ data }: { data: ConsoleOverview }) {
  const level = data.expected_pressure_level;
  const style = STYLE[level] ?? STYLE.MODERATE;
  const suggested = data.staffing.deficit.reduce(
    (sum, entry) => sum + entry.additional_shifts_suggested,
    0,
  );

  // Sotto la soglia moderata non c'è niente da segnalare: un avviso sempre acceso
  // smette di essere un avviso.
  if (level === 'LOW' && suggested === 0) return null;

  const inbound = data.inbound.next_60_min;

  return (
    <div
      className="animate-fade-up mb-4 rounded-2xl border p-4"
      style={{
        borderColor: `rgb(var(${style.cssVar}) / 0.4)`,
        backgroundColor: `rgb(var(${style.cssVar}) / 0.07)`,
      }}
      role="status"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          aria-hidden="true"
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: `rgb(var(${style.cssVar}))` }}
        />
        <p className="text-sm font-semibold" style={{ color: `rgb(var(${style.cssVar}))` }}>
          {style.label}
        </p>
        <span className="text-[10px] font-medium uppercase tracking-wide text-faint">{level}</span>
      </div>

      <p className="mt-2 text-sm leading-relaxed text-ink">
        {inbound.commitments}{' '}
        {inbound.commitments === 1 ? 'arrivo confermato' : 'arrivi confermati'} nella prossima ora (
        {inbound.weighted} {inbound.weighted === 1 ? 'ponderato' : 'ponderati'})
        {data.care_mix.length > 0 && (
          <>
            , in prevalenza <strong>{data.care_mix[0]!.label.toLowerCase()}</strong>
          </>
        )}
        .{' '}
        {suggested > 0
          ? suggested === 1
            ? 'Servirebbe 1 turno aggiuntivo per reggere il carico previsto.'
            : `Servirebbero ${suggested} turni aggiuntivi per reggere il carico previsto.`
          : 'Il personale in turno è sufficiente per il carico previsto.'}
      </p>

      {suggested > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {data.staffing.deficit.map((entry) => (
            <li
              key={entry.qualification}
              className="rounded-full border border-line bg-surface px-3 py-1 text-xs text-ink"
            >
              <span className="tabular font-semibold">+{entry.additional_shifts_suggested}</span>{' '}
              {entry.qualification.toLowerCase()}
              <span className="text-faint"> · {entry.candidates_available} disponibili</span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-2.5 text-[11px] text-faint">
        Previsione basata su carico attuale + arrivi confermati. Gli stessi arrivi penalizzano
        questa struttura nel ranking dei cittadini successivi. Proposta da rivedere e approvare:
        HealthPulse non convoca nessuno.
      </p>
    </div>
  );
}
