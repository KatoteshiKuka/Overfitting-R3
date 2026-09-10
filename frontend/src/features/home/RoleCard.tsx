import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

type RoleCardProps = {
  to: string;
  icon: ReactNode;
  title: string;
  description: string;
  cta: string;
  accent?: boolean;
  onSelect: () => void;
};

export function RoleCard({
  to,
  icon,
  title,
  description,
  cta,
  accent = false,
  onSelect,
}: RoleCardProps) {
  return (
    <Link
      to={to}
      onClick={onSelect}
      className={`group flex flex-col rounded-2xl border p-6 text-left shadow-card transition-all hover:-translate-y-0.5 ${
        accent
          ? 'border-accent/40 bg-surface hover:border-accent'
          : 'border-line bg-surface hover:border-accent/50'
      }`}
    >
      <span
        aria-hidden="true"
        className={`grid h-12 w-12 place-items-center rounded-2xl ${
          accent ? 'bg-accent text-white' : 'bg-raised text-muted'
        }`}
      >
        {icon}
      </span>

      <h2 className="mt-5 text-lg font-semibold tracking-tight text-ink">{title}</h2>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{description}</p>

      <span
        className={`mt-6 inline-flex min-h-11 items-center justify-center rounded-xl px-5 text-sm font-medium transition-colors ${
          accent
            ? 'bg-accent text-white group-hover:opacity-90'
            : 'border border-line text-ink group-hover:border-accent/50'
        }`}
      >
        {cta}
      </span>
    </Link>
  );
}
