import { apiGet } from '@/api/client';
import { ErrorState } from '@/components/ErrorState';
import { SpidMark } from '@/features/auth/SpidMark';
import type { DemoDirectory } from '@/features/auth/types';
import { useAuth } from '@/features/auth/useAuth';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

const SPID_BLUE = '#06c';

type SpidLoginPanelProps = {
  title: string;
  description: string;
  /** Chiamata dopo un accesso riuscito, per proseguire da dove si era rimasti. */
  onDone?: () => void;
  onBack?: () => void;
};

/** Accesso one-click scegliendo una delle identità interamente sintetiche. */
export function SpidLoginPanel({ title, description, onDone, onBack }: SpidLoginPanelProps) {
  const { loginCitizen } = useAuth();
  const [username, setUsername] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const directory = useQuery({
    queryKey: ['auth', 'demo-identities'],
    queryFn: () => apiGet<DemoDirectory>('/auth/demo-identities'),
  });
  const identities = directory.data?.citizens ?? [];
  const selectedUsername = username ?? identities[0]?.username ?? '';
  const selectedIdentity = identities.find((identity) => identity.username === selectedUsername);

  async function enter() {
    if (!selectedUsername) return;
    setPending(true);
    setError(null);
    try {
      await loginCitizen(selectedUsername);
      onDone?.();
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          <p className="mt-1 text-sm leading-relaxed text-muted">{description}</p>
        </div>
        <span className="shrink-0 rounded-full border border-line px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-faint">
          Demo
        </span>
      </div>

      {(error !== null || directory.isError) && (
        <div className="mt-4">
          <ErrorState error={error ?? directory.error} />
        </div>
      )}

      <div className="mt-4">
        <label htmlFor="demo-patient" className="block text-sm font-medium text-ink">
          Paziente mock
        </label>
        <select
          id="demo-patient"
          value={selectedUsername}
          disabled={directory.isPending || identities.length === 0}
          onChange={(event) => setUsername(event.target.value)}
          className="mt-1.5 min-h-11 w-full rounded-xl border border-line bg-surface px-3 text-sm text-ink focus:border-accent disabled:opacity-60"
        >
          {identities.map((identity) => (
            <option key={identity.username} value={identity.username}>
              {identity.display_name}
            </option>
          ))}
        </select>
        {selectedIdentity && (
          <div className="mt-3 rounded-xl bg-raised p-3">
            <p className="text-sm font-semibold text-ink">{selectedIdentity.display_name}</p>
            <p className="mt-0.5 text-xs text-muted">
              {selectedIdentity.hero
                ? `Scenario demo ${selectedIdentity.hero}`
                : 'Profilo sanitario sintetico'}
              {selectedIdentity.note ? ` · ${selectedIdentity.note}` : ''}
            </p>
          </div>
        )}
        {identities.length === 0 && !directory.isPending && !directory.isError && (
          <p className="mt-1.5 text-xs text-faint">Nessun paziente mock disponibile.</p>
        )}
      </div>

      <button
        type="button"
        onClick={() => void enter()}
        disabled={pending || directory.isPending || !selectedUsername}
        style={{ backgroundColor: SPID_BLUE }}
        className="mt-3 flex min-h-11 w-full items-center justify-center gap-2.5 rounded-lg px-5 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        <SpidMark />
        {pending ? 'Accesso in corso…' : 'Entra come paziente'}
      </button>
      <p className="mt-2 text-center text-[11px] text-faint">
        Identità sintetica per la dimostrazione; nessuna autenticazione reale.
      </p>

      {onBack && (
        <button
          type="button"
          onClick={onBack}
          className="mx-auto mt-4 block min-h-11 text-sm text-muted transition-colors hover:text-ink"
        >
          ← Indietro
        </button>
      )}
    </div>
  );
}
