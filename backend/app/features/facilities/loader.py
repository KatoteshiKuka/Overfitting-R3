"""Normalizzazione dei dataset grezzi di `data/facilities/` in record uniformi.

Tutte le funzioni qui sono pure e non toccano il database: si possono importare e testare
da qualsiasi branch senza effetti collaterali. Per supportare un dataset nuovo di solito
basta aggiungere un alias in `FIELD_ALIASES` o una parola chiave in `TYPE_KEYWORDS`.
"""

from __future__ import annotations

import csv
import json
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

TYPE_OTHER = "altro"

# Categorie usate dai filtri dell'interfaccia. L'ordine conta: la prima che matcha vince,
# quindi le più specifiche stanno prima (un "Pronto Soccorso Ospedaliero" è un PS, non un ospedale).
TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("pronto-soccorso", ("pronto soccorso", "prontosoccorso", "pronto-soccorso", "dea", "triage")),
    ("casa-comunita", ("casa della comunita", "casa di comunita", "casa comunita", "cdc")),
    ("farmacia", ("farmacia", "parafarmacia")),
    ("ambulatorio", ("ambulatorio", "poliambulatorio", "consultorio", "distretto")),
    ("ospedale", ("ospedale", "ospedaliera", "presidio ospedaliero", "clinica", "policlinico")),
]

# Sigle che vanno confrontate per intero: come sottostringa darebbero falsi positivi.
TYPE_EXACT: dict[str, str] = {
    "ps": "pronto-soccorso",
    "po": "ospedale",
    "cdc": "casa-comunita",
}

# Nomi di colonna accettati per ciascun campo normalizzato (confronto insensibile a
# maiuscole, accenti, spazi e underscore).
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "name": (
        "name",
        "nome",
        "denominazione",
        "denominazionestruttura",
        "descrizionestruttura",
        "struttura",
        "presidio",
        "denominazionepresidio",
        "ragionesociale",
    ),
    "type": (
        "type",
        "tipologia",
        "tipo",
        "tipostruttura",
        "tipologiastruttura",
        "categoria",
        "natura",
        "descrizionetipologia",
    ),
    "asl": (
        "asl",
        "azienda",
        "aziendasanitaria",
        "codiceasl",
        "descrizioneasl",
        "ente",
        "aziendaospedaliera",
    ),
    "municipality": (
        "municipality",
        "comune",
        "citta",
        "localita",
        "descrizionecomune",
        "comunestruttura",
    ),
    "province": ("province", "provincia", "siglaprovincia", "prov"),
    "address": ("address", "indirizzo", "via", "sede", "indirizzosede", "ubicazione"),
    "postal_code": ("postalcode", "cap", "codicepostale"),
    "latitude": ("latitude", "latitudine", "lat", "coordy", "y"),
    "longitude": ("longitude", "longitudine", "lon", "lng", "long", "coordx", "x"),
    "beds": ("beds", "postiletto", "postilettototali", "npostiletto", "pl", "totalepostiletto"),
    "phone": ("phone", "telefono", "tel", "recapito", "contatto", "numerotelefono"),
    "geo_precision": ("geoprecision", "precisione"),
}

_ALIAS_TO_FIELD: dict[str, str] = {
    alias: field for field, aliases in FIELD_ALIASES.items() for alias in aliases
}


@dataclass(frozen=True, slots=True)
class FacilityRecord:
    """Presidio normalizzato, pronto per essere scritto a DB."""

    name: str
    type: str = TYPE_OTHER
    asl: str | None = None
    municipality: str | None = None
    province: str | None = None
    address: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    beds: int | None = None
    phone: str | None = None
    geo_precision: str | None = None
    source: str = ""

    @property
    def dedup_key(self) -> tuple[str, str]:
        return (self.name.casefold(), (self.municipality or "").casefold())

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_key(value: str) -> str:
    """`POSTI LETTO`, `posti_letto` e `Posti Letto` diventano tutti `postiletto`."""
    cleaned = strip_accents(value).casefold()
    return "".join(char for char in cleaned if char.isalnum())


def normalize_text(value: str) -> str:
    """Testo minuscolo, senza accenti, con separatori ridotti a spazi singoli."""
    cleaned = strip_accents(value).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in cleaned).split())


def normalize_type(raw: object) -> str:
    if raw is None:
        return TYPE_OTHER
    text = normalize_text(str(raw))
    if not text:
        return TYPE_OTHER
    if text in TYPE_EXACT:
        return TYPE_EXACT[text]
    for canonical, keywords in TYPE_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return canonical
    return TYPE_OTHER


def clean_str(raw: object, max_length: int | None = None) -> str | None:
    if raw is None:
        return None
    text = " ".join(str(raw).split())
    if not text or text.casefold() in {"nan", "null", "none", "-", "n/a", "nd", "n.d."}:
        return None
    return text[:max_length] if max_length else text


def parse_float(raw: object) -> float | None:
    """I portali italiani esportano spesso i decimali con la virgola."""
    text = clean_str(raw)
    if text is None:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def parse_int(raw: object) -> int | None:
    value = parse_float(raw)
    return int(value) if value is not None else None


def map_record(raw: dict[str, object], source: str = "") -> FacilityRecord | None:
    """Traduce un record grezzo nello schema normalizzato. `None` se manca il nome."""
    fields: dict[str, object] = {}
    for raw_key, raw_value in raw.items():
        if raw_key is None:
            continue
        field = _ALIAS_TO_FIELD.get(normalize_key(str(raw_key)))
        # Il primo alias trovato vince: evita che una colonna secondaria sovrascriva la principale.
        if field is not None and fields.get(field) in (None, ""):
            fields[field] = raw_value

    name = clean_str(fields.get("name"), 255)
    if name is None:
        return None

    return FacilityRecord(
        name=name,
        type=normalize_type(fields.get("type")),
        asl=clean_str(fields.get("asl"), 120),
        municipality=clean_str(fields.get("municipality"), 120),
        province=clean_str(fields.get("province"), 8),
        address=clean_str(fields.get("address"), 255),
        postal_code=clean_str(fields.get("postal_code"), 16),
        latitude=parse_float(fields.get("latitude")),
        longitude=parse_float(fields.get("longitude")),
        beds=parse_int(fields.get("beds")),
        phone=clean_str(fields.get("phone"), 64),
        geo_precision=clean_str(fields.get("geo_precision"), 16),
        source=source,
    )


def read_text(path: Path) -> str:
    """I dataset dei portali arrivano con encoding disomogenei: si prova in cascata."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_json_records(path: Path) -> list[dict[str, object]]:
    payload = json.loads(read_text(path))
    if isinstance(payload, dict):
        # Molti export incapsulano le righe in una chiave contenitore.
        for key in ("result", "records", "data", "items", "features"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                nested = nested.get("records") or nested.get("data")
            if isinstance(nested, list):
                payload = nested
                break
        else:
            payload = [payload]
    return [row for row in payload if isinstance(row, dict)]


def read_csv_records(path: Path) -> list[dict[str, object]]:
    text = read_text(path)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    return [dict(row) for row in reader]


def read_file(path: Path) -> list[dict[str, object]]:
    if path.suffix.casefold() == ".json":
        return read_json_records(path)
    if path.suffix.casefold() in {".csv", ".tsv", ".txt"}:
        return read_csv_records(path)
    return []


def load_directory(directory: Path) -> tuple[list[FacilityRecord], list[Path]]:
    """Legge tutti i dataset di una cartella e ne restituisce i record deduplicati.

    Ritorna anche i file effettivamente letti, così lo stato di sistema può dire
    all'utente quanti dataset sono stati caricati.
    """
    if not directory.is_dir():
        return [], []

    records: list[FacilityRecord] = []
    seen: set[tuple[str, str]] = set()
    used_files: list[Path] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            rows = read_file(path)
        except (json.JSONDecodeError, csv.Error, OSError):
            # Un file illeggibile non deve impedire il caricamento degli altri.
            continue
        if not rows:
            continue

        used_files.append(path)
        for row in rows:
            record = map_record(row, source=path.name)
            if record is None or record.dedup_key in seen:
                continue
            seen.add(record.dedup_key)
            records.append(record)

    return records, used_files
