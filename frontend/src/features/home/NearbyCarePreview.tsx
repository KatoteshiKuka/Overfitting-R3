import { ErrorState } from '@/components/ErrorState';
import { NearbyFacilitiesMap } from '@/features/home/NearbyFacilitiesMap';
import { AddressForm } from '@/features/triage/AddressForm';
import { useNearbyFacilities } from '@/features/triage/useTriage';
import type { NearbyFacility } from '@/features/triage/types';
import { facilityTypeLabel } from '@/lib/facilityTypes';
import type { FacilityType } from '@/api/types';
import { useState } from 'react';

type NearbyCarePreviewProps = {
  onContinue: () => void;
  onBack: () => void;
};

export function NearbyCarePreview({ onContinue, onBack }: NearbyCarePreviewProps) {
  const nearby = useNearbyFacilities();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  function locate(address: string) {
    setSelectedId(null);
    nearby.mutate(address, {
      onSuccess: (data) => setSelectedId(data.facilities[0]?.facility_id ?? null),
    });
  }

  const selected =
    nearby.data?.facilities.find((facility) => facility.facility_id === selectedId) ?? null;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col py-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-accent">Prima dell’accesso</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">
            Scopri subito i servizi vicino a te
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
            Farmacie, Case della Comunità e ambulatori possono risolvere i bisogni meno urgenti
            senza passare dal pronto soccorso.
          </p>
        </div>
        <button
          type="button"
          onClick={onBack}
          className="min-h-11 rounded-xl border border-line px-4 text-sm text-muted hover:text-ink"
        >
          Indietro
        </button>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[minmax(18rem,2fr)_minmax(0,3fr)]">
        <section className="rounded-2xl border border-line bg-surface p-5">
          <AddressForm onSubmit={locate} pending={nearby.isPending} autoLocate />
          {nearby.isPending && (
            <p className="mt-4 text-sm text-muted" role="status">
              Cerco i servizi territoriali più vicini…
            </p>
          )}

          {selected && (
            <div className="mt-5 rounded-xl bg-raised p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-faint">Selezionato</p>
              <p className="mt-1 font-semibold text-ink">{selected.name}</p>
              <p className="mt-1 text-xs text-muted">
                {facilityTypeLabel(selected.type as FacilityType)} · {selected.distance_km} km
                {selected.municipality ? ` · ${selected.municipality}` : ''}
              </p>
              {selected.address && <p className="mt-2 text-xs text-faint">{selected.address}</p>}
            </div>
          )}
        </section>

        <section aria-label="Mappa dei servizi vicini" className="min-h-[23rem]">
          {nearby.isError && <ErrorState error={nearby.error} onRetry={() => nearby.reset()} />}
          {nearby.data ? (
            <div className="h-[23rem]">
              <NearbyFacilitiesMap
                data={nearby.data}
                selectedId={selectedId}
                onSelect={(facility: NearbyFacility) => setSelectedId(facility.facility_id)}
              />
            </div>
          ) : (
            !nearby.isError && (
              <div className="flex h-full min-h-[23rem] items-center justify-center rounded-2xl border border-dashed border-line px-8 text-center">
                <p className="max-w-sm text-sm leading-relaxed text-faint">
                  Il browser chiederà il permesso per mostrarti la mappa. La posizione serve solo
                  per questa ricerca e non viene salvata.
                </p>
              </div>
            )
          )}
        </section>
      </div>

      {nearby.data && (
        <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {nearby.data.facilities.map((facility) => (
            <button
              key={facility.facility_id}
              type="button"
              onClick={() => setSelectedId(facility.facility_id)}
              className={`min-w-52 rounded-xl border p-3 text-left ${
                selectedId === facility.facility_id
                  ? 'border-accent bg-accent-soft'
                  : 'border-line bg-surface'
              }`}
            >
              <span className="block truncate text-sm font-medium text-ink">{facility.name}</span>
              <span className="mt-1 block text-xs text-muted">
                {facilityTypeLabel(facility.type as FacilityType)} · {facility.distance_km} km
              </span>
            </button>
          ))}
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-line bg-raised p-4">
        <p className="max-w-xl text-xs leading-relaxed text-muted">
          Questa è una panoramica informativa. Il triage successivo valuterà sintomi, urgenza,
          tempi di viaggio, attesa e afflusso previsto.
        </p>
        <button
          type="button"
          onClick={onContinue}
          className="min-h-11 rounded-xl bg-accent px-5 text-sm font-medium text-white hover:opacity-90"
        >
          {nearby.data ? 'Continua e scegli il paziente' : 'Continua senza posizione'}
        </button>
      </div>
    </div>
  );
}
