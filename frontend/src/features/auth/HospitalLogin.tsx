import { apiGet } from '@/api/client';
import type { FacilityList } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { useAuth } from '@/features/auth/useAuth';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

const ROLE_LABELS: Record<string, string> = {
  'hospital.admin': 'Direzione sanitaria',
  'ps.coordinator': 'Coordinamento PS',
  'reparto.lead': 'Responsabile di reparto',
  'sola.lettura': 'Consultazione (sola lettura)',
};

/**
 * Accesso del personale di struttura.
 *
 * Dominio separato da quello del cittadino: chi lavora in ospedale non entra con SPID,
 * e la sessione che ne risulta è un'altra cosa anche nel modello dati.
 */
export function HospitalLogin({ onBack }: { onBack: () => void }) {
  const { loginOperator } = useAuth();
  const [username, setUsername] = useState('ps.coordinator');
  const [facilityId, setFacilityId] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const facilities = useQuery({
    queryKey: ['facilities', 'pronto-soccorso', 'login'],
    queryFn: () =>
      apiGet<FacilityList>('/facilities', { type: 'pronto-soccorso', limit: 60 }),
  });

  const options = facilities.data?.items ?? [];
  const selected = facilityId ?? options[0]?.id ?? null;

  async function submit() {
    if (selected === null) return;
    setPending(true);
    setError(null);
    try {
      await loginOperator(username, selected);
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-8">
      <span className="self-center rounded-full border border-line bg-surface px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-faint">
        Accesso struttura · demo
      </span>
      <h1 className="mt-4 text-center text-2xl font-semibold tracking-tight text-ink">
        Console operativa
      </h1>
      <p className="mx-auto mt-2 max-w-sm text-center text-sm leading-relaxed text-muted">
        Account di servizio simulati. Il personale non accede con l'identità SPID del
        cittadino: sono due domini distinti.
      </p>

      {error !== null && (
        <div className="mt-5">
          <ErrorState error={error} />
        </div>
      )}

      <div className="mt-6 space-y-4 rounded-2xl border border-line bg-surface p-5">
        <div>
          <label htmlFor="op-role" className="block text-sm font-medium text-ink">
            Ruolo
          </label>
          <select
            id="op-role"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-ink focus:border-accent"
          >
            {Object.entries(ROLE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
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
              </option>
            ))}
          </select>
          {options.length === 0 && !facilities.isPending && (
            <p className="mt-1.5 text-xs text-faint">
              Nessun pronto soccorso nei dati caricati.
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={() => void submit()}
          disabled={pending || selected === null}
          className="min-h-11 w-full rounded-xl bg-accent text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {pending ? 'Accesso in corso…' : 'Entra'}
        </button>
      </div>

      <button
        type="button"
        onClick={onBack}
        className="mx-auto mt-6 min-h-11 text-sm text-muted transition-colors hover:text-ink"
      >
        ← Torna all'accesso cittadino
      </button>
    </div>
  );
}
