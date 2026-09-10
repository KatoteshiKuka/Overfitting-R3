import { Card } from '@/components/Card';
import { TriageCodeBadge } from '@/components/TriageCodeBadge';
import type { Assessment } from '@/features/triage/types';
import { TRIAGE_SCALE } from '@/lib/triage';

type AssessmentPanelProps = {
  assessment: Assessment;
};

/** Esito del triage. Il codice rosso ha un trattamento a parte: lì la mappa non serve. */
export function AssessmentPanel({ assessment }: AssessmentPanelProps) {
  const definition = TRIAGE_SCALE[assessment.code];
  const isEmergency = assessment.code === 'rosso';

  return (
    <Card className="animate-fade-up overflow-hidden">
      <div
        className="h-1 w-full"
        style={{ backgroundColor: `rgb(var(${definition.cssVar}))` }}
        aria-hidden="true"
      />
      <div className="p-5">
        <div className="flex flex-wrap items-center gap-2">
          <TriageCodeBadge code={assessment.code} withPriority />
          {assessment.escalated && (
            <span
              className="rounded-full px-2.5 py-1 text-[11px] font-medium"
              style={{
                backgroundColor: 'rgb(var(--triage-arancione) / 0.12)',
                color: 'rgb(var(--triage-arancione))',
              }}
              title="Le regole di sicurezza hanno alzato il codice deciso dal modello"
            >
              gravità corretta al rialzo
            </span>
          )}
        </div>

        <p className="mt-3 text-sm leading-relaxed text-ink">{assessment.reason}</p>

        <div className="mt-4 rounded-xl bg-raised px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-faint">Dove andare</p>
          <p className="mt-1 text-[15px] font-semibold capitalize text-ink">
            {assessment.care_setting}
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-muted">{assessment.advice}</p>
        </div>

        {isEmergency && (
          <a
            href="tel:118"
            className="mt-4 flex min-h-12 items-center justify-center gap-2 rounded-xl text-sm font-semibold text-white"
            style={{ backgroundColor: 'rgb(var(--triage-rosso))' }}
          >
            Chiama subito il 118
          </a>
        )}

        {assessment.red_flags.length > 0 && (
          <p className="mt-3 text-xs text-faint">
            Sintomi rilevati come critici: {assessment.red_flags.join(', ')}.
          </p>
        )}
      </div>
    </Card>
  );
}
