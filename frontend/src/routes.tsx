/**
 * Registro delle rotte.
 *
 * FILE GLOBALE — append-only. Per aggiungere una feature si accoda **una voce** in fondo
 * all'array `ROUTES`: non si riordina, non si riformatta, non si rinominano le esistenti.
 * Vedi AGENTS.md e STATE.md.
 *
 * Ogni voce con `nav` compare automaticamente nella navigazione (rail su desktop,
 * tab bar su mobile): non serve toccare i componenti di layout.
 */

import type { NavIconName } from '@/components/NavIcon';
import { FacilityDetailPage } from '@/features/facilities/FacilityDetailPage';
import { FacilitiesPage } from '@/features/facilities/FacilitiesPage';
import { FeatureBPage } from '@/features/feature-b/FeatureBPage';
import { HomePage } from '@/features/home/HomePage';
import { OperatorePage } from '@/features/operatore/OperatorePage';
import { TriagePage } from '@/features/triage/TriagePage';
import type { ReactElement } from 'react';

export type AppRoute = {
  path: string;
  element: ReactElement;
  nav?: {
    label: string;
    icon: NavIconName;
    /** Voce ancora da assegnare: la navigazione la mostra attenuata. */
    pending?: boolean;
  };
};

export const ROUTES: AppRoute[] = [
  { path: '/', element: <HomePage />, nav: { label: 'Home', icon: 'home' } },
  { path: '/presidi', element: <FacilitiesPage />, nav: { label: 'Presidi', icon: 'facilities' } },
  { path: '/presidi/:facilityId', element: <FacilityDetailPage /> },
  {
    path: '/feature-b',
    element: <FeatureBPage />,
    nav: { label: 'Feature B', icon: 'slot', pending: true },
  },
  // Feature 1: assistente di triage per il paziente.
  { path: '/paziente', element: <TriagePage />, nav: { label: 'Assistente', icon: 'triage' } },
  // Feature 2: area del personale, ancora da sviluppare. Senza `nav`: ci si arriva dalla home.
  { path: '/operatore', element: <OperatorePage /> },
];

export const NAV_ROUTES = ROUTES.filter(
  (route): route is AppRoute & { nav: NonNullable<AppRoute['nav']> } => Boolean(route.nav),
);
