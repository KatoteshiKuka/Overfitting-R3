import { apiGet } from '@/api/client';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import { Skeleton } from '@/components/Skeleton';
import { StatTile } from '@/components/StatTile';
import { HospitalLogin } from '@/features/auth/HospitalLogin';
import { InboundPanel } from '@/features/operatore/InboundPanel';
import { ReadinessPanel } from '@/features/operatore/ReadinessPanel';
import { StaffingPanel } from '@/features/operatore/StaffingPanel';
import type { ConsoleOverview } from '@/features/operatore/types';
import { useAuth } from '@/features/auth/useAuth';
import { formatDateTime, formatNumber } from '@/lib/format';
import { useQuery } from '@tanstack/react-query';

/**
 * Console operativa della struttura.
 *
 * Vista **aggregata**: nessun nome, nessun codice fiscale. Chi organizza un turno deve
 * sapere quanti arrivi aspettarsi e di che tipo, non chi sono le persone.
 */
export function OperatorePage() {
  const { state } = useAuth();

  const overview = useQuery({
    queryKey: ['hospital', 'console'],
    queryFn: () => apiGet<ConsoleOverview>('/hospital/console/overview'),
    // Il closed loop si deve vedere: la console si aggiorna da sola.
    refetchInterval: 15_000,
  });

  // La console mostra dati operativi di una struttura precisa: senza sapere chi sei e
  // dove lavori non c'è niente da mostrare. Il login avviene qui, non all'ingresso
  // dell'applicazione.
  if (state.status !== 'operator') {
    return <HospitalLogin />;
  }

  if (overview.isPending) {
    return (
      <div className="mx-auto w-full max-w-5xl py-6">
        <Skeleton count={4} />
      </div>
    );
  }

  if (overview.isError) {
    return (
      <div className="mx-auto w-full max-w-3xl py-6">
        <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />
      </div>
    );
  }

  const data = overview.data;

  return (
    <div className="mx-auto w-full max-w-6xl">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-ink">{data.facility.name}</h1>
          <p className="mt-0.5 text-sm text-muted">
            {state.session.operator.display_name} · {data.facility.municipality ?? 'Lazio'}
          </p>
        </div>
        <p className="text-xs text-faint">
          Aggiornata {formatDateTime(data.generated_at)}
        </p>
      </div>

      <section aria-label="Situazione attuale" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-line bg-surface px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-faint">Pressione</p>
            <ProvenanceTag value={data.pressure.provenance} />
          </div>
          <p className="tabular mt-1 text-2xl font-semibold capitalize text-ink">
            {data.pressure.level}
          </p>
          <p className="mt-0.5 text-xs text-muted">
            {data.pressure.waiting_total} in attesa · {data.pressure.in_treatment} in cura
          </p>
          {data.pressure.observed_at && (
            <p className="mt-0.5 text-[11px] text-faint">
              rilevata {formatDateTime(data.pressure.observed_at)}
            </p>
          )}
        </div>

        <StatTile
          label="In turno"
          value={formatNumber(data.staffing.on_shift)}
          hint={`${data.staffing.on_call} reperibili`}
        />
        <StatTile
          label="Attesi 60 min"
          value={formatNumber(data.inbound.next_60_min.commitments)}
          hint={`${data.inbound.next_60_min.weighted} ponderati`}
        />
        <div className="rounded-xl border border-line bg-surface px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-faint">Attesa</p>
            <ProvenanceTag value="DERIVED" />
          </div>
          <p className="tabular mt-1 text-2xl font-semibold text-ink">
            {data.expected_pressure_level}
          </p>
          <p className="mt-0.5 text-xs text-muted">pressione prevista</p>
        </div>
      </section>

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <InboundPanel inbound={data.inbound} careMix={data.care_mix} />
        <ReadinessPanel readiness={data.readiness} />
      </div>

      <div className="mt-4">
        <StaffingPanel staffing={data.staffing} />
      </div>

      <Card className="mt-4 p-4">
        <p className="text-xs leading-relaxed text-muted">
          Gli arrivi previsti derivano dalle conferme dei cittadini, pesate per stato
          (<code className="text-ink">{data.inbound.weight_formula}</code>): una conferma non è un
          arrivo certo. Il tipo di accesso è un raggruppamento di preparazione, non una
          diagnosi né un'assegnazione di reparto — <strong className="text-ink">chi arriva
          entra sempre dal pronto soccorso</strong> e il triage lo esegue il personale.
        </p>
      </Card>
    </div>
  );
}
