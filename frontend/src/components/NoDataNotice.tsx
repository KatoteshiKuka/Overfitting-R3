import { EmptyState } from '@/components/EmptyState';

/**
 * Stato che vede chi clona il repo prima di scaricare i dataset.
 * Deve spiegare cosa fare, non limitarsi a dire che non c'è niente.
 */
export function NoDataNotice() {
  return (
    <EmptyState
      title="Nessun dataset caricato"
      description={
        <>
          <p>
            Il backend non ha trovato file in <code className="text-ink">data/facilities/</code>.
            Scarica il censimento delle strutture dal Portale Open Data della Regione Lazio
            (Pronto Soccorso, Posti letto, Strutture sanitarie), copia il CSV o il JSON in quella
            cartella e ricarica.
          </p>
          <p className="mt-3">Le istruzioni complete sono in <code className="text-ink">data/README.md</code>.</p>
        </>
      }
      action={
        <code className="inline-block rounded-lg bg-raised px-3 py-2 text-xs text-muted">
          cd backend && uv run python -m app.cli seed --reset
        </code>
      }
    />
  );
}
