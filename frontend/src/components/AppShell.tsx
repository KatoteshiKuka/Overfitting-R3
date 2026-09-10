import { TopBar } from '@/components/TopBar';
import type { ReactNode } from 'react';

type AppShellProps = {
  children: ReactNode;
};

/**
 * Telaio dell'interfaccia: solo barra superiore e contenuto a tutta finestra.
 *
 * Niente navigazione laterale: il percorso è guidato (si sceglie il ruolo e si prosegue),
 * quindi un menu permanente ruberebbe spazio senza aggiungere niente. Si torna indietro
 * dal logo o dai pulsanti in pagina.
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-ground">
      <a
        href="#contenuto"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:text-white"
      >
        Salta al contenuto
      </a>

      <TopBar />

      <main id="contenuto" className="flex w-full flex-1 flex-col px-4 pb-8 pt-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
