"""Carico dei presidi, dai dati aperti della Regione Lazio.

I conteggi arrivano da `data/congestion/pronto-soccorso.json`, prodotto da
`scripts/fetch_open_data.py` a partire dal dataset regionale degli accessi ai pronto
soccorso. Non c'è nessun valore inventato: se una struttura non è nel dataset, non ha
dati di carico e l'interfaccia lo dice invece di riempire il vuoto con una stima.
"""

from __future__ import annotations

import json
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dataset_state import record_load
from app.features.congestion.models import FacilityLoad
from app.features.congestion.schemas import CongestionList, FacilityLoadRead, QueueBreakdown
from app.features.congestion.waiting import Queue, estimate_wait, level_for, load_ratio
from app.features.facilities.models import Facility

DATASET_NAME = "congestion"


def _key(name: str, municipality: str | None) -> str:
    """Chiave di abbinamento tolleante a maiuscole, accenti e punteggiatura."""
    raw = f"{name}|{municipality or ''}"
    decomposed = unicodedata.normalize("NFKD", raw)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    return " ".join("".join(c if c.isalnum() or c == "|" else " " for c in stripped).split())


def _parse_observed(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _read_source(directory: Path) -> tuple[list[dict], str, datetime | None]:
    if not directory.is_dir():
        return [], "assente", None

    items: list[dict] = []
    label = "open-data"
    observed: datetime | None = None

    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        items.extend(entry for entry in payload.get("items", []) if isinstance(entry, dict))
        label = payload.get("source") or label
        observed = observed or _parse_observed(payload.get("snapshot_at"))

    return items, label, observed


def seed_loads(db: Session, reset: bool = False) -> int:
    """Carica le code reali abbinandole ai presidi già censiti."""
    existing = db.scalar(select(FacilityLoad.facility_id).limit(1))
    if existing is not None and not reset:
        return 0
    if reset:
        db.execute(delete(FacilityLoad))

    settings = get_settings()
    items, label, observed = _read_source(settings.congestion_dir)
    if not items:
        record_load(db, DATASET_NAME, files=0, records=0)
        db.commit()
        return 0

    index = {
        _key(facility.name, facility.municipality): facility.id
        for facility in db.scalars(select(Facility)).all()
    }

    written = 0
    for entry in items:
        facility_id = index.get(_key(entry.get("facility_name", ""), entry.get("municipality")))
        if facility_id is None:
            continue

        waiting = entry.get("waiting") or {}
        queue = Queue(
            rosso=int(waiting.get("rosso") or 0),
            giallo=int(waiting.get("giallo") or 0),
            verde=int(waiting.get("verde") or 0),
            bianco=int(waiting.get("bianco") or 0),
            non_assegnato=int(waiting.get("non_assegnato") or 0),
            in_treatment=int(entry.get("in_treatment") or 0),
            capacity_hint=int(entry.get("capacity_hint") or 20),
        )

        db.add(
            FacilityLoad(
                facility_id=facility_id,
                waiting_red=queue.rosso,
                waiting_yellow=queue.giallo,
                waiting_green=queue.verde,
                waiting_white=queue.bianco,
                waiting_unassigned=queue.non_assegnato,
                waiting_total=int(waiting.get("totale") or queue.total),
                in_treatment=queue.in_treatment,
                in_observation=int(entry.get("in_observation") or 0),
                capacity_hint=queue.capacity_hint,
                ratio=load_ratio(queue),
                source="open-data",
                observed_at=observed,
            )
        )
        written += 1

    record_load(db, DATASET_NAME, files=1, records=written)
    db.commit()
    return written


def to_queue(row: FacilityLoad) -> Queue:
    return Queue(
        rosso=row.waiting_red,
        giallo=row.waiting_yellow,
        verde=row.waiting_green,
        bianco=row.waiting_white,
        non_assegnato=row.waiting_unassigned,
        in_treatment=row.in_treatment,
        capacity_hint=row.capacity_hint,
    )


def waiting_minutes_for(row: FacilityLoad, app_code: str) -> int:
    """Attesa stimata per chi arriva con quel codice di triage."""
    return estimate_wait(to_queue(row), app_code)


def to_read(row: FacilityLoad) -> FacilityLoadRead:
    return FacilityLoadRead(
        facility_id=row.facility_id,
        queue=QueueBreakdown(
            rosso=row.waiting_red,
            giallo=row.waiting_yellow,
            verde=row.waiting_green,
            bianco=row.waiting_white,
            non_assegnato=row.waiting_unassigned,
            totale=row.waiting_total,
        ),
        in_treatment=row.in_treatment,
        in_observation=row.in_observation,
        ratio=row.ratio,
        level=level_for(row.ratio),
        source=row.source,
        observed_at=row.observed_at,
        updated_at=row.updated_at,
    )


def list_loads(db: Session) -> CongestionList:
    rows = db.scalars(select(FacilityLoad)).all()
    settings = get_settings()
    _, label, observed = _read_source(settings.congestion_dir)
    return CongestionList(
        items=[to_read(row) for row in rows],
        total=len(rows),
        source=label if rows else "assente",
        observed_at=observed,
    )


def get_load(db: Session, facility_id: int) -> FacilityLoadRead | None:
    row = db.get(FacilityLoad, facility_id)
    return to_read(row) if row else None


def loads_by_facility(db: Session) -> dict[int, FacilityLoad]:
    """Indice per id, usato dal piano di triage per non fare una query per struttura."""
    return {row.facility_id: row for row in db.scalars(select(FacilityLoad)).all()}
