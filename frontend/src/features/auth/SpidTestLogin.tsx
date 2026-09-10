import { apiGet } from '@/api/client';
import { ErrorState } from '@/components/ErrorState';
import { Skeleton } from '@/components/Skeleton';
import { useAuth } from '@/features/auth/useAuth';
import type { DemoDirectory } from '@/features/auth/types';
import { BRANDING } from '@/lib/branding';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { HospitalLogin } from '@/features/auth/HospitalLogin';

/**
 * Schermata di accesso.
 *
 * Le identità sono sintetiche e vengono mostrate esplicitamente: non è un login vero,
 * e nasconderlo dietro un finto modulo SPID darebbe l'impressione sbagliata. Non c'è
 * campo password perché non esiste alcuna password da verificare.
 */
export function SpidTestLogin() {
  const { loginCitizen } = useAuth();
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [showHospital, setShowHospital] = useState(false);

  const directory = useQuery({
    queryKey: ['auth', 'demo-identities'],
    queryFn: () => apiGet<DemoDirectory>('/auth/demo-identities'),
  });

  async function enter(username: string) {
    setPending(username);
    setError(null);
    try {
      await loginCitizen(username);
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(null);
    }
  }

  if (showHospital) {
    return <HospitalLogin onBack={() => setShowHospital(false)} />;
  }

  const heroes = (directory.data?.citizens ?? []).filter((row) => row.hero);
  const others = (directory.data?.citizens ?? []).filter((row) => !row.hero);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center py-8">
      <div className="text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-faint">
          Demo
        </span>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink">
          Accedi a {BRANDING.fullName}
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">
          Per questa demo vengono utilizzate esclusivamente identità sintetiche. Nessun dato
          appartiene a persone reali e non viene richiesta alcuna password.
        </p>
      </div>

      {error !== null && (
        <div className="mt-6">
          <ErrorState error={error} />
        </div>
      )}

      {directory.isPending && (
        <div className="mt-8">
          <Skeleton count={3} />
        </div>
      )}

      {directory.isError && (
        <div className="mt-8">
          <ErrorState error={directory.error} onRetry={() => void directory.refetch()} />
        </div>
      )}

      {directory.data && (
        <>
          <p className="mt-8 text-xs font-medium uppercase tracking-wide text-faint">
            Entra con SPID — ambiente di test
          </p>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {heroes.map((row) => (
              <li key={row.username}>
                <IdentityButton
                  identity={row}
                  pending={pending === row.username}
                  disabled={pending !== null}
                  onSelect={() => void enter(row.username)}
                />
              </li>
            ))}
          </ul>

          {others.length > 0 && (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs text-faint hover:text-muted">
                Altre {others.length} identità di test
              </summary>
              <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                {others.map((row) => (
                  <li key={row.username}>
                    <IdentityButton
                      identity={row}
                      pending={pending === row.username}
                      disabled={pending !== null}
                      onSelect={() => void enter(row.username)}
                    />
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}

      <div className="mt-8 border-t border-line pt-5 text-center">
        <button
          type="button"
          onClick={() => setShowHospital(true)}
          className="min-h-11 text-sm text-accent transition-opacity hover:opacity-80"
        >
          Accesso struttura →
        </button>
      </div>
    </div>
  );
}

function IdentityButton({
  identity,
  pending,
  disabled,
  onSelect,
}: {
  identity: DemoDirectory['citizens'][number];
  pending: boolean;
  disabled: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className="w-full rounded-xl border border-line bg-surface p-3 text-left transition-colors hover:border-accent/50 disabled:opacity-50"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium text-ink">{identity.display_name}</span>
        {identity.hero && (
          <span className="rounded-full bg-accent-soft px-2 py-0.5 text-[10px] font-medium text-accent-ink">
            HERO {identity.hero}
          </span>
        )}
      </div>
      <p className="mt-0.5 text-xs text-faint">{identity.care_intent}</p>
      {identity.note && (
        <p className="mt-1 text-[11px] text-muted">{identity.note}</p>
      )}
      {pending && <p className="mt-1 text-[11px] text-accent">Accesso in corso…</p>}
    </button>
  );
}
