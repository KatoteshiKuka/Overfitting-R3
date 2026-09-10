import { Card } from '@/components/Card';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import type { ConsoleOverview, PressureLevel } from '@/features/operatore/types';

const LEVEL_STYLE: Record<PressureLevel, { label: string; cssVar: string }> = {
  LOW: { label: 'Basso', cssVar: '--triage-verde' },
  MODERATE: { label: 'Moderato', cssVar: '--triage-azzurro' },
  HIGH: { label: 'Alto', cssVar: '--triage-arancione' },
  VERY_HIGH: { label: 'Molto alto', cssVar: '--triage-rosso' },
};

export function ReadinessPanel({ readiness }: { readiness: ConsoleOverview['readiness'] }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Aree da preparare</h2>
        <ProvenanceTag value="DERIVED" />
      </div>
      <p className="mt-1 text-xs text-muted">
        Dove potrebbe servire più supporto. È preparazione, non assegnazione di pazienti.
      </p>

      {readiness.length === 0 ? (
        <p className="mt-4 text-sm text-faint">
          Nessun arrivo confermato: niente da anticipare.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {readiness.map((entry) => {
            const style = LEVEL_STYLE[entry.level] ?? LEVEL_STYLE.MODERATE;
            return (
              <li
                key={entry.area}
                className="flex items-center justify-between gap-3 rounded-xl bg-raised px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">{entry.area}</p>
                  <p className="mt-0.5 text-[11px] text-faint">{entry.reason}</p>
                </div>
                <span
                  className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium"
                  style={{
                    color: `rgb(var(${style.cssVar}))`,
                    backgroundColor: `rgb(var(${style.cssVar}) / 0.12)`,
                  }}
                >
                  {style.label}
                </span>
              </li>
            );
          })}
        </ul>
      )}

      <p className="mt-4 text-[11px] leading-relaxed text-faint">
        Livelli in categorie e non in percentuali: dietro non c'è un modello validato, e un
        «85% previsto» darebbe una precisione che non abbiamo.
      </p>
    </Card>
  );
}
