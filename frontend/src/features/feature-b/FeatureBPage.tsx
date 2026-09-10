import { ComingSoon } from '@/components/ComingSoon';

/**
 * Slot feature B. Sostituisci il contenuto quando la feature viene assegnata in TASKS.md:
 * la rotta `/feature-b` è già registrata, non serve toccare `routes.tsx`.
 */
export function FeatureBPage() {
  return (
    <ComingSoon
      slot="Feature B"
      frontendPath="frontend/src/features/feature-b/"
      backendPath="backend/app/features/feature_b/"
      ideas={[
        'Indice di pressione sui pronto soccorso: picchi termici ed eventi in città correlati alla saturazione dei presidi.',
        'Serie storiche dei tempi di attesa ambulatoriali dal Portale Nazionale, per capire quando conviene presentarsi.',
        'Cruscotto della saturazione per ASL, con confronto tra presidi dello stesso territorio.',
      ]}
    />
  );
}
