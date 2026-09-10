import { Card } from '@/components/Card';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import type { ConsoleOverview } from '@/features/operatore/types';

type InboundPanelProps = {
  inbound: ConsoleOverview['inbound'];
  careMix: ConsoleOverview['care_mix'];
};

export function InboundPanel({ inbound, careMix }: InboundPanelProps) {
  const windows: { label: string; value: ConsoleOverview['inbound']['next_30_min'] }[] = [
    { label: '30 min', value: inbound.next_30_min },
    { label: '60 min', value: inbound.next_60_min },
    { label: '4 ore', value: inbound.next_4_hours },
  ];

  const total = careMix.reduce((sum, entry) => sum + entry.count, 0);

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Arrivi confermati da HealthPulse</h2>
        <ProvenanceTag value={inbound.provenance} />
      </div>
      <p className="mt-1 text-xs text-muted">
        Persone che hanno dichiarato di dirigersi qui. Non sostituisce la domanda esterna.
      </p>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {windows.map((entry) => (
          <div key={entry.label} className="rounded-xl bg-raised px-3 py-2.5 text-center">
            <p className="text-[11px] font-medium uppercase tracking-wide text-faint">
              {entry.label}
            </p>
            <p className="tabular mt-0.5 text-2xl font-semibold text-ink">
              {entry.value.commitments}
            </p>
            <p className="tabular mt-0.5 text-[11px] text-muted">
              {entry.value.weighted} ponderati
            </p>
          </div>
        ))}
      </div>

      <h3 className="mt-5 text-xs font-medium uppercase tracking-wide text-faint">
        Tipo di accesso atteso
      </h3>
      {careMix.length === 0 ? (
        <p className="mt-2 text-sm text-faint">
          Nessun arrivo confermato in questo momento.
        </p>
      ) : (
        <ul className="mt-2 space-y-2">
          {careMix.map((entry) => (
            <li key={entry.cluster}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="text-ink">{entry.label}</span>
                <span className="tabular text-muted">{entry.count}</span>
              </div>
              <div
                className="mt-1 h-1.5 overflow-hidden rounded-full bg-raised"
                role="presentation"
              >
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${total > 0 ? (entry.count / total) * 100 : 0}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
