import { AppShell } from '@/components/AppShell';
import { NotFoundPage } from '@/features/home/NotFoundPage';
import { ROUTES } from '@/routes';
import { Route, Routes } from 'react-router-dom';

export function App() {
  return (
    <AppShell>
      <Routes>
        {ROUTES.map((route) => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  );
}
