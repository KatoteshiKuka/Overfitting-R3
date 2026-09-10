import { apiGet } from '@/api/client';
import { ErrorState } from '@/components/ErrorState';
import { Skeleton } from '@/components/Skeleton';
import { SpidMark } from '@/features/auth/SpidMark';
import type { DemoDirectory, DemoIdentity } from '@/features/auth/types';
import { useAuth } from '@/features/auth/useAuth';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

// Blu istituzionale del pulsante SPID. Vive qui e non fra i token di tema perché non è
// un colore dell'applicazione: appartiene al sistema di identità.
const SPID_BLUE = '#06c';
const SPID_BLUE_DARK = '#04a';

type SpidLoginPanelProps = {
  title: string;
  description: string;
  /** Chiamata dopo un accesso riuscito, per proseguire da dove si era rimasti. */
  onDone?: () => void;
};

/**
 * Accesso del cittadino, nello stile del pulsante SPID.
 *
 * Ricalca il flusso vero — si preme «Entra con SPID» e si sceglie l'identità — ma le
 * identità sono sintetiche e non c'è nessuna password: dichiararlo apertamente è più
 * onesto che simulare un modulo di autenticazione che non autentica niente.
 */
export function SpidLoginPanel({ title, description, onDone }: SpidLoginPanelProps) {
  const { loginCitizen } = useAuth();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  const directory = useQuery({
    queryKey: ['auth', 'demo-identities'],
    queryFn: () => apiGet<DemoDirectory>('/auth/demo-identities'),
    enabled: open,
  });

  async function enter(username: string) {
    setPending(username);
    setError(null);
    try {
      await loginCitizen(username);
      onDone?.();
    } catch (caught) {
      setError(caught);
    } finally {
      setPending(null);
    }
  }

  const heroes = (directory.data?.citizens ?? []).filter((row) => row.hero);
  const others = (directory.data?.citizens ?? []).filter((row) => !row.hero);

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

      {!open ? (
        <>
          <button
            type="button"
            onClick={() => setOpen(true)}
            style={{ backgroundColor: SPID_BLUE }}
            className="mt-4 flex min-h-11 w-full items-center justify-center gap-2.5 rounded-lg px-5 text-sm font-semibold text-white transition-colors hover:brightness-110"
            onMouseDown={(event) => {
              event.currentTarget.style.backgroundColor = SPID_BLUE_DARK;
            }}
            onMouseUp={(event) => {
              event.currentTarget.style.backgroundColor = SPID_BLUE;
            }}
          >
            <SpidMark />
            Entra con SPID
          </button>
          <p className="mt-2 text-center text-[11px] text-faint">
            Ambiente di test · solo identità sintetiche
          </p>
        </>
      ) : (
        <div className="mt-4">
          <div
            className="flex items-center gap-2 rounded-t-lg px-4 py-2.5 text-sm font-semibold text-white"
            style={{ backgroundColor: SPID_BLUE }}
          >
            <SpidMark className="h-4 w-4" />
            Scegli l'identità di test
          </div>

          <div className="rounded-b-lg border border-t-0 border-line p-3">
            {error !== null && (
              <div className="mb-3">
                <ErrorState error={error} />
              </div>
            )}

            {directory.isPending && <Skeleton count={2} />}

            {directory.isError && (
              <ErrorState error={directory.error} onRetry={() => void directory.refetch()} />
            )}

            {directory.data && (
              <>
                <ul className="space-y-1.5">
                  {heroes.map((row) => (
                    <li key={row.username}>
                      <IdentityRow
                        identity={row}
                        pending={pending === row.username}
                        disabled={pending !== null}
                        onSelect={() => void enter(row.username)}
                      />
                    </li>
                  ))}
                </ul>

                {others.length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer px-2 py-1 text-xs text-faint hover:text-muted">
                      Altre {others.length} identità
                    </summary>
                    <ul className="mt-1.5 space-y-1.5">
                      {others.map((row) => (
                        <li key={row.username}>
                          <IdentityRow
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

            <button
              type="button"
              onClick={() => setOpen(false)}
              className="mt-2 min-h-11 w-full text-xs text-faint transition-colors hover:text-muted"
            >
              Annulla
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function IdentityRow({
  identity,
  pending,
  disabled,
  onSelect,
}: {
  identity: DemoIdentity;
  pending: boolean;
  disabled: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className="flex w-full items-center gap-3 rounded-lg border border-line bg-surface px-3 py-2.5 text-left transition-colors hover:border-accent/50 disabled:opacity-50"
    >
      <span
        aria-hidden="true"
        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-semibold text-white"
        style={{ backgroundColor: SPID_BLUE }}
      >
        {identity.display_name
          .split(' ')
          .map((part) => part[0])
          .join('')
          .slice(0, 2)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-ink">{identity.display_name}</span>
          {identity.hero && (
            <span className="shrink-0 rounded-full bg-accent-soft px-1.5 py-0.5 text-[10px] font-medium text-accent-ink">
              {identity.hero}
            </span>
          )}
        </span>
        <span className="block truncate text-[11px] text-faint">
          {identity.note ?? identity.care_intent}
        </span>
      </span>
      {pending && <span className="shrink-0 text-[11px] text-accent">…</span>}
    </button>
  );
}
