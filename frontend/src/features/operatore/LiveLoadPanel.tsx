import { apiGet } from '@/api/client';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { ProvenanceTag } from '@/components/ProvenanceTag';
import { Skeleton } from '@/components/Skeleton';
import { CongestionForm } from '@/features/operatore/CongestionForm';
import type { CongestionSnapshot } from '@/features/operatore/types';
import { formatDateTime } from '@/lib/format';
import { useQuery } from '@tanstack/react-query';

/** Punto di ingresso del dato osservato che alimenta lo stesso ranking del cittadino. */
export function LiveLoadPanel({ facilityId }: { facilityId: number }) {
  const snapshot = useQuery({
    queryKey: ['congestion', facilityId],
    queryFn: () => apiGet<CongestionSnapshot>(`/congestion/${facilityId}`),
  });

  if (snapshot.isPending) {
    return (
      <Card className="p-5">
        <Skeleton count={2} />
      </Card>
    );
  }

  if (snapshot.isError) {
    return <ErrorState error={snapshot.error} onRetry={() => void snapshot.refetch()} />;
  }

  const provenance = snapshot.data.source === 'dichiarato' ? 'OBSERVED' : 'HISTORICAL';

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ink">Aggiorna il carico del pronto soccorso</h2>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            Inserisci la situazione rilevata adesso. Il nuovo dato aggiorna immediatamente la
            previsione interna e i suggerimenti mostrati ai cittadini.
          </p>
        </div>
        <div className="text-right">
          <ProvenanceTag value={provenance} />
          {snapshot.data.observed_at && (
            <p className="mt-1 text-[10px] text-faint">
              {formatDateTime(snapshot.data.observed_at)}
            </p>
          )}
        </div>
      </div>

      <CongestionForm snapshot={snapshot.data} />
    </Card>
  );
}
