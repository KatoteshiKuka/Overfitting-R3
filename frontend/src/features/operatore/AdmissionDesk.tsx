import { apiGet, apiPost } from '@/api/client';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import { CLUSTER_LABELS } from '@/features/operatore/careMix';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

type PersonRef = {
  given_name: string;
  family_name: string;
  relationship: string | null;
  phone: string | null;
};

type Preadmission = {
  code: string;
  commitment_id: string;
  status: 'issued' | 'accepted' | 'expired';
  expires_at: string;
  triage_hint: null;
  care_cluster: string;
  facility_name: string | null;
  identity: {
    given_name: string;
    family_name: string;
    fiscal_code: string;
    birth_date: string;
    is_minor: boolean;
    guardian: PersonRef | null;
  };
  clinical_context: {
    exemptions: { code: string; description: string }[];
    chronic_conditions: string[];
    gp: PersonRef | null;
  };
  user_input: Record<string, string | null>;
};

/** Campo mancante: si dichiara, non si lascia una riga vuota. */
function Value({ children }: { children: string | null | undefined }) {
  if (!children) {
    return (
      <span className="text-[11px] font-medium uppercase tracking-wide text-faint">
        Unavailable
      </span>
    );
  }
  return <span className="text-sm text-ink">{children}</span>;
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-4 gap-y-0.5 py-2">
      <dt className="w-40 shrink-0 text-xs text-faint">{label}</dt>
      <dd className="min-w-0 flex-1">{children}</dd>
    </div>
  );
}

/**
 * Sportello di accettazione.
 *
 * L'operatore inserisce il codice che la persona mostra all'arrivo e vede quello che
 * serve a prenderla in carico: chi è, cosa ha già in anagrafe, chi contattare. Niente
 * di più — e in particolare **nessun codice di triage**: quello lo assegna il personale
 * dopo aver visto la persona, e anticiparlo qui significherebbe influenzarlo.
 */
export function AdmissionDesk() {
  const [code, setCode] = useState('');
  const [record, setRecord] = useState<Preadmission | null>(null);
  const queryClient = useQueryClient();

  const resolve = useMutation({
    mutationFn: (value: string) =>
      apiGet<Preadmission>(`/admission/resolve/${value.trim().toUpperCase()}`),
    onSuccess: setRecord,
  });

  const accept = useMutation({
    mutationFn: (value: string) => apiPost<Preadmission>(`/admission/${value}/accept`, {}),
    onSuccess: (data) => {
      setRecord(data);
      // L'accettazione toglie una persona dagli arrivi attesi: la console va rinfrescata.
      void queryClient.invalidateQueries({ queryKey: ['hospital', 'console'] });
    },
  });

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">Accettazione</h2>
        <ProvenanceTag value="SYNTHETIC" />
      </div>
      <p className="mt-1 text-xs text-muted">
        Inserisci il codice mostrato dalla persona per confermare soltanto che è arrivata. Il
        resoconto è già visibile sopra e non dipende da questo passaggio.
      </p>

      <form
        className="mt-3 flex flex-col gap-2 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          if (code.trim()) resolve.mutate(code);
        }}
      >
        <label htmlFor="admission-code" className="sr-only">
          Codice di pre-accettazione
        </label>
        <input
          id="admission-code"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="PA-XXXX-XX"
          className="tabular min-h-11 flex-1 rounded-xl border border-line bg-surface px-4 text-sm uppercase tracking-wider text-ink placeholder:normal-case placeholder:tracking-normal placeholder:text-faint focus:border-accent"
        />
        <button
          type="submit"
          disabled={resolve.isPending || !code.trim()}
          className="min-h-11 shrink-0 rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {resolve.isPending ? 'Cerco…' : 'Leggi codice'}
        </button>
      </form>

      {resolve.isError && (
        <div className="mt-3">
          <ErrorState error={resolve.error} />
        </div>
      )}

      {record && (
        <div className="mt-4 animate-fade-up rounded-xl border border-line bg-raised p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-base font-semibold text-ink">
              {record.identity.given_name} {record.identity.family_name}
            </p>
            <span
              className="rounded-full px-2.5 py-1 text-[11px] font-medium"
              style={
                record.status === 'accepted'
                  ? {
                      color: 'rgb(var(--triage-verde))',
                      backgroundColor: 'rgb(var(--triage-verde) / 0.12)',
                    }
                  : {
                      color: 'rgb(var(--triage-azzurro))',
                      backgroundColor: 'rgb(var(--triage-azzurro) / 0.12)',
                    }
              }
            >
              {record.status === 'accepted' ? 'accettato' : 'in attesa di accettazione'}
            </span>
          </div>

          <dl className="mt-3 divide-y divide-line">
            <Row label="Codice fiscale">
              <span className="tabular text-sm text-ink">{record.identity.fiscal_code}</span>
            </Row>
            <Row label="Data di nascita">
              <Value>{record.identity.birth_date}</Value>
              {record.identity.is_minor && (
                <span
                  className="ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium"
                  style={{
                    color: 'rgb(var(--triage-arancione))',
                    backgroundColor: 'rgb(var(--triage-arancione) / 0.12)',
                  }}
                >
                  minorenne
                </span>
              )}
            </Row>
            {record.identity.is_minor && (
              <Row label="Tutore">
                <Value>
                  {record.identity.guardian
                    ? `${record.identity.guardian.given_name} ${record.identity.guardian.family_name} · ${record.identity.guardian.phone ?? ''}`
                    : null}
                </Value>
              </Row>
            )}
            <Row label="Medico curante">
              <Value>
                {record.clinical_context.gp
                  ? `${record.clinical_context.gp.given_name} ${record.clinical_context.gp.family_name}`
                  : null}
              </Value>
            </Row>
            <Row label="Esenzioni">
              <Value>
                {record.clinical_context.exemptions.length > 0
                  ? record.clinical_context.exemptions
                      .map((e) => `${e.code} ${e.description}`)
                      .join(' · ')
                  : null}
              </Value>
            </Row>
            <Row label="Patologie croniche">
              <Value>
                {record.clinical_context.chronic_conditions.length > 0
                  ? record.clinical_context.chronic_conditions.join(' · ')
                  : null}
              </Value>
            </Row>
            <Row label="Recapito indicato">
              <Value>{record.user_input.contact_phone}</Value>
            </Row>
            <Row label="Tipo di accesso atteso">
              <span className="text-sm text-ink">
                {CLUSTER_LABELS[record.care_cluster] ?? record.care_cluster}
              </span>
            </Row>
            <Row label="Triage">
              <span className="text-[11px] font-medium uppercase tracking-wide text-faint">
                Da assegnare all'arrivo
              </span>
            </Row>
          </dl>

          {accept.isError && (
            <div className="mt-3">
              <ErrorState error={accept.error} />
            </div>
          )}

          {record.status !== 'accepted' && (
            <button
              type="button"
              onClick={() => accept.mutate(record.code)}
              disabled={accept.isPending}
              className="mt-4 min-h-11 w-full rounded-xl bg-accent text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              {accept.isPending ? 'Confermo…' : 'Conferma arrivo'}
            </button>
          )}
        </div>
      )}
    </Card>
  );
}
