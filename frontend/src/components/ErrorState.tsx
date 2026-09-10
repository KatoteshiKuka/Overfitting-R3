import { ApiError } from '@/api/client';

type ErrorStateProps = {
  error: unknown;
  onRetry?: () => void;
};

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const isOffline = error instanceof ApiError && error.code === 'network_error';
  const message = error instanceof Error ? error.message : 'Errore imprevisto.';

  return (
    <div
      role="alert"
      className="rounded-2xl border border-line bg-surface px-6 py-10 text-center"
      style={{ borderColor: 'rgb(var(--triage-arancione) / 0.35)' }}
    >
      <p className="text-base font-semibold text-ink">
        {isOffline ? 'Backend non raggiungibile' : 'Qualcosa non ha funzionato'}
      </p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">{message}</p>
      {isOffline && (
        <code className="mt-3 inline-block rounded-lg bg-raised px-3 py-1.5 text-xs text-muted">
          cd backend && uv run fastapi dev app/main.py
        </code>
      )}
      {onRetry && (
        <div className="mt-5">
          <button
            type="button"
            onClick={onRetry}
            className="min-h-11 rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90"
          >
            Riprova
          </button>
        </div>
      )}
    </div>
  );
}
