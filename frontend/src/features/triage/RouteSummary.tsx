import { CONGESTION_COLORS, CONGESTION_LABELS, formatMinutes } from '@/features/triage/congestion';
import type { PlanOption } from '@/features/triage/types';

type RouteSummaryProps = {
  option: PlanOption;
  /** Perché la struttura più vicina non è quella consigliata, quando succede. */
  crowdingNote?: string | null;
};

/**
 * I due numeri che contano davvero, affiancati e sommati: quanto ci metti ad arrivare
 * e quanto aspetti una volta lì. Tenerli separati è il punto dell'app — un pronto
 * soccorso vicino ma pieno può costare più di uno lontano e scarico.
 */
export function RouteSummary({ option, crowdingNote }: RouteSummaryProps) {
  const cssVar = CONGESTION_COLORS[option.congestion_level];

  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-faint">
        Struttura consigliata
      </p>
      <h3 className="mt-1 text-lg font-semibold leading-tight text-ink">{option.name}</h3>
      {option.address && (
        <p className="mt-0.5 text-sm text-muted">
          {option.address}
          {option.municipality ? ` · ${option.municipality}` : ''}
        </p>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Metric
          label="Viaggio"
          value={formatMinutes(option.travel_minutes)}
          hint={`${option.distance_km} km`}
        />
        <Metric
          label="Attesa attuale"
          value={formatMinutes(option.waiting_minutes)}
          hint={CONGESTION_LABELS[option.congestion_level]}
          cssVar={cssVar}
        />
        <Metric
          label="Arrivi previsti"
          value={formatMinutes(option.inbound_wait_minutes)}
          hint={
            option.inbound_people > 0
              ? `${option.inbound_people} persone già confermate`
              : 'nessuna conferma attiva'
          }
          cssVar="--triage-azzurro"
        />
        <Metric label="Totale" value={formatMinutes(option.total_minutes)} strong />
      </div>

      <p className="mt-2 text-[11px] leading-relaxed text-faint">
        Totale = viaggio + attesa attuale + impatto degli arrivi che HealthPulse ha già indirizzato
        qui. Le nuove raccomandazioni usano questo totale, così non mandano tutti nello stesso
        pronto soccorso.
      </p>

      {crowdingNote && (
        <p
          className="mt-4 rounded-xl px-3 py-2.5 text-xs leading-relaxed"
          style={{
            backgroundColor: 'rgb(var(--triage-azzurro) / 0.1)',
            color: 'rgb(var(--triage-azzurro))',
          }}
        >
          {crowdingNote}
        </p>
      )}

      <p className="mt-4 text-xs leading-relaxed text-faint">
        {option.route_source === 'osrm'
          ? 'Tragitto in auto calcolato su OpenStreetMap.'
          : 'Tragitto stimato in linea d’aria: il servizio di navigazione non ha risposto.'}{' '}
        L’attesa è calcolata sulle persone in coda davanti a te, per il tuo codice.
        {option.geo_precision === 'comune' && (
          <>
            {' '}
            La posizione esatta di questa struttura non è nei dati aperti: è collocata al centro del
            comune, quindi distanza e tempi sono indicativi.
          </>
        )}
      </p>
    </div>
  );
}

function Metric({
  label,
  value,
  hint,
  cssVar,
  strong = false,
}: {
  label: string;
  value: string;
  hint?: string;
  cssVar?: string;
  strong?: boolean;
}) {
  return (
    <div className={`rounded-xl px-2 py-2 text-center ${strong ? 'bg-accent-soft' : 'bg-raised'}`}>
      <p className="text-[11px] font-medium uppercase tracking-wide text-faint">{label}</p>
      <p
        className={`tabular mt-0.5 font-semibold leading-tight ${strong ? 'text-xl text-accent-ink' : 'text-lg text-ink'}`}
        style={cssVar && !strong ? { color: `rgb(var(${cssVar}))` } : undefined}
      >
        {value}
      </p>
      {hint && <p className="mt-0.5 truncate text-[11px] text-faint">{hint}</p>}
    </div>
  );
}
