import { BRANDING } from '@/lib/branding';

export function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <span
        aria-hidden="true"
        className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-white"
      >
        <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2.5 10h3l1.8-4.5L10 14l2-6 1.5 2h4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <span className="leading-tight">
        <span className="block text-[15px] font-semibold tracking-tight text-ink">
          {BRANDING.name}
          <span className="text-accent"> {BRANDING.region}</span>
        </span>
        <span className="hidden text-[11px] text-faint sm:block">{BRANDING.tagline}</span>
      </span>
    </span>
  );
}
