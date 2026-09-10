import type { ReactNode } from 'react';

type BadgeProps = {
  children: ReactNode;
  /** Variabile CSS del colore semantico, es. `--triage-verde`. Assente = neutro. */
  cssVar?: string;
  className?: string;
};

export function Badge({ children, cssVar, className = '' }: BadgeProps) {
  const style = cssVar
    ? { color: `rgb(var(${cssVar}))`, backgroundColor: `rgb(var(${cssVar}) / 0.12)` }
    : undefined;

  return (
    <span
      style={style}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        cssVar ? '' : 'bg-raised text-muted'
      } ${className}`}
    >
      {children}
    </span>
  );
}
