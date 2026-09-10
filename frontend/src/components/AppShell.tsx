import { NavRail } from '@/components/NavRail';
import { TabBar } from '@/components/TabBar';
import { TopBar } from '@/components/TopBar';
import type { ReactNode } from 'react';

type AppShellProps = {
  children: ReactNode;
};

/** Telaio dell'interfaccia: top bar, navigazione e area contenuto a larghezza leggibile. */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-dvh bg-ground">
      <a
        href="#contenuto"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:text-white"
      >
        Salta al contenuto
      </a>

      <TopBar />

      <div className="mx-auto flex w-full max-w-5xl gap-8 px-4 pb-24 pt-6 md:pb-12">
        <NavRail />
        <main id="contenuto" className="min-w-0 flex-1">
          {children}
        </main>
      </div>

      <TabBar />
    </div>
  );
}
