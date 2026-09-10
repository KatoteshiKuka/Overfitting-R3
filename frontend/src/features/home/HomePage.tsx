import { StatTile } from '@/components/StatTile';
import { useFacilitySummary } from '@/features/facilities/useFacilities';
import { EntryCard } from '@/features/home/EntryCard';
import { TriageScale } from '@/features/home/TriageScale';
import { BRANDING } from '@/lib/branding';
import { formatDateTime, formatNumber } from '@/lib/format';
import { useSystemStatus } from '@/lib/useSystemStatus';

export function HomePage() {
  const status = useSystemStatus();
  const summary = useFacilitySummary();

  const facilitiesDataset = status.data?.datasets.find((dataset) => dataset.name === 'facilities');

  return (
    <>
      <section className="animate-fade-up">
        <p className="text-sm font-medium text-accent">{BRANDING.tagline}</p>
        <h1 className="mt-2 text-[2rem] font-semibold leading-[1.15] tracking-tight text-ink sm:text-4xl">
          {BRANDING.claim}
        </h1>
        <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-muted">
          {BRANDING.subclaim}
        </p>
      </section>

      <section aria-label="Sezioni principali" className="mt-8 grid gap-3 sm:grid-cols-3">
        <EntryCard
          to="/presidi"
          icon="facilities"
          title="Presidi sanitari"
          description="Cerca e filtra le strutture del territorio: pronto soccorso, case della comunità, farmacie, ambulatori."
        />
        <EntryCard
          to="/feature-a"
          icon="slot"
          title="Feature A"
          description="Slot libero, già collegato all'app. Verrà scelto e sviluppato dal team."
          pending
        />
        <EntryCard
          to="/feature-b"
          icon="slot"
          title="Feature B"
          description="Slot libero, già collegato all'app. Verrà scelto e sviluppato dal team."
          pending
        />
      </section>

      <section aria-label="Stato dei dati" className="mt-8">
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile
            label="Presidi"
            value={summary.data ? formatNumber(summary.data.total) : '—'}
            hint="strutture censite"
          />
          <StatTile
            label="Aziende"
            value={status.data ? formatNumber(status.data.asl_count) : '—'}
            hint="ASL coperte"
          />
          <StatTile
            label="Comuni"
            value={summary.data ? formatNumber(summary.data.municipalities) : '—'}
            hint="territori raggiunti"
          />
          <StatTile
            label="Dati"
            value={facilitiesDataset ? formatNumber(facilitiesDataset.files) : '—'}
            hint={`aggiornati ${formatDateTime(facilitiesDataset?.last_loaded_at ?? null)}`}
          />
        </div>
        <p className="mt-3 text-xs text-faint">
          Fonte: Portale Open Data Regione Lazio. I file caricati stanno in{' '}
          <code>data/facilities/</code>.
        </p>
      </section>

      <TriageScale />
    </>
  );
}
