import { ComingSoon } from '@/components/ComingSoon';

/**
 * Slot feature A. Sostituisci il contenuto quando la feature viene assegnata in TASKS.md:
 * la rotta `/feature-a` è già registrata, non serve toccare `routes.tsx`.
 */
export function FeatureAPage() {
  return (
    <ComingSoon
      slot="Feature A"
      frontendPath="frontend/src/features/feature-a/"
      backendPath="backend/app/features/feature_a/"
      ideas={[
        'Assistente di triage: poche domande sui sintomi, un codice colore in uscita e la struttura più adatta al caso.',
        'Percorso guidato per i codici a bassa intensità: perché il pronto soccorso non serve e dove andare invece.',
        'Ricerca per prossimità: le strutture territoriali più vicine a un indirizzo, ordinate per idoneità.',
      ]}
    />
  );
}
