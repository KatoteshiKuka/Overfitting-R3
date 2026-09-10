export type NavIconName = 'home' | 'facilities' | 'slot';

type NavIconProps = {
  name: NavIconName;
  className?: string;
};

export function NavIcon({ name, className = 'h-5 w-5' }: NavIconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {name === 'home' && <path d="M3.5 10.5 12 4l8.5 6.5V20a1 1 0 0 1-1 1h-4v-6h-7v6h-4a1 1 0 0 1-1-1Z" />}
      {name === 'facilities' && (
        <>
          <path d="M4 20V8.5L12 4l8 4.5V20" />
          <path d="M12 10v5M9.5 12.5h5" />
          <path d="M3 20h18" />
        </>
      )}
      {name === 'slot' && (
        <>
          <rect x="3.5" y="3.5" width="17" height="17" rx="3" strokeDasharray="3 3" />
          <path d="M12 8.5v7M8.5 12h7" />
        </>
      )}
    </svg>
  );
}
