import { RoleCard } from '@/features/home/RoleCard';
import { TriageScale } from '@/features/home/TriageScale';
import { BRANDING } from '@/lib/branding';
import { useRole } from '@/lib/useRole';

/** Apertura dell'app: si sceglie chi sei, e da lì cambia tutto il percorso. */
export function HomePage() {
  const { setRole } = useRole();

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center py-6">
      <section className="animate-fade-up text-center">
        <p className="text-sm font-medium text-accent">{BRANDING.tagline}</p>
        <h1 className="mx-auto mt-2 max-w-2xl text-[2rem] font-semibold leading-[1.15] tracking-tight text-ink sm:text-4xl">
          {BRANDING.claim}
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-muted">
          {BRANDING.subclaim}
        </p>
      </section>

      <section aria-label="Scegli il tuo ruolo" className="mt-10 grid gap-4 sm:grid-cols-2">
        <RoleCard
          to="/paziente"
          accent
          onSelect={() => setRole('paziente')}
          title="Ho bisogno di aiuto"
          description="Raccontami cosa ti succede: capiamo insieme quanto è urgente e dove conviene andare, con i tempi reali di viaggio e di attesa."
          cta="Inizia"
          icon={
            <svg
              viewBox="0 0 24 24"
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20.5 10.5c0 5-8.5 9.5-8.5 9.5s-8.5-4.5-8.5-9.5a5 5 0 0 1 8.5-3.5 5 5 0 0 1 8.5 3.5Z" />
            </svg>
          }
        />

        <RoleCard
          to="/operatore"
          onSelect={() => setRole('operatore')}
          title="Lavoro in una struttura"
          description="Monitoraggio dei reparti e dello stato dei presidi. Sezione in costruzione: la sviluppa il team."
          cta="Entra"
          icon={
            <svg
              viewBox="0 0 24 24"
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M4 20V8.5L12 4l8 4.5V20" />
              <path d="M12 10v5M9.5 12.5h5" />
              <path d="M3 20h18" />
            </svg>
          }
        />
      </section>

      <TriageScale />

      <p className="mt-10 rounded-xl border border-line bg-raised px-4 py-3 text-xs leading-relaxed text-muted">
        HealthPulse non è un servizio medico e non sostituisce una diagnosi. In caso di
        emergenza chiama sempre il <strong className="text-ink">118</strong>.
      </p>
    </div>
  );
}
