import { EmergencyCard } from '@/features/home/EmergencyCard';
import { TRIAGE_CODES, TRIAGE_SCALE } from '@/lib/triage';

/**
 * La scala dei codici, spiegata. È il vocabolario che entrambe le feature useranno:
 * mostrarlo subito rende leggibile tutto il resto dell'app.
 */
export function TriageScale() {
  return (
    <section aria-labelledby="scala-triage" className="mt-10">
      <h2 id="scala-triage" className="text-sm font-semibold text-ink">
        I cinque codici
      </h2>
      <p className="mt-1 text-sm text-muted">
        I primi tre si gestiscono quasi sempre sul territorio, senza pronto soccorso.
      </p>

      <ul className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {TRIAGE_CODES.map((code) => {
          const definition = TRIAGE_SCALE[code];
          return (
            <li
              key={code}
              className="flex items-start gap-3 rounded-xl border border-line bg-surface p-3"
            >
              <span
                aria-hidden="true"
                className="mt-1 h-3 w-3 shrink-0 rounded-full ring-2"
                style={{
                  backgroundColor: `rgb(var(${definition.cssVar}))`,
                  // L'anello tiene visibile il codice bianco anche su fondo chiaro.
                  ['--tw-ring-color' as string]: `rgb(var(${definition.cssVar}) / 0.25)`,
                }}
              />
              <div className="min-w-0">
                {/* Priorità su riga propria: le etichette lunghe non spezzano l'allineamento. */}
                <p className="text-sm font-medium leading-tight text-ink">{definition.label}</p>
                <p className="mt-0.5 text-xs text-faint">{definition.priority}</p>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">
                  {definition.description}
                </p>
              </div>
            </li>
          );
        })}
        {/* Sesta cella della griglia: lo spazio lasciato libero dai cinque codici. */}
        <li>
          <EmergencyCard />
        </li>
      </ul>
    </section>
  );
}
