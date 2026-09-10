export type ChipOption = {
  value: string;
  label: string;
  count?: number;
};

type FilterChipsProps = {
  options: ChipOption[];
  value: string;
  onChange: (value: string) => void;
  allLabel?: string;
  label: string;
};

export function FilterChips({
  options,
  value,
  onChange,
  allLabel = 'Tutte',
  label,
}: FilterChipsProps) {
  const chips: ChipOption[] = [{ value: '', label: allLabel }, ...options];

  return (
    <div role="group" aria-label={label} className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
      {chips.map((chip) => {
        const isActive = chip.value === value;
        return (
          <button
            key={chip.value || 'all'}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(chip.value)}
            className={`min-h-11 shrink-0 rounded-full border px-4 text-sm transition-colors ${
              isActive
                ? 'border-accent bg-accent-soft font-medium text-accent-ink'
                : 'border-line bg-surface text-muted hover:border-accent/40 hover:text-ink'
            }`}
          >
            {chip.label}
            {chip.count !== undefined && (
              <span className="tabular ml-1.5 text-xs opacity-70">{chip.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
