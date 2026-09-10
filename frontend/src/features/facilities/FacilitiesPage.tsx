import type { FacilityType } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { FacilityCard } from '@/components/FacilityCard';
import { FilterChips, type ChipOption } from '@/components/FilterChips';
import { NoDataNotice } from '@/components/NoDataNotice';
import { EmptyState } from '@/components/EmptyState';
import { PageHeader } from '@/components/PageHeader';
import { SearchField } from '@/components/SearchField';
import { Skeleton } from '@/components/Skeleton';
import { useFacilities, useFacilitySummary } from '@/features/facilities/useFacilities';
import { facilityTypeLabel } from '@/lib/facilityTypes';
import { formatNumber } from '@/lib/format';
import { useDebouncedValue } from '@/lib/useDebouncedValue';
import { useState } from 'react';

const PAGE_SIZE = 30;

export function FacilitiesPage() {
  const [search, setSearch] = useState('');
  const [type, setType] = useState<FacilityType | ''>('');
  const debouncedSearch = useDebouncedValue(search, 250);

  const summary = useFacilitySummary();
  const facilities = useFacilities({ q: debouncedSearch, type, limit: PAGE_SIZE });

  // I contatori per tipologia arrivano dal riepilogo, così i chip dicono quanto c'è dietro.
  const typeOptions: ChipOption[] = (summary.data?.by_type ?? []).map((entry) => ({
    value: entry.type,
    label: facilityTypeLabel(entry.type),
    count: entry.count,
  }));

  const isEmptyCensus = summary.isSuccess && summary.data.total === 0;

  return (
    <div className="mx-auto w-full max-w-4xl">
      <PageHeader
        title="Presidi sanitari"
        description="Il censimento delle strutture del territorio, così come arriva dai dataset aperti della Regione."
      />

      {facilities.isError ? (
        <ErrorState error={facilities.error} onRetry={() => void facilities.refetch()} />
      ) : isEmptyCensus ? (
        <NoDataNotice />
      ) : (
        <>
          <div className="space-y-3">
            <SearchField
              label="Cerca un presidio"
              value={search}
              onChange={setSearch}
              placeholder="Cerca per nome, comune, indirizzo o ASL…"
            />
            <FilterChips
              label="Filtra per tipologia"
              options={typeOptions}
              value={type}
              onChange={(value) => setType(value as FacilityType | '')}
            />
          </div>

          <div className="mt-6">
            {facilities.isPending ? (
              <Skeleton count={4} />
            ) : facilities.data.total === 0 ? (
              <EmptyState
                title="Nessun presidio corrisponde"
                description="Prova con un altro termine di ricerca o rimuovi il filtro sulla tipologia."
              />
            ) : (
              <>
                <p className="tabular mb-3 text-xs text-faint">
                  {formatNumber(facilities.data.total)} risultati
                  {facilities.data.total > facilities.data.items.length &&
                    ` · primi ${facilities.data.items.length}`}
                </p>
                <ul className="space-y-3">
                  {facilities.data.items.map((facility) => (
                    <li key={facility.id} className="animate-fade-up">
                      <FacilityCard facility={facility} />
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
