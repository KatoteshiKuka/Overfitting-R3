import { apiGet, apiPost } from '@/api/client';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import { Skeleton } from '@/components/Skeleton';
import type { IncomingPatient } from '@/features/operatore/types';
import { formatDateTime } from '@/lib/format';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

function Value({ children }: { children: string | null | undefined }) {
  return children ? (
    <span className="text-sm text-ink">{children}</span>
  ) : (
    <span className="text-[11px] font-medium uppercase tracking-wide text-faint">Unavailable</span>
  );
}

/** Resoconti condivisi al momento della conferma, quindi disponibili prima dell'arrivo. */
export function IncomingPatientsPanel({ facilityId }: { facilityId: number }) {
  const queryClient = useQueryClient();
  const incoming = useQuery({
    queryKey: ['hospital', 'incoming', facilityId],
    queryFn: () => apiGet<IncomingPatient[]>('/hospital/incoming-patients'),
    refetchInterval: 15_000,
  });

  const checkIn = useMutation({
    mutationFn: (code: string) => apiPost<unknown>(`/admission/${code}/accept`, {}),
    onSuccess: async () => {
      await Promise.all([
        incoming.refetch(),
        queryClient.invalidateQueries({ queryKey: ['hospital', 'console', facilityId] }),
      ]);
    },
  });

  if (incoming.isPending) {
    return (
      <Card className="p-5">
        <Skeleton count={2} />
      </Card>
    );
  }

  if (incoming.isError) {
    return <ErrorState error={incoming.error} onRetry={() => void incoming.refetch()} />;
  }

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ink">Pazienti annunciati</h2>
          <p className="mt-1 max-w-3xl text-xs leading-relaxed text-muted">
            Il resoconto arriva quando il paziente conferma la destinazione: non serve aspettare il
            check-in. Sono visibili solo i profili che hanno scelto questa struttura.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ProvenanceTag value="SYNTHETIC" />
          <span className="rounded-full bg-raised px-2.5 py-1 text-xs font-semibold text-ink">
            {incoming.data.length}
          </span>
        </div>
      </div>

      {incoming.data.length === 0 ? (
        <p className="mt-4 rounded-xl bg-raised px-4 py-5 text-center text-sm text-faint">
          Nessun paziente ha ancora condiviso un resoconto con questa struttura.
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {incoming.data.map((patient) => {
            const arrived = patient.commitment_status === 'ARRIVED';
            const checkingThis = checkIn.isPending && checkIn.variables === patient.code;

            return (
              <li
                key={patient.commitment_id}
                className="rounded-2xl border border-line bg-raised p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold text-ink">
                      {patient.identity.given_name} {patient.identity.family_name}
                    </p>
                    <p className="mt-0.5 text-xs text-muted">
                      {arrived
                        ? 'Arrivo confermato dalla struttura'
                        : `Arrivo previsto ${formatDateTime(patient.expected_arrival_at)}`}
                    </p>
                  </div>
                  <span
                    className="rounded-full px-2.5 py-1 text-[11px] font-medium"
                    style={{
                      color: `rgb(var(--triage-${arrived ? 'verde' : 'azzurro'}))`,
                      backgroundColor: `rgb(var(--triage-${arrived ? 'verde' : 'azzurro'}) / 0.12)`,
                    }}
                  >
                    {arrived ? 'Arrivato' : 'In arrivo'}
                  </span>
                </div>

                {patient.triage_summary && (
                  <div className="mt-3 rounded-xl border border-line bg-surface p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-ink">
                        Valutazione preliminare HealthPulse
                      </p>
                      <span className="text-[10px] uppercase tracking-wide text-faint">
                        Codice suggerito {patient.triage_summary.priority_code} ·{' '}
                        {patient.triage_summary.provider} · non è una diagnosi
                      </span>
                    </div>
                    <p className="mt-2 text-sm font-medium text-ink">
                      {patient.triage_summary.reason}
                    </p>
                    <p className="mt-1 text-xs leading-relaxed text-muted">
                      {patient.triage_summary.advice}
                    </p>
                  </div>
                )}

                <dl className="mt-3 grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <dt className="text-faint">Codice fiscale</dt>
                    <dd className="tabular mt-0.5 text-ink">{patient.identity.fiscal_code}</dd>
                  </div>
                  <div>
                    <dt className="text-faint">Data di nascita</dt>
                    <dd className="mt-0.5 text-ink">{patient.identity.birth_date}</dd>
                  </div>
                  <div>
                    <dt className="text-faint">Telefono</dt>
                    <dd className="mt-0.5">
                      <Value>{patient.identity.mobile_phone}</Value>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faint">Email</dt>
                    <dd className="mt-0.5 break-all">
                      <Value>{patient.identity.email}</Value>
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-faint">Patologie croniche</dt>
                    <dd className="mt-0.5">
                      <Value>
                        {patient.clinical_context.chronic_conditions.length
                          ? patient.clinical_context.chronic_conditions.join(' · ')
                          : null}
                      </Value>
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-faint">Esenzioni</dt>
                    <dd className="mt-0.5">
                      <Value>
                        {patient.clinical_context.exemptions.length
                          ? patient.clinical_context.exemptions
                              .map((item) => `${item.code} ${item.description}`)
                              .join(' · ')
                          : null}
                      </Value>
                    </dd>
                  </div>
                </dl>

                {checkIn.isError && checkIn.variables === patient.code && (
                  <div className="mt-3">
                    <ErrorState error={checkIn.error} />
                  </div>
                )}

                {!arrived && (
                  <button
                    type="button"
                    onClick={() => checkIn.mutate(patient.code)}
                    disabled={checkIn.isPending}
                    className="mt-4 min-h-11 rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
                  >
                    {checkingThis ? 'Confermo…' : 'Conferma che è arrivato'}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <p className="mt-3 text-[11px] leading-relaxed text-faint">
        Il check-in aggiorna soltanto lo stato dell’arrivo. Non assegna il triage, non certifica la
        veridicità della persona e la mancata presentazione non produce penalità.
      </p>
    </Card>
  );
}
