import { NavIcon } from '@/components/NavIcon';
import { NAV_ROUTES } from '@/routes';
import { NavLink } from 'react-router-dom';

/** Navigazione laterale su desktop. Le voci arrivano dal registro rotte. */
export function NavRail() {
  return (
    <nav aria-label="Sezioni" className="hidden w-56 shrink-0 md:block">
      <ul className="sticky top-24 space-y-1">
        {NAV_ROUTES.map((route) => (
          <li key={route.path}>
            <NavLink
              to={route.path}
              end={route.path === '/'}
              className={({ isActive }) =>
                `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition-colors ${
                  isActive
                    ? 'bg-accent-soft font-medium text-accent-ink'
                    : 'text-muted hover:bg-raised hover:text-ink'
                }`
              }
            >
              <NavIcon name={route.nav.icon} />
              <span className="flex-1">{route.nav.label}</span>
              {route.nav.pending && (
                <span className="rounded-full bg-raised px-1.5 py-0.5 text-[10px] text-faint">
                  slot
                </span>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
