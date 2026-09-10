import { MAP_COLORS, MAP_ORIGIN_COLOR } from '@/features/triage/congestion';
import type { PlanOption, PlanResponse } from '@/features/triage/types';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet';

type FacilityMapProps = {
  plan: PlanResponse;
  selectedId: number | null;
  onSelect: (option: PlanOption) => void;
};

/** Inquadra il percorso mostrato, non tutti i punti: così la mappa resta leggibile. */
function FitRoute({ plan, selected }: { plan: PlanResponse; selected: PlanOption }) {
  const map = useMap();

  useEffect(() => {
    const points: [number, number][] =
      selected.route_geometry.length > 1
        ? selected.route_geometry.map((point) => [point[0], point[1]])
        : [
            [plan.origin.latitude, plan.origin.longitude],
            [selected.latitude, selected.longitude],
          ];
    map.fitBounds(points, { padding: [50, 50], maxZoom: 15 });
  }, [map, plan, selected]);

  return null;
}

export function FacilityMap({ plan, selectedId, onSelect }: FacilityMapProps) {
  const selected =
    plan.options.find((option) => option.facility_id === selectedId) ?? plan.options[0];
  if (!selected) return null;

  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-line">
      <MapContainer
        center={[plan.origin.latitude, plan.origin.longitude]}
        zoom={13}
        scrollWheelZoom={false}
        zoomControl={false}
        className="h-full w-full"
      >
        {/*
          Tile in scala di grigi: la cartografia standard è satura di colori e insegne,
          e coprirebbe proprio quello che deve risaltare — il percorso e i due capolinea.
        */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        {/* Tracciato: una scia chiara sotto e la linea piena sopra, così si stacca dallo sfondo. */}
        {selected.route_geometry.length > 1 && (
          <>
            <Polyline
              positions={selected.route_geometry.map((p) => [p[0], p[1]])}
              pathOptions={{ color: '#ffffff', weight: 9, opacity: 0.9 }}
            />
            <Polyline
              positions={selected.route_geometry.map((p) => [p[0], p[1]])}
              pathOptions={{
                color: MAP_ORIGIN_COLOR,
                weight: 4,
                opacity: 1,
                // Tratteggio quando il percorso è una stima in linea d'aria.
                dashArray: selected.route_source === 'osrm' ? undefined : '6 8',
              }}
            />
          </>
        )}

        {/* Le alternative restano visibili ma defilate: non devono competere col percorso. */}
        {plan.options
          .filter((option) => option.facility_id !== selected.facility_id)
          .map((option) => (
            <CircleMarker
              key={option.facility_id}
              center={[option.latitude, option.longitude]}
              radius={6}
              eventHandlers={{ click: () => onSelect(option) }}
              pathOptions={{
                color: '#ffffff',
                fillColor: MAP_COLORS[option.congestion_level],
                fillOpacity: 0.85,
                weight: 2,
              }}
            >
              <Tooltip direction="top">
                {option.name} · {option.total_minutes} min
              </Tooltip>
            </CircleMarker>
          ))}

        <CircleMarker
          center={[plan.origin.latitude, plan.origin.longitude]}
          radius={8}
          pathOptions={{
            color: '#ffffff',
            fillColor: MAP_ORIGIN_COLOR,
            fillOpacity: 1,
            weight: 3,
          }}
        >
          <Tooltip direction="top" permanent>
            Sei qui
          </Tooltip>
        </CircleMarker>

        <CircleMarker
          center={[selected.latitude, selected.longitude]}
          radius={11}
          pathOptions={{
            color: '#ffffff',
            fillColor: MAP_COLORS[selected.congestion_level],
            fillOpacity: 1,
            weight: 3,
          }}
        >
          <Tooltip direction="top" permanent>
            {selected.name}
          </Tooltip>
        </CircleMarker>

        <FitRoute plan={plan} selected={selected} />
      </MapContainer>
    </div>
  );
}
