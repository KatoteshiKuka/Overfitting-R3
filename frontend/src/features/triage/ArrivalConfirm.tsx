import { apiGet, apiPost } from '@/api/client';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { QrCode } from '@/components/QrCode';
import { SpidLoginPanel } from '@/features/auth/SpidLoginPanel';
import { useAuth } from '@/features/auth/useAuth';
import { formatMinutes } from '@/features/triage/congestion';
import type { Assessment, PlanOption } from '@/features/triage/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

type Commitment = {
  commitment_id: string;
  facility_id: number;
  facility_name: string | null;
  status: string;
  eta_minutes: number;
  expected_arrival_at: string;
};

type CommitmentList = {
  items: Commitment[];
  total: number;
};

type Preadmission = {
  code: string;
  expires_at: string;
  triage_hint: null;
};

type ArrivalConfirmProps = {
  option: PlanOption;
  assessment: Assessment;
  provider: string;
};

/**
 * Conferma della destinazione e pre-accettazione.
 *
 * Nulla parte in automatico dopo un consiglio: la struttura viene avvisata solo se la
 * persona preme il pulsante. Ed è sempre revocabile, senza alcuna conseguenza — non
 * esiste nessun punteggio, nessuna segnalazione per chi cambia idea.
 */
export function ArrivalConfirm({ option, assessment, provider }: ArrivalConfirmProps) {
  const { state } = useAuth();
  const queryClient = useQueryClient();
  const [preadmission, setPreadmission] = useState<Preadmission | null>(null);
  const [phone, setPhone] = useState('');
  const citizenId = state.status === 'citizen' ? state.session.profile.fiscalNumber : null;
  const mineQueryKey = ['arrivals', 'mine', citizenId] as const;

  const mine = useQuery({
    queryKey: mineQueryKey,
    queryFn: () => apiGet<CommitmentList>('/arrivals/commitments/mine'),
    enabled: citizenId !== null,
  });

  useEffect(() => {
    setPreadmission(null);
    setPhone('');
  }, [citizenId]);

  const activeCommitment = mine.data?.items.find(
    (item) => item.status === 'CONFIRMED' || item.status === 'EN_ROUTE',
  );
  const restoredCommitment =
    activeCommitment?.facility_id === option.facility_id ? activeCommitment : null;
  const conflictingCommitment =
    activeCommitment && activeCommitment.facility_id !== option.facility_id
      ? activeCommitment
      : null;
  const commitment = restoredCommitment;

  const prepare = useMutation({
    mutationFn: ({ id, contactPhone }: { id: string; contactPhone: string | null }) =>
      apiPost<Preadmission>('/navigation/preadmission', {
        commitment_id: id,
        contact_phone: contactPhone,
        triage_summary: {
          priority_code: assessment.code,
          reason: assessment.reason.slice(0, 500),
          advice: assessment.advice.slice(0, 500),
          provider: provider || 'regole',
          provisional: true,
        },
        consents: {
          share_arrival: true,
          share_preadmission: true,
          share_reason: true,
        },
      }),
    onSuccess: setPreadmission,
  });

  const confirm = useMutation({
    mutationFn: () =>
      apiPost<Commitment>('/arrivals/commitments', {
        facility_id: option.facility_id,
        eta_minutes: option.travel_minutes,
        care_intent: assessment.care_setting,
        consents: {
          share_arrival: true,
          share_preadmission: true,
          share_reason: true,
        },
      }),
    onSuccess: (created) => {
      queryClient.setQueryData<CommitmentList>(mineQueryKey, (current) => ({
        items: [created, ...(current?.items ?? [])],
        total: (current?.total ?? 0) + 1,
      }));
      prepare.mutate({ id: created.commitment_id, contactPhone: null });
    },
  });

  const cancel = useMutation({
    mutationFn: (id: string) => apiPost<Commitment>(`/arrivals/commitments/${id}/cancel`, {}),
    onSuccess: (cancelled) => {
      setPreadmission(null);
      queryClient.setQueryData<CommitmentList>(mineQueryKey, (current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.commitment_id === cancelled.commitment_id ? cancelled : item,
              ),
            }
          : current,
      );
    },
  });

  // L'identità serve solo da qui in avanti: per avvisare la struttura bisogna sapere
  // chi sta arrivando. Tutto quello che viene prima — sintomi, codice, mappa — resta
  // accessibile senza autenticarsi.
  if (state.status !== 'citizen') {
    return (
      <SpidLoginPanel
        title="Per confermare serve la tua identità"
        description={`La struttura deve sapere chi sta arrivando. Fin qui non ti abbiamo chiesto nulla: l'accesso serve solo per avvisare ${option.name}.`}
      />
    );
  }

  if (mine.isError) {
    return (
      <Card className="p-5">
        <ErrorState error={mine.error} />
        <button
          type="button"
          onClick={() => void mine.refetch()}
          className="mt-3 min-h-11 text-sm font-medium text-accent-ink hover:underline"
        >
          Riprova
        </button>
      </Card>
    );
  }

  if (conflictingCommitment) {
    return (
      <Card className="border-amber-300/60 p-5">
        <h3 className="text-sm font-semibold text-ink">Hai già una destinazione attiva</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          Risulti in viaggio verso {conflictingCommitment.facility_name ?? 'un’altra struttura'}.
          Per evitare di comunicare due arrivi contemporanei, annulla prima quella destinazione.
        </p>
        {cancel.isError && (
          <div className="mt-3">
            <ErrorState error={cancel.error} />
          </div>
        )}
        <button
          type="button"
          onClick={() => cancel.mutate(conflictingCommitment.commitment_id)}
          disabled={cancel.isPending}
          className="mt-4 min-h-11 w-full rounded-xl border border-line px-5 text-sm font-medium text-ink transition-colors hover:border-accent/50 disabled:opacity-40"
        >
          {cancel.isPending ? 'Annullo…' : 'Annulla la destinazione precedente'}
        </button>
      </Card>
    );
  }

  if (commitment === null) {
    return (
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-ink">Ti stai dirigendo qui?</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          Se confermi, condividi con questa struttura il tuo profilo sintetico e la valutazione
          preliminare mostrata sopra. Puoi annullare in qualsiasi momento, senza conseguenze.
        </p>

        {confirm.isError && (
          <div className="mt-3">
            <ErrorState error={confirm.error} />
          </div>
        )}

        <button
          type="button"
          onClick={() => confirm.mutate()}
          disabled={confirm.isPending || mine.isPending}
          className="mt-4 min-h-11 w-full rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {mine.isPending
            ? 'Verifico le destinazioni…'
            : confirm.isPending
              ? 'Invio…'
              : 'Confermo che mi sto dirigendo qui'}
        </button>
      </Card>
    );
  }

  return (
    <Card className="animate-fade-up overflow-hidden">
      <div
        className="h-1 w-full"
        style={{ backgroundColor: 'rgb(var(--triage-verde))' }}
        aria-hidden="true"
      />
      <div className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-ink">Destinazione confermata</h3>
          <span
            className="rounded-full px-2.5 py-1 text-[11px] font-medium"
            style={{
              color: 'rgb(var(--triage-verde))',
              backgroundColor: 'rgb(var(--triage-verde) / 0.12)',
            }}
          >
            {commitment.status}
          </span>
        </div>
        <p className="mt-1.5 text-sm text-muted">
          {commitment.facility_name} · arrivo previsto tra {formatMinutes(commitment.eta_minutes)}
        </p>

        {preadmission === null ? (
          <div className="mt-4 rounded-xl bg-raised p-4">
            <p className="text-sm font-medium text-ink">
              {prepare.isPending ? 'Invio il resoconto alla struttura…' : 'Invia il resoconto'}
            </p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              L’ospedale vedrà i dati prima del tuo arrivo. Puoi aggiungere un recapito oppure
              riprovare senza inserirlo.
            </p>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <label htmlFor="contact-phone" className="sr-only">
                Recapito telefonico
              </label>
              <input
                id="contact-phone"
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="Recapito (facoltativo)"
                className="min-h-11 flex-1 rounded-xl border border-line bg-surface px-4 text-sm text-ink placeholder:text-faint focus:border-accent"
              />
              <button
                type="button"
                onClick={() =>
                  prepare.mutate({
                    id: commitment.commitment_id,
                    contactPhone: phone.trim() || null,
                  })
                }
                disabled={prepare.isPending}
                className="min-h-11 shrink-0 rounded-xl border border-accent px-4 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-soft disabled:opacity-40"
              >
                {prepare.isPending ? 'Invio…' : 'Invia e genera QR'}
              </button>
            </div>
            {prepare.isError && (
              <div className="mt-3">
                <ErrorState error={prepare.error} />
              </div>
            )}
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-accent/40 bg-accent-soft p-4 text-center">
            <p className="text-xs font-medium uppercase tracking-wide text-accent-ink">
              Pre-accettazione pronta
            </p>
            <div className="mt-3 flex justify-center">
              <QrCode
                value={preadmission.code}
                label={`Codice di accettazione ${preadmission.code}`}
              />
            </div>
            <p className="mt-3 text-xs leading-relaxed text-accent-ink/80">
              Il resoconto è già visibile alla struttura. Il QR serve solo a confermare il tuo
              arrivo; il triage resta responsabilità del personale e non ci sono penalità se cambi
              idea.
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={() => cancel.mutate(commitment.commitment_id)}
          disabled={cancel.isPending}
          className="mt-4 min-h-11 text-sm text-muted underline-offset-2 transition-colors hover:text-ink hover:underline disabled:opacity-40"
        >
          {cancel.isPending ? 'Annullo…' : 'Ho cambiato idea, annulla'}
        </button>
      </div>
    </Card>
  );
}
