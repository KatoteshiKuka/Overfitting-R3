"""Geocodifica e calcolo del tragitto tramite i servizi aperti di OpenStreetMap.

Nominatim traduce l'indirizzo in coordinate, OSRM calcola il percorso stradale.
Entrambi possono non rispondere: in quel caso si ricade sulla distanza in linea d'aria,
che è meno precisa ma sempre disponibile. I minuti restano un numero calcolato, non stimato
da un modello linguistico.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0

# Velocità media urbana: il traffico di Roma non premia le medie ottimistiche.
URBAN_SPEED_KMH = 22.0

# Le strade non sono rettilinee: correzione applicata quando OSRM non risponde.
DETOUR_FACTOR = 1.35


@dataclass(frozen=True, slots=True)
class GeoPoint:
    label: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Route:
    distance_km: float
    travel_minutes: int
    #: `osrm` se il percorso è reale, `stimato` se calcolato in linea d'aria.
    source: str


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def straight_line_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Route:
    distance = haversine_km(lat1, lon1, lat2, lon2) * DETOUR_FACTOR
    minutes = max(1, round(distance / URBAN_SPEED_KMH * 60))
    return Route(distance_km=round(distance, 1), travel_minutes=minutes, source="stimato")


async def geocode(address: str) -> GeoPoint | None:
    """Indirizzo → coordinate. La ricerca è vincolata al Lazio per evitare omonimie."""
    settings = get_settings()
    query = address.strip()
    if not query:
        return None

    params = {
        "q": query,
        "format": "json",
        "limit": "1",
        "countrycodes": "it",
        # Riquadro del Lazio: senza, "Via Roma" può finire in Piemonte.
        "viewbox": "11.45,42.85,14.05,40.75",
        "bounded": "1",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.geo_timeout_seconds) as client:
            response = await client.get(
                settings.nominatim_url,
                params=params,
                headers={"User-Agent": settings.user_agent},
            )
            response.raise_for_status()
            results = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Geocodifica non riuscita per '%s': %s", query, exc)
        return None

    if not results:
        return None

    first = results[0]
    try:
        return GeoPoint(
            label=first.get("display_name", query),
            latitude=float(first["lat"]),
            longitude=float(first["lon"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


async def route_between(origin: GeoPoint, dest_lat: float, dest_lon: float) -> Route:
    """Percorso stradale reale, con ricaduta sulla linea d'aria se OSRM non risponde."""
    settings = get_settings()
    path = f"{origin.longitude},{origin.latitude};{dest_lon},{dest_lat}"

    try:
        async with httpx.AsyncClient(timeout=settings.geo_timeout_seconds) as client:
            response = await client.get(
                f"{settings.osrm_url}/{path}",
                params={"overview": "false"},
                headers={"User-Agent": settings.user_agent},
            )
            response.raise_for_status()
            body = response.json()
        routes = body.get("routes") or []
        if routes:
            leg = routes[0]
            return Route(
                distance_km=round(leg["distance"] / 1000, 1),
                travel_minutes=max(1, round(leg["duration"] / 60)),
                source="osrm",
            )
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.warning("OSRM non disponibile, uso la distanza in linea d'aria: %s", exc)

    return straight_line_route(origin.latitude, origin.longitude, dest_lat, dest_lon)
