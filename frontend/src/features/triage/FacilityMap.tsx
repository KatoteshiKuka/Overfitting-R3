import type { PlanOption, PlanResponse } from '@/features/triage/types';
import { MAP_COLORS, MAP_ORIGIN_COLOR } from '@/features/triage/congestion';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet';

type FacilityMapProps = {
  plan: PlanResponse;
  selectedId: number | null;
  onSelect: (option: PlanOption) => void;
};

/** Riporta la vista sui punti ogni volta che cambia il piano o la selezione. */
function FitBounds({ plan, selectedId }: { plan: PlanResponse; selectedId: number | null }) {
  const map = useMap();

  useEffect(() => {
    const selected = plan.options.find((option) => option.facility_id === selectedId);
    if (selected) {
      map.flyTo([selected.latitude, selected.longitude], 14, { duration: 0.6 });
      return;
    }
    const points: [number, number][] = [
      [plan.origin.latitude, plan.origin.longitude],
      ...plan.options.map((option): [number, number] => [option.latitude, option.longitude]),
    ];
    if (points.length > 1) map.fitBounds(points, { padding: [40, 40] });
  }, [map, plan, selectedId]);

  return null;
}

export function FacilityMap({ plan, selectedId, onSelect }: FacilityMapProps) {
  return (
    <div className="h-[380px] overflow-hidden rounded-2xl border border-line">
      <MapContainer
        center={[plan.origin.latitude, plan.origin.longitude]}
        zoom={13}
        scrollWheelZoom={false}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Punto di partenza: neutro, si distingue dalle strutture per forma e colore. */}
        <CircleMarker
          center={[plan.origin.latitude, plan.origin.longitude]}
          radius={7}
          pathOptions={{
            color: MAP_ORIGIN_COLOR,
            fillColor: MAP_ORIGIN_COLOR,
            fillOpacity: 1,
            weight: 3,
          }}
        >
          <Popup>Sei qui</Popup>
        </CircleMarker>

        {plan.options.map((option) => {
          const color = MAP_COLORS[option.congestion_level];
          const isSelected = option.facility_id === selectedId;
          return (
            <CircleMarker
              key={option.facility_id}
              center={[option.latitude, option.longitude]}
              radius={option.recommended ? 12 : 9}
              eventHandlers={{ click: () => onSelect(option) }}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: isSelected ? 1 : 0.7,
                weight: isSelected ? 4 : 2,
              }}
            >
              <Popup>
                <strong>{option.name}</strong>
                <br />
                {option.total_minutes} min in tutto · attesa {option.waiting_minutes} min
              </Popup>
            </CircleMarker>
          );
        })}

        <FitBounds plan={plan} selectedId={selectedId} />
      </MapContainer>
    </div>
  );
}
