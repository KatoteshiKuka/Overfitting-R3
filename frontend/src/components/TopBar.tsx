import { DataStatusPill } from '@/components/DataStatusPill';
import { Logo } from '@/components/Logo';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useTheme } from '@/lib/useTheme';
import { Link } from 'react-router-dom';

export function TopBar() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-ground/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center gap-3 px-4">
        <Link to="/" className="rounded-lg" aria-label="Vai alla home">
          <Logo />
        </Link>
        <div className="flex-1" />
        <DataStatusPill />
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </div>
    </header>
  );
}
