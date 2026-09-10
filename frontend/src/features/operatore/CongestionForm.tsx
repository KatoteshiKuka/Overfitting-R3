import { apiPut } from '@/api/client';
import { ErrorState } from '@/components/ErrorState';
import type { CongestionDraft, CongestionSnapshot } from '@/features/operatore/types';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

type CongestionFormProps = {
  snapshot: CongestionSnapshot;
};

const FIELDS: { key: keyof CongestionDraft; label: string; hint: string }[] = [
  { key: 'waiting_red', label: 'Rossi', hint: 'in attesa' },
  { key: 'waiting_yellow', label: 'Gialli', hint: 'in attesa' },
  { key: 'waiting_green', label: 'Verdi', hint: 'in attesa' },
  { key: 'waiting_white', label: 'Bianchi', hint: 'in attesa' },
  { key: 'waiting_unassigned', label: 'Da assegnare', hint: 'senza codice' },
  { key: 'in_treatment', label: 'In trattamento', hint: 'nelle aree PS' },
  { key: 'in_observation', label: 'In osservazione', hint: 'OBI' },
];

function initialDraft(snapshot: CongestionSnapshot): CongestionDraft {
  return {
    waiting_red: snapshot.queue.rosso,
    waiting_yellow: snapshot.queue.giallo,
    waiting_green: snapshot.queue.verde,
    waiting_white: snapshot.queue.bianco,
    waiting_unassigned: snapshot.queue.non_assegnato,
    in_treatment: snapshot.in_treatment,
    in_observation: snapshot.in_observation,
  };
}

/** Modifica esplicita del carico osservato: nessuna simulazione parte da sola. */
export function CongestionForm({ snapshot }: CongestionFormProps) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<CongestionDraft>(() => initialDraft(snapshot));
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const update = useMutation({
    mutationFn: () =>
      apiPut<CongestionSnapshot>(`/congestion/${snapshot.facility_id}`, {
        ...draft,
        observed_at: new Date().toISOString(),
      }),
    onSuccess: async (next) => {
      setDraft(initialDraft(next));
      setSavedAt(next.observed_at);
      queryClient.setQueryData(['congestion', snapshot.facility_id], next);
      await queryClient.invalidateQueries({
        queryKey: ['hospital', 'console', snapshot.facility_id],
      });
    },
  });

  function change(key: keyof CongestionDraft, raw: string) {
    const parsed = Number.parseInt(raw, 10);
    const value = Number.isFinite(parsed) ? Math.min(500, Math.max(0, parsed)) : 0;
    setDraft((current) => ({ ...current, [key]: value }));
    setSavedAt(null);
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        update.mutate();
      }}
    >
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
        {FIELDS.map((field) => (
          <label key={field.key} className="rounded-xl bg-raised px-3 py-2.5">
            <span className="block text-[11px] font-medium uppercase tracking-wide text-faint">
              {field.label}
            </span>
            <input
              type="number"
              min={0}
              max={500}
              inputMode="numeric"
              value={draft[field.key]}
              onChange={(event) => change(field.key, event.target.value)}
              className="tabular mt-1 min-h-10 w-full rounded-lg border border-line bg-surface px-2 text-lg font-semibold text-ink focus:border-accent"
              aria-label={`${field.label}, ${field.hint}`}
            />
            <span className="mt-0.5 block text-[10px] text-faint">{field.hint}</span>
          </label>
        ))}
      </div>

      {update.isError && (
        <div className="mt-3">
          <ErrorState error={update.error} />
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted" aria-live="polite">
          {savedAt
            ? 'Carico osservato salvato. Attese, pressione e ranking sono stati ricalcolati.'
            : 'Il salvataggio sostituisce lo snapshot storico con un dato dichiarato dalla struttura.'}
        </p>
        <button
          type="submit"
          disabled={update.isPending}
          className="min-h-11 rounded-xl bg-accent px-5 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {update.isPending ? 'Ricalcolo…' : 'Salva e ricalcola'}
        </button>
      </div>
    </form>
  );
}
