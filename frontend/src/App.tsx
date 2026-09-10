import { AppShell } from '@/components/AppShell';
import { AuthProvider } from '@/features/auth/AuthContext';
import { NotFoundPage } from '@/features/home/NotFoundPage';
import { ROUTES } from '@/routes';
import { Route, Routes } from 'react-router-dom';

/**
 * L'applicazione è aperta: la home lascia scegliere il ruolo senza chiedere niente.
 *
 * L'autenticazione non è un cancello all'ingresso ma un passaggio puntuale, chiesto solo
 * quando serve davvero: al cittadino nel momento in cui conferma una destinazione, e a
 * chi lavora in una struttura quando apre la console. Fare login per poter descrivere
 * un mal di gola sarebbe un ostacolo senza motivo.
 */
export function App() {
  return (
    <AuthProvider>
      <AppShell>
        <Routes>
          {ROUTES.map((route) => (
            <Route key={route.path} path={route.path} element={route.element} />
          ))}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </AuthProvider>
  );
}
