import { NavIcon } from '@/components/NavIcon';
import { NAV_ROUTES } from '@/routes';
import { NavLink } from 'react-router-dom';

/** Navigazione su mobile: stesse voci della rail, ancorate in basso e raggiungibili col pollice. */
export function TabBar() {
  return (
    <nav
      aria-label="Sezioni"
      className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 backdrop-blur md:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <ul className="mx-auto flex max-w-2xl">
        {NAV_ROUTES.map((route) => (
          <li key={route.path} className="flex-1">
            <NavLink
              to={route.path}
              end={route.path === '/'}
              className={({ isActive }) =>
                `flex min-h-14 flex-col items-center justify-center gap-1 text-[11px] transition-colors ${
                  isActive ? 'text-accent' : 'text-faint'
                }`
              }
            >
              <NavIcon name={route.nav.icon} />
              <span>{route.nav.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
