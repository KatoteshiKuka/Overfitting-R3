import { facilityTypeLabel } from '@/lib/facilityTypes';
import type { FacilityType } from '@/api/types';
import type { NearbyFacility, NearbyResponse } from '@/features/triage/types';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet';

type NearbyFacilitiesMapProps = {
  data: NearbyResponse;
  selectedId: number | null;
  onSelect: (facility: NearbyFacility) => void;
};

const TYPE_COLORS: Record<string, string> = {
  farmacia: '#22c55e',
  'casa-comunita': '#38bdf8',
  ambulatorio: '#a78bfa',
};

function FitNearby({ data }: { data: NearbyResponse }) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] = [
      [data.origin.latitude, data.origin.longitude],
      ...data.facilities.map((facility): [number, number] => [
        facility.latitude,
        facility.longitude,
      ]),
    ];
    map.fitBounds(points, { padding: [36, 36], maxZoom: 14 });
  }, [data, map]);

  return null;
}

export function NearbyFacilitiesMap({ data, selectedId, onSelect }: NearbyFacilitiesMapProps) {
  return (
    <div className="h-full w-full overflow-hidden rounded-2xl border border-line">
      <MapContainer
        center={[data.origin.latitude, data.origin.longitude]}
        zoom={13}
        scrollWheelZoom={false}
        zoomControl={false}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="map-muted"
        />

        <CircleMarker
          center={[data.origin.latitude, data.origin.longitude]}
          radius={9}
          pathOptions={{ color: '#ffffff', fillColor: '#0f766e', fillOpacity: 1, weight: 3 }}
        >
          <Tooltip direction="top" permanent>
            Sei qui
          </Tooltip>
        </CircleMarker>

        {data.facilities.map((facility) => {
          const selected = facility.facility_id === selectedId;
          return (
            <CircleMarker
              key={facility.facility_id}
              center={[facility.latitude, facility.longitude]}
              radius={selected ? 11 : 7}
              eventHandlers={{ click: () => onSelect(facility) }}
              pathOptions={{
                color: '#ffffff',
                fillColor: TYPE_COLORS[facility.type] ?? '#64748b',
                fillOpacity: 0.95,
                weight: selected ? 4 : 2,
              }}
            >
              <Tooltip direction="top" permanent={selected}>
                {facility.name} · {facility.distance_km} km ·{' '}
                {facilityTypeLabel(facility.type as FacilityType)}
              </Tooltip>
            </CircleMarker>
          );
        })}

        <FitNearby data={data} />
      </MapContainer>
    </div>
  );
}
