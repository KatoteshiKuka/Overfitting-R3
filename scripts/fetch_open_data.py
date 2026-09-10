#!/usr/bin/env python3
"""Scarica i dataset aperti reali e li normalizza nel formato dell'app.

    uv run --with httpx python scripts/fetch_open_data.py

Fonti (vedi `data/FINALIDATASET.xlsx`, colonna "Link fonte"):

- HP-D01  Pronto Soccorso, accessi in tempo reale  → code reali per codice colore
- HP-D08  Farmacie della Regione Lazio             → farmacie con coordinate
- HP-D05  Elenco degli ospedali del Lazio          → ospedali pubblici
- HP-D05b Strutture sanitarie private accreditate  → ambulatori con coordinate

Gli output finiscono in `data/facilities/` e `data/congestion/` e vengono committati:
il team non deve rieseguire lo script per far partire l'app. Si rilancia solo quando
si vuole aggiornare la fotografia dei dati.

Le strutture prive di coordinate vengono geocodificate con Nominatim, rispettandone
il limite di una richiesta al secondo. La cache su disco evita di ripetere il lavoro.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import unicodedata
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FACILITIES = DATA / "facilities"
CONGESTION = DATA / "congestion"
CACHE = DATA / ".geocache.json"

USER_AGENT = "HealthPulse/0.1 (hackathon; open data ingestion)"

SOURCES = {
    "pronto_soccorso": (
        "https://dati.lazio.it/dataset/144e577e-8a7e-4613-9830-48cbb1d7ee0f/resource/"
        "12c31624-f1a4-4874-a903-8954549ddb81/download/output_1627742164504.csv"
    ),
    "farmacie": (
        "https://dati.lazio.it/dataset/551579e1-a65d-4e7e-80d7-9bfe07fb2bdc/resource/"
        "7658322d-b629-4d77-a9f1-e4aad7c8f83b/download/farmaciereglaziolatlon.csv"
    ),
    "ospedali": (
        "https://dati.lazio.it/dataset/d2250e06-22b7-4b45-b8ad-6678cb8ab7db/resource/"
        "0219ed0b-5f99-47a3-be27-9df0d108ff6f/download/elencoospedali.csv"
    ),
    "private": (
        "https://dati.lazio.it/dataset/9c87461b-4e37-4357-b70d-85bdc07146c1/resource/"
        "1a59e29a-da23-4fb9-8b14-78289f3333cb/download/struttureprivateaccreditate.csv"
    ),
}

# Riquadro del Lazio: serve a scartare le coordinate palesemente sbagliate,
# che nei dataset regionali non sono rare.
LAZIO_BBOX = (40.7, 11.4, 42.9, 14.1)
ROME = (41.8931, 12.4828)

# Strutture private con queste parole nella ragione sociale non sono ambulatori
# dove un cittadino può presentarsi per un problema acuto.
PRIVATE_EXCLUDE = ("rsa", "residenza", "hospice", "riabilitazione", "lungodegenza", "casa di cura")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    d_lat, d_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


def in_lazio(lat: float, lon: float) -> bool:
    return LAZIO_BBOX[0] <= lat <= LAZIO_BBOX[2] and LAZIO_BBOX[1] <= lon <= LAZIO_BBOX[3]


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return None if text in {"", "-", "N/A", "ND"} else text


def title_case(value: str | None) -> str | None:
    """I dataset regionali sono spesso tutto maiuscolo: illeggibile in interfaccia."""
    text = clean(value)
    if text is None:
        return None
    return text.title() if text.isupper() else text


def fetch(url: str) -> str:
    response = httpx.get(url, timeout=120, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return response.content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return response.content.decode("utf-8", errors="replace")


def read_csv(text: str, delimiter: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))


def load_cache() -> dict[str, list[float] | None]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


# I dataset regionali abbreviano i nomi degli istituti in modo che Nominatim non
# riconosce: qui si riportano alla forma estesa usata su OpenStreetMap.
ABBREVIATIONS = (
    ("pol. univ.", "policlinico"),
    ("policlinico universitario", "policlinico"),
    ("osp. gen.", "ospedale"),
    ("osp. di", "ospedale di"),
    ("osp.", "ospedale"),
    ("p.o.", "ospedale"),
    ("c.t.o.", "cto"),
    ("ss.", "santi"),
    ("s. ", "san "),
    ("-fbf", " fatebenefratelli"),
    ("fbf", "fatebenefratelli"),
    ("ist.", "istituto"),
    ("naz.", "nazionale"),
)


def expand(name: str) -> str:
    text = name
    for short, long in ABBREVIATIONS:
        text = text.replace(short, long).replace(short.upper(), long)
        text = text.replace(short.title(), long)
    return " ".join(text.replace("-", " ").split())


# Oltre questa distanza dal centro del proprio comune, un risultato è di un'altra
# struttura omonima: senza questo controllo l'ospedale di Rieti finisce a Roma.
MAX_KM_FROM_TOWN = 20.0


def _nominatim(params: dict[str, str]) -> tuple[float, float] | None:
    """Una richiesta al secondo, come da politica d'uso del servizio."""
    time.sleep(1.1)
    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params | {"format": "json", "limit": "1"},
            headers={"User-Agent": USER_AGENT},
            timeout=25,
        )
        response.raise_for_status()
        results = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    if not results:
        return None
    return (float(results[0]["lat"]), float(results[0]["lon"]))


def geocode_town(town: str, cache: dict) -> tuple[float, float] | None:
    """Centro del comune: serve sia da ripiego sia da metro per validare i risultati."""
    key = f"@comune|{town}"
    if key in cache:
        hit = cache[key]
        return (hit[0], hit[1]) if hit else None

    point = _nominatim({"city": town, "state": "Lazio", "country": "Italy"})
    if point and not in_lazio(*point):
        point = None

    cache[key] = list(point) if point else None
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return point


def geocode_facility(name: str, town: str | None, cache: dict) -> tuple[float, float, str] | None:
    """Coordinate di una struttura, con l'indicazione di quanto sono precise.

    Ritorna `(lat, lon, precisione)` dove la precisione è `esatta` se il punto è
    davvero quello della struttura, `comune` se è stato possibile solo collocarla
    nel proprio centro abitato. Distinguere i due casi è necessario: 89 ospedali
    tutti sul centro di Roma renderebbero insensato il calcolo della struttura più vicina.
    """
    key = f"{name}|{town or ''}"
    if key in cache:
        hit = cache[key]
        return (hit[0], hit[1], hit[2]) if hit else None

    expanded = expand(name)
    centre = geocode_town(town, cache) if town else None

    def acceptable(candidate: tuple[float, float] | None) -> bool:
        if candidate is None or not in_lazio(*candidate):
            return False
        # Senza un centro di riferimento ci si accontenta del riquadro regionale.
        if centre is None:
            return True
        return haversine(*centre, *candidate) <= MAX_KM_FROM_TOWN

    attempts: list[dict[str, str]] = []
    if town:
        # La ricerca strutturata è la più affidabile: vincola davvero al comune.
        attempts.append({"amenity": expanded, "city": town, "country": "Italy"})
        attempts.append({"amenity": f"ospedale {expanded}", "city": town, "country": "Italy"})
        attempts.append({"q": f"{expanded}, {town}", "countrycodes": "it"})
    attempts.append({"q": f"{expanded}, Lazio, Italia", "countrycodes": "it"})

    result: tuple[float, float, str] | None = None
    for params in attempts:
        candidate = _nominatim(params)
        if acceptable(candidate) and candidate is not None:
            result = (candidate[0], candidate[1], "esatta")
            break

    if result is None and centre is not None:
        result = (centre[0], centre[1], "comune")

    cache[key] = list(result) if result else None
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return result


def normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in stripped).split())


# --- Pronto soccorso: anagrafica + code reali ------------------------------------


PS_TYPE_CAPACITY = {"PS": 15, "PS SPEC.": 15, "DEA I": 25, "DEA II": 40}


def build_pronto_soccorso(cache: dict) -> tuple[list[dict], dict]:
    rows = read_csv(fetch(SOURCES["pronto_soccorso"]), ";")
    print(f"  pronto soccorso: {len(rows)} righe")

    facilities: list[dict] = []
    loads: list[dict] = []
    snapshot = None

    for row in rows:
        name = title_case(row.get("ISTITUTO"))
        town = title_case(row.get("COMUNE"))
        if not name:
            continue

        snapshot = snapshot or clean(row.get("DATA"))
        point = geocode_facility(name, town, cache)

        facilities.append(
            {
                "name": f"{name} — Pronto Soccorso",
                "type": "Pronto Soccorso",
                "asl": clean(row.get("ASL")),
                "municipality": town,
                "latitude": point[0] if point else None,
                "longitude": point[1] if point else None,
                "geo_precision": point[2] if point else None,
            }
        )

        def count(field: str) -> int:
            try:
                return int(row.get(field) or 0)
            except ValueError:
                return 0

        loads.append(
            {
                "facility_name": f"{name} — Pronto Soccorso",
                "municipality": town,
                "ps_type": clean(row.get("TIPO")) or "PS",
                "waiting": {
                    "rosso": count("ROSSI_ATT"),
                    "giallo": count("GIALLI_ATT"),
                    "verde": count("VERDI_ATT"),
                    "bianco": count("BIANCHI_ATT"),
                    "non_assegnato": count("NONESEG_ATT"),
                    "totale": count("TOT_ATT"),
                },
                "in_treatment": count("TOT_TRATT"),
                "in_observation": count("TOT_OB"),
                "capacity_hint": PS_TYPE_CAPACITY.get(clean(row.get("TIPO")) or "PS", 20),
            }
        )

    congestion = {
        "source": "Regione Lazio — Pronto Soccorso, accessi in tempo reale (HP-D01)",
        "url": "https://dati.lazio.it/dataset/pronto-soccorso-accessi-in-tempo-reale",
        "snapshot_at": snapshot,
        "note": (
            "Fotografia reale delle code al momento indicato. Il portale regionale non "
            "espone uno storico né un feed aggiornato: questo resta l'ultimo dato pubblico."
        ),
        "items": loads,
    }
    return facilities, congestion


# --- Farmacie -------------------------------------------------------------------


def build_farmacie(today: datetime) -> list[dict]:
    rows = read_csv(fetch(SOURCES["farmacie"]), ";")
    print(f"  farmacie: {len(rows)} righe")

    out: list[dict] = []
    for row in rows:
        end = clean(row.get("DATAFINEVALIDITA"))
        if end:
            try:
                if datetime.strptime(end, "%d/%m/%Y") <= today:
                    continue  # farmacia chiusa
            except ValueError:
                pass

        try:
            lat, lon = float(row["LATITUDINE"]), float(row["LONGITUDINE"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_lazio(lat, lon):
            continue

        town = title_case(row.get("DESCRIZIONECOMUNE"))
        # Alcune coordinate sono chiaramente errate: una farmacia "di Roma" a 40 km
        # dal centro sposterebbe il consiglio sulla struttura sbagliata.
        if town and town.casefold() == "roma" and haversine(*ROME, lat, lon) > 30:
            continue

        out.append(
            {
                "name": f"Farmacia {title_case(row.get('DESCRIZIONEFARMACIA')) or ''}".strip(),
                "type": "Farmacia",
                "municipality": town,
                "province": clean(row.get("SIGLAPROVINCIA")),
                "address": title_case(row.get("INDIRIZZO")),
                "postal_code": clean(row.get("CAP")),
                "latitude": lat,
                "longitude": lon,
                "geo_precision": "esatta",
            }
        )
    return out


# --- Ospedali pubblici ----------------------------------------------------------


def build_ospedali(cache: dict, known: set[str]) -> list[dict]:
    rows = read_csv(fetch(SOURCES["ospedali"]), ",")
    print(f"  ospedali: {len(rows)} righe")

    out: list[dict] = []
    for row in rows:
        name = title_case(row.get("nome_struttura"))
        town = title_case(row.get("comune"))
        if not name or normalize_name(name) in known:
            continue

        point = geocode_facility(name, town, cache)

        out.append(
            {
                "name": name,
                "type": "Ospedale",
                "asl": title_case(row.get("ASL")),
                "municipality": town,
                "province": clean(row.get("provincia")),
                "latitude": point[0] if point else None,
                "longitude": point[1] if point else None,
                "geo_precision": point[2] if point else None,
            }
        )
    return out


# --- Ambulatori privati accreditati ---------------------------------------------


def build_ambulatori() -> list[dict]:
    rows = read_csv(fetch(SOURCES["private"]), ",")
    print(f"  strutture private accreditate: {len(rows)} righe")

    out: list[dict] = []
    for row in rows:
        name = title_case(row.get("NOME PRESIDIO")) or title_case(row.get("RAGIONE SOCIALE"))
        if not name:
            continue
        if any(word in name.casefold() for word in PRIVATE_EXCLUDE):
            continue

        try:
            lat, lon = float(row["Latitude"]), float(row["Longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if not in_lazio(lat, lon):
            continue

        out.append(
            {
                "name": name,
                "type": "Ambulatorio",
                "asl": clean(row.get("ASL")),
                "municipality": title_case(row.get("COMUNE")),
                "address": title_case(row.get("INDIRIZZO")),
                "postal_code": clean(row.get("CAP")),
                "latitude": lat,
                "longitude": lon,
                "geo_precision": "esatta",
            }
        )
    return out


def write_json(path: Path, payload: object, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    size = path.stat().st_size / 1024
    print(f"  scritto {path.relative_to(ROOT)} ({label}, {size:.0f} KB)")


def main() -> int:
    cache = load_cache()
    today = datetime.now()

    print("Scarico i dataset aperti...")
    ps_facilities, congestion = build_pronto_soccorso(cache)
    known = {normalize_name(f["name"].split(" — ")[0]) for f in ps_facilities}

    farmacie = build_farmacie(today)
    ospedali = build_ospedali(cache, known)
    ambulatori = build_ambulatori()

    print("\nScrivo gli output:")
    write_json(FACILITIES / "pronto-soccorso.json", ps_facilities, f"{len(ps_facilities)} PS")
    write_json(FACILITIES / "farmacie.json", farmacie, f"{len(farmacie)} farmacie")
    write_json(FACILITIES / "ospedali.json", ospedali, f"{len(ospedali)} ospedali")
    write_json(FACILITIES / "ambulatori.json", ambulatori, f"{len(ambulatori)} ambulatori")
    write_json(CONGESTION / "pronto-soccorso.json", congestion, "code reali")

    geo = ps_facilities + ospedali
    exact = sum(1 for f in geo if f.get("geo_precision") == "esatta")
    approx = sum(1 for f in geo if f.get("geo_precision") == "comune")
    print(f"\nGeocodifica: {exact} esatte, {approx} al centro del comune, "
          f"{len(geo) - exact - approx} non risolte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
