import { Badge } from '@/components/Badge';
import { TRIAGE_SCALE, type TriageCode } from '@/lib/triage';

type TriageCodeBadgeProps = {
  code: TriageCode;
  /** Mostra anche la priorità testuale: il colore da solo non basta mai. */
  withPriority?: boolean;
};

export function TriageCodeBadge({ code, withPriority = false }: TriageCodeBadgeProps) {
  const definition = TRIAGE_SCALE[code];

  return (
    <Badge cssVar={definition.cssVar}>
      <span
        aria-hidden="true"
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: `rgb(var(${definition.cssVar}))` }}
      />
      <span>Codice {definition.label}</span>
      {withPriority && <span className="font-normal opacity-80">· {definition.priority}</span>}
    </Badge>
  );
}
