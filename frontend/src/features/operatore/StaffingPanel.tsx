import { Card } from '@/components/Card';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import type { ConsoleOverview } from '@/features/operatore/types';
import { useState } from 'react';

/**
 * Copertura dei turni.
 *
 * Il pulsante dice «Rivedi e approva», non «Attiva»: HealthPulse misura e propone, ma
 * chi convoca qualcuno è una persona. Nessuna chiamata parte da qui.
 */
export function StaffingPanel({ staffing }: { staffing: ConsoleOverview['staffing'] }) {
  const [reviewing, setReviewing] = useState(false);

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Copertura turni</h2>
        <div className="flex items-center gap-2">
          <ProvenanceTag value={staffing.provenance} />
          <span className="text-[10px] uppercase tracking-wide text-faint">
            {staffing.policy}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {[
          { label: 'In turno', value: staffing.on_shift },
          { label: 'Reperibili', value: staffing.on_call },
          { label: 'In riposo', value: staffing.resting },
        ].map((entry) => (
          <div key={entry.label} className="rounded-xl bg-raised px-3 py-2.5 text-center">
            <p className="text-[11px] font-medium uppercase tracking-wide text-faint">
              {entry.label}
            </p>
            <p className="tabular mt-0.5 text-xl font-semibold text-ink">{entry.value}</p>
          </div>
        ))}
      </div>

      {staffing.deficit.length > 0 ? (
        <>
          <h3 className="mt-5 text-xs font-medium uppercase tracking-wide text-faint">
            Turni aggiuntivi proposti
          </h3>
          <ul className="mt-2 space-y-2">
            {staffing.deficit.map((entry) => (
              <li
                key={entry.qualification}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-raised px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">
                    {entry.qualification} · {entry.additional_shifts_suggested} turni
                  </p>
                  <p className="mt-0.5 text-[11px] text-faint">
                    {entry.reason} · {entry.candidates_available} candidati eleggibili
                  </p>
                </div>
              </li>
            ))}
          </ul>

          <button
            type="button"
            onClick={() => setReviewing((current) => !current)}
            className="mt-3 min-h-11 rounded-xl border border-line px-4 text-sm text-ink transition-colors hover:border-accent/50"
          >
            Rivedi e approva
          </button>
          {reviewing && (
            <p className="mt-2 text-xs leading-relaxed text-muted">
              La proposta va valutata da un responsabile: HealthPulse non contatta nessuno
              e non assegna turni in automatico.
            </p>
          )}
        </>
      ) : (
        <p className="mt-4 text-sm text-faint">
          Nessun turno aggiuntivo proposto per la pressione attesa.
        </p>
      )}

      {staffing.excluded.length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-xs text-faint hover:text-muted">
            {staffing.excluded.length} persone escluse dai candidati
          </summary>
          <ul className="mt-2 space-y-1">
            {staffing.excluded.map((entry) => (
              <li key={entry.id} className="text-xs text-muted">
                <span className="tabular font-medium text-ink">{entry.id}</span> ·{' '}
                {entry.qualification} — {entry.exclusion_reason}
              </li>
            ))}
          </ul>
        </details>
      )}
    </Card>
  );
}
