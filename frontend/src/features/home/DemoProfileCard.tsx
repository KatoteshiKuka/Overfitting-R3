type DemoProfileCardProps = {
  name: string;
  role: string;
  description: string;
  initials: string;
  cta: string;
  badge: string;
  accent?: boolean;
  pending?: boolean;
  disabled?: boolean;
  onSelect: () => void;
};

/** Profilo sintetico selezionabile nella schermata iniziale della demo. */
export function DemoProfileCard({
  name,
  role,
  description,
  initials,
  cta,
  badge,
  accent = false,
  pending = false,
  disabled = false,
  onSelect,
}: DemoProfileCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={`group flex w-full flex-col rounded-2xl border p-6 text-left shadow-card transition-all hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-60 ${
        accent
          ? 'border-accent/40 bg-surface hover:border-accent'
          : 'border-line bg-surface hover:border-accent/50'
      }`}
    >
      <div className="flex w-full items-start justify-between gap-3">
        <span
          aria-hidden="true"
          className={`grid h-12 w-12 place-items-center rounded-full text-sm font-semibold ${
            accent ? 'bg-accent text-white' : 'bg-raised text-ink'
          }`}
        >
          {initials}
        </span>
        <span className="rounded-full border border-line px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-faint">
          {badge}
        </span>
      </div>

      <h2 className="mt-5 text-lg font-semibold tracking-tight text-ink">{name}</h2>
      <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-accent">{role}</p>
      <p className="mt-3 flex-1 text-sm leading-relaxed text-muted">{description}</p>

      <span
        className={`mt-6 inline-flex min-h-11 items-center justify-center rounded-xl px-5 text-sm font-medium transition-colors ${
          accent
            ? 'bg-accent text-white group-hover:opacity-90'
            : 'border border-line text-ink group-hover:border-accent/50'
        }`}
      >
        {pending ? 'Accesso in corso…' : cta}
      </span>
    </button>
  );
}
