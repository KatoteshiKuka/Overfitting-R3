import { Skeleton } from '@/components/Skeleton';
import { SpidTestLogin } from '@/features/auth/SpidTestLogin';
import { useAuth } from '@/features/auth/useAuth';
import type { ReactNode } from 'react';

/**
 * Cancello d'ingresso dell'applicazione.
 *
 * Finché la sessione non è stata verificata sul server si mostra uno scheletro: senza
 * questo stato intermedio, chi è già autenticato vedrebbe comparire per un istante la
 * schermata di accesso a ogni ricaricamento della pagina.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  const { state } = useAuth();

  if (state.status === 'loading') {
    return (
      <div className="mx-auto w-full max-w-md flex-1 py-16">
        <Skeleton count={2} />
      </div>
    );
  }

  if (state.status === 'anonymous') {
    return <SpidTestLogin />;
  }

  return <>{children}</>;
}
