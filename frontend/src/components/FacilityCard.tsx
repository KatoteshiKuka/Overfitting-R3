import type { Facility } from '@/api/types';
import { Badge } from '@/components/Badge';
import { facilityTypeLabel, isTerritorial } from '@/lib/facilityTypes';
import { joinParts } from '@/lib/format';
import { Link } from 'react-router-dom';

type FacilityCardProps = {
  facility: Facility;
};

export function FacilityCard({ facility }: FacilityCardProps) {
  const territorial = isTerritorial(facility.type);
  const location = joinParts([facility.address, facility.municipality, facility.postal_code]);

  return (
    <Link
      to={`/presidi/${facility.id}`}
      className="group block rounded-2xl border border-line bg-surface p-4 shadow-card transition-colors hover:border-accent/50"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[15px] font-semibold leading-snug text-ink group-hover:text-accent-ink">
          {facility.name}
        </h3>
        <Badge cssVar={territorial ? '--triage-verde' : '--triage-arancione'}>
          {facilityTypeLabel(facility.type)}
        </Badge>
      </div>

      {location && <p className="mt-1.5 text-sm text-muted">{location}</p>}

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-faint">
        {facility.asl && <span>{facility.asl}</span>}
        {facility.beds !== null && facility.beds > 0 && (
          <span className="tabular">{facility.beds} posti letto</span>
        )}
        {facility.phone && <span>{facility.phone}</span>}
      </div>
    </Link>
  );
}
