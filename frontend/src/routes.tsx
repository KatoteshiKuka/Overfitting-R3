/**
 * Registro delle rotte.
 *
 * FILE GLOBALE — append-only. Per aggiungere una feature si accoda **una voce** in fondo
 * all'array `ROUTES`: non si riordina, non si riformatta, non si rinominano le esistenti.
 * Vedi AGENTS.md e STATE.md.
 */

import { FacilityDetailPage } from '@/features/facilities/FacilityDetailPage';
import { FacilitiesPage } from '@/features/facilities/FacilitiesPage';
import { HomePage } from '@/features/home/HomePage';
import { OperatorePage } from '@/features/operatore/OperatorePage';
import { TriagePage } from '@/features/triage/TriagePage';
import type { ReactElement } from 'react';

export type AppRoute = {
  path: string;
  element: ReactElement;
};

export const ROUTES: AppRoute[] = [
  { path: '/', element: <HomePage /> },
  { path: '/presidi', element: <FacilitiesPage /> },
  { path: '/presidi/:facilityId', element: <FacilityDetailPage /> },
  // Feature 1: assistente di triage per il paziente.
  { path: '/paziente', element: <TriagePage /> },
  // Feature 2: area del personale, ancora da sviluppare.
  { path: '/operatore', element: <OperatorePage /> },
];
