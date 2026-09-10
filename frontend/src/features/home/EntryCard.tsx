import { NavIcon, type NavIconName } from '@/components/NavIcon';
import { Link } from 'react-router-dom';

type EntryCardProps = {
  to: string;
  icon: NavIconName;
  title: string;
  description: string;
  pending?: boolean;
};

export function EntryCard({ to, icon, title, description, pending = false }: EntryCardProps) {
  return (
    <Link
      to={to}
      className={`group flex flex-col rounded-2xl border p-5 shadow-card transition-colors ${
        pending
          ? 'border-dashed border-line bg-surface hover:border-accent/40'
          : 'border-line bg-surface hover:border-accent/60'
      }`}
    >
      <span
        aria-hidden="true"
        className={`grid h-10 w-10 place-items-center rounded-xl ${
          pending ? 'bg-raised text-faint' : 'bg-accent-soft text-accent-ink'
        }`}
      >
        <NavIcon name={icon} />
      </span>

      <h3 className="mt-4 text-[15px] font-semibold text-ink">
        {title}
        {pending && (
          <span className="ml-2 rounded-full bg-raised px-2 py-0.5 text-[10px] font-normal text-faint">
            da assegnare
          </span>
        )}
      </h3>
      <p className="mt-1.5 flex-1 text-sm leading-relaxed text-muted">{description}</p>
      <span className="mt-4 text-sm text-accent transition-opacity group-hover:opacity-80">
        {pending ? 'Vedi lo slot →' : 'Apri →'}
      </span>
    </Link>
  );
}
