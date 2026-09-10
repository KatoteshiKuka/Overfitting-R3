/**
 * Scorciatoia al 118, nello spazio lasciato libero dai cinque codici.
 *
 * È un link `tel:` e non un pulsante con conferma: chi ha davvero un'emergenza deve
 * poter chiamare con un tocco, senza passaggi intermedi.
 */
export function EmergencyCard() {
  return (
    <a
      href="tel:118"
      className="flex items-center gap-3 rounded-xl border p-3 transition-transform hover:-translate-y-0.5"
      style={{
        borderColor: 'rgb(var(--triage-rosso) / 0.4)',
        backgroundColor: 'rgb(var(--triage-rosso) / 0.08)',
      }}
    >
      <span
        aria-hidden="true"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-white"
        style={{ backgroundColor: 'rgb(var(--triage-rosso))' }}
      >
        <svg
          viewBox="0 0 24 24"
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M6.5 3.5h3l1.5 4-2 1.5a12 12 0 0 0 6 6l1.5-2 4 1.5v3a1.5 1.5 0 0 1-1.7 1.5A17 17 0 0 1 5 5.2 1.5 1.5 0 0 1 6.5 3.5Z" />
        </svg>
      </span>
      <div className="min-w-0">
        <p
          className="text-sm font-semibold leading-tight"
          style={{ color: 'rgb(var(--triage-rosso))' }}
        >
          Chiama il 118
        </p>
        <p className="mt-0.5 text-xs leading-relaxed text-muted">
          Se è un'emergenza non aspettare il triage: chiama subito.
        </p>
      </div>
    </a>
  );
}
