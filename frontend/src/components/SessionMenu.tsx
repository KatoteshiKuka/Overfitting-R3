import { useAuth } from '@/features/auth/useAuth';

/**
 * Identità in corso e uscita.
 *
 * Il codice fiscale non compare: per riconoscersi basta il nome, e mostrarlo in ogni
 * schermata sarebbe un dato personale esposto senza motivo.
 */
export function SessionMenu() {
  const { state, logout } = useAuth();

  if (state.status === 'loading' || state.status === 'anonymous') return null;

  const label =
    state.status === 'citizen'
      ? `${state.session.profile.name} ${state.session.profile.familyName}`
      : state.session.operator.display_name;

  const badge = state.status === 'citizen' ? 'SPID TEST' : 'STRUTTURA';

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-right leading-tight sm:block">
        <span className="block text-xs font-medium text-ink">{label}</span>
        <span className="block text-[10px] uppercase tracking-wide text-faint">{badge}</span>
      </span>
      <button
        type="button"
        onClick={() => void logout()}
        className="min-h-11 rounded-xl border border-line px-3 text-xs text-muted transition-colors hover:text-ink"
      >
        Esci
      </button>
    </div>
  );
}
