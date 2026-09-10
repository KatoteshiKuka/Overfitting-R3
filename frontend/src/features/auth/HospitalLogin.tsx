import { apiGet } from '@/api/client';
import type { FacilityList } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { useAuth } from '@/features/auth/useAuth';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useState } from 'react';

const DEMO_OPERATOR = 'ps.coordinator';

/**
 * Accesso del personale di struttura.
 *
 * Dominio separato da quello del cittadino: chi lavora in ospedale non entra con SPID,
 * ed è giusto che l'aspetto sia diverso — sono due percorsi che non vanno confusi.
 */
type HospitalLoginProps = {
  onBack?: () => void;
  onDone?: () => void;
};

export function HospitalLogin({ onBack, onDone }: HospitalLoginProps = {}) {
  const { loginOperator } = useAuth();
  const [facilityId, setFacilityId] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const facilities = useQuery({
    queryKey: ['facilities', 'pronto-soccorso', 'login'],
    queryFn: () => apiGet<FacilityList>('/facilities', { type: 'pronto-soccorso', limit: 60 }),
  });

  const options = facilities.data?.items ?? [];
  const selected = facilityId ?? options[0]?.id ?? null;

  async function submit() {
    if (selected === null) return;
    setPending(true);
    setError(null);
    try {
      await loginOperator(DEMO_OPERATOR, selected);
      onDone?.();
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
      <div className="text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-faint">
          Accesso struttura · demo
        </span>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ink">Console operativa</h1>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-muted">
          Un solo profilo sintetico per la demo. Il personale non usa l’identità del cittadino: i
          due accessi restano separati.
        </p>
      </div>

      {error !== null && (
        <div className="mt-5">
          <ErrorState error={error} />
        </div>
      )}

      <div className="mt-6 space-y-4 rounded-2xl border border-line bg-surface p-5">
        <div className="flex items-center gap-3 rounded-xl bg-raised p-3">
          <span
            aria-hidden="true"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-accent text-xs font-semibold text-white"
          >
            EC
          </span>
          <span>
            <span className="block text-sm font-semibold text-ink">Dott.ssa Elisa Conti</span>
            <span className="block text-xs text-muted">Responsabile pronto soccorso · demo</span>
          </span>
        </div>

        <div>
          <label htmlFor="op-facility" className="block text-sm font-medium text-ink">
            Struttura
          </label>
          <select
            id="op-facility"
            value={selected ?? ''}
            disabled={facilities.isPending || options.length === 0}
            onChange={(event) => setFacilityId(Number(event.target.value))}
            className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-ink focus:border-accent disabled:opacity-60"
          >
            {options.map((facility) => (
              <option key={facility.id} value={facility.id}>
                {facility.name}
                {facility.municipality ? ` — ${facility.municipality}` : ''}
              </option>
            ))}
          </select>
          {options.length === 0 && !facilities.isPending && (
            <p className="mt-1.5 text-xs text-faint">Nessun pronto soccorso nei dati caricati.</p>
          )}
        </div>

        <button
          type="button"
          onClick={() => void submit()}
          disabled={pending || selected === null}
          className="min-h-11 w-full rounded-xl bg-accent text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {pending ? 'Accesso in corso…' : 'Entra nella console'}
        </button>
      </div>

      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="mx-auto mt-6 min-h-11 text-sm text-muted transition-colors hover:text-ink"
        >
          ← Indietro
        </button>
      ) : (
        <Link
          to="/"
          className="mx-auto mt-6 min-h-11 text-sm leading-[2.75rem] text-muted transition-colors hover:text-ink"
        >
          ← Torna alla scelta del ruolo
        </Link>
      )}
    </div>
  );
}
