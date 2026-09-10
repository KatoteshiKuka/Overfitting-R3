import { Logo } from '@/components/Logo';
import { SessionMenu } from '@/components/SessionMenu';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useTheme } from '@/lib/useTheme';
import { Link } from 'react-router-dom';

export function TopBar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-ground/85 backdrop-blur">
      <div className="flex h-16 w-full items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="rounded-lg" aria-label="Torna alla scelta del ruolo">
          <Logo />
        </Link>
        <div className="flex-1" />
        <SessionMenu />
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </div>
    </header>
  );
}
