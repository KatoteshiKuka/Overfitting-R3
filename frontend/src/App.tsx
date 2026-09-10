import { AppShell } from '@/components/AppShell';
import { AuthGate } from '@/features/auth/AuthGate';
import { AuthProvider } from '@/features/auth/AuthContext';
import { NotFoundPage } from '@/features/home/NotFoundPage';
import { ROUTES } from '@/routes';
import { Route, Routes } from 'react-router-dom';

export function App() {
  return (
    <AuthProvider>
      <AppShell>
        {/* Nessuna pagina è raggiungibile prima di aver verificato la sessione. */}
        <AuthGate>
          <Routes>
            {ROUTES.map((route) => (
              <Route key={route.path} path={route.path} element={route.element} />
            ))}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthGate>
      </AppShell>
    </AuthProvider>
  );
}
