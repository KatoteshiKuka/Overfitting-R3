import { Badge } from '@/components/Badge';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { Skeleton } from '@/components/Skeleton';
import { useFacility } from '@/features/facilities/useFacilities';
import { facilityTypeHint, facilityTypeLabel, isTerritorial } from '@/lib/facilityTypes';
import { joinParts } from '@/lib/format';
import { Link, useParams } from 'react-router-dom';

export function FacilityDetailPage() {
  const { facilityId } = useParams();
  const { data, isPending, isError, error, refetch } = useFacility(Number(facilityId));

  if (isPending) return <Skeleton count={2} />;
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />;

  const territorial = isTerritorial(data.type);
  const rows: { label: string; value: string }[] = [
    { label: 'Indirizzo', value: joinParts([data.address, data.postal_code, data.municipality]) },
    { label: 'Provincia', value: data.province ?? '' },
    { label: 'Azienda sanitaria', value: data.asl ?? '' },
    { label: 'Telefono', value: data.phone ?? '' },
    { label: 'Posti letto', value: data.beds !== null && data.beds > 0 ? String(data.beds) : '' },
    {
      label: 'Coordinate',
      value:
        data.latitude !== null && data.longitude !== null
          ? `${data.latitude.toFixed(5)}, ${data.longitude.toFixed(5)}`
          : '',
    },
    { label: 'Fonte', value: data.source },
  ].filter((row) => row.value !== '');

  return (
    <div className="mx-auto w-full max-w-3xl">
      <Link
        to="/presidi"
        className="mb-5 inline-flex min-h-11 items-center gap-1.5 text-sm text-muted transition-colors hover:text-ink"
      >
        <span aria-hidden="true">←</span> Tutti i presidi
      </Link>

      <div className="mb-6">
        <Badge cssVar={territorial ? '--triage-verde' : '--triage-arancione'}>
          {facilityTypeLabel(data.type)}
        </Badge>
        <h1 className="mt-3 text-2xl font-semibold leading-tight tracking-tight text-ink">
          {data.name}
        </h1>
        <p className="mt-1.5 text-sm text-muted">{facilityTypeHint(data.type)}</p>
      </div>

      <Card>
        <dl className="divide-y divide-line">
          {rows.map((row) => (
            <div key={row.label} className="flex flex-wrap gap-x-6 gap-y-1 px-4 py-3">
              <dt className="w-40 shrink-0 text-sm text-faint">{row.label}</dt>
              <dd className="tabular min-w-0 flex-1 text-sm text-ink">{row.value}</dd>
            </div>
          ))}
        </dl>
      </Card>

      {territorial && (
        <p
          className="mt-4 rounded-xl px-4 py-3 text-sm"
          style={{
            backgroundColor: 'rgb(var(--triage-verde) / 0.1)',
            color: 'rgb(var(--triage-verde))',
          }}
        >
          Struttura territoriale: adatta ai casi a bassa intensità, senza passare dal pronto
          soccorso.
        </p>
      )}
    </div>
  );
}
