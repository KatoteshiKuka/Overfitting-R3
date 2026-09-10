import { Card } from '@/components/Card';
import { Link } from 'react-router-dom';

type ComingSoonProps = {
  slot: string;
  /** Cartelle già pronte per chi prende lo slot. */
  frontendPath: string;
  backendPath: string;
  ideas: string[];
};

/**
 * Pagina degli slot feature non ancora assegnati.
 * Non è un segnaposto muto: dice a chi apre l'app quali sono i prossimi passi e dove si lavora.
 */
export function ComingSoon({ slot, frontendPath, backendPath, ideas }: ComingSoonProps) {
  return (
    <>
      <div className="mb-6">
        <span className="inline-flex items-center gap-2 rounded-full border border-dashed border-line px-3 py-1 text-xs text-faint">
          Slot libero
        </span>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-ink">{slot}</h1>
        <p className="mt-1.5 max-w-xl text-sm text-muted">
          Questa funzionalità non è ancora stata assegnata. Lo spazio è già predisposto: rotta,
          router e cartelle esistono, basta riempirli.
        </p>
      </div>

      <Card className="p-5">
        <h2 className="text-sm font-semibold text-ink">Come prenderla in carico</h2>
        <ol className="mt-3 space-y-2.5 text-sm text-muted">
          <li className="flex gap-3">
            <span className="tabular text-faint">1.</span>
            <span>
              Sposta la card in <code className="text-ink">TASKS.md</code> da TODO a IN_PROGRESS con
              il tuo ID agente, poi committa e pusha.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="tabular text-faint">2.</span>
            <span>
              Scrivi il contratto API in <code className="text-ink">STATE.md</code> prima di
              implementare, così l'altra metà del team può partire sui mock.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="tabular text-faint">3.</span>
            <span>
              Apri <code className="text-ink">feat/&lt;nome&gt;</code> e lavora solo in{' '}
              <code className="text-ink">{frontendPath}</code> e{' '}
              <code className="text-ink">{backendPath}</code>.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="tabular text-faint">4.</span>
            <span>
              Prima del push: <code className="text-ink">pnpm build</code>,{' '}
              <code className="text-ink">uv run ruff check .</code> e{' '}
              <code className="text-ink">./check_compliance.sh</code>.
            </span>
          </li>
        </ol>
      </Card>

      <Card className="mt-4 p-5">
        <h2 className="text-sm font-semibold text-ink">Idee coerenti con la traccia</h2>
        <ul className="mt-3 space-y-2 text-sm text-muted">
          {ideas.map((idea) => (
            <li key={idea} className="flex gap-2.5">
              <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
              <span>{idea}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-faint">
          Sono spunti, non vincoli: la scelta la fa il team.
        </p>
      </Card>

      <Link
        to="/presidi"
        className="mt-6 inline-flex min-h-11 items-center text-sm text-accent transition-opacity hover:opacity-80"
      >
        Intanto guarda i presidi censiti →
      </Link>
    </>
  );
}
