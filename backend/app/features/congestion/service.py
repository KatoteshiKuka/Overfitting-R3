"""Carico dei presidi.

I valori attuali sono **finti ma deterministici**: derivano da un hash del nome della
struttura, così restano identici a ogni riavvio e la demo è ripetibile. Un valore casuale
cambierebbe a ogni refresh e non sarebbe difendibile.

Quando arriveranno i dataset reali si sostituisce `synthetic_load` con il caricamento
dei dati veri: il resto dell'applicazione non cambia, perché legge solo la tabella.
"""

from __future__ import annotations

from hashlib import blake2b

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.congestion.models import FacilityLoad
from app.features.congestion.schemas import CongestionList, FacilityLoadRead
from app.features.facilities.models import Facility

# Quanto tende a essere affollata ogni tipologia, e quanto si aspetta al massimo.
TYPE_PROFILE: dict[str, tuple[float, float, int]] = {
    # tipo: (rapporto minimo, rapporto massimo, attesa in minuti a saturazione piena)
    "pronto-soccorso": (0.55, 0.98, 240),
    "ospedale": (0.45, 0.90, 150),
    "casa-comunita": (0.20, 0.65, 45),
    "ambulatorio": (0.25, 0.70, 60),
    "farmacia": (0.05, 0.40, 15),
    "altro": (0.20, 0.60, 40),
}


def _stable_unit(seed: str) -> float:
    """Numero stabile in [0, 1) ricavato dal nome: stesso presidio, stesso valore."""
    digest = blake2b(seed.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") / float(1 << 64)


def synthetic_load(facility: Facility) -> FacilityLoad:
    """Carico plausibile per un presidio, riproducibile e coerente con la tipologia."""
    low, high, max_wait = TYPE_PROFILE.get(facility.type, TYPE_PROFILE["altro"])
    unit = _stable_unit(f"{facility.name}|{facility.municipality or ''}")

    ratio = low + (high - low) * unit
    waiting = round(max_wait * ratio**2)
    # Una struttura più grande smaltisce più persone a parità di saturazione.
    capacity = facility.beds if facility.beds and facility.beds > 0 else 12
    people = round(capacity * ratio)

    return FacilityLoad(
        facility_id=facility.id,
        ratio=round(ratio, 3),
        waiting_minutes=waiting,
        people_waiting=people,
        source="stimato",
    )


def level_for(ratio: float) -> str:
    if ratio < 0.6:
        return "basso"
    if ratio < 0.85:
        return "medio"
    return "alto"


def seed_loads(db: Session, reset: bool = False) -> int:
    """Genera il carico per i presidi che non ne hanno ancora uno."""
    existing = {row for row in db.scalars(select(FacilityLoad.facility_id)).all()}

    created = 0
    for facility in db.scalars(select(Facility)).all():
        if facility.id in existing and not reset:
            continue
        if facility.id in existing:
            db.merge(synthetic_load(facility))
        else:
            db.add(synthetic_load(facility))
        created += 1

    db.commit()
    return created


def to_read(row: FacilityLoad) -> FacilityLoadRead:
    return FacilityLoadRead(
        facility_id=row.facility_id,
        ratio=row.ratio,
        waiting_minutes=row.waiting_minutes,
        people_waiting=row.people_waiting,
        source=row.source,
        updated_at=row.updated_at,
        level=level_for(row.ratio),
    )


def list_loads(db: Session) -> CongestionList:
    rows = db.scalars(select(FacilityLoad)).all()
    items = [to_read(row) for row in rows]
    # Se anche una sola riga è dichiarata da un operatore, non è più tutto stimato.
    sources = {row.source for row in rows}
    source = "misto" if len(sources) > 1 else (next(iter(sources)) if sources else "stimato")
    return CongestionList(items=items, total=len(items), source=source)


def get_load(db: Session, facility_id: int) -> FacilityLoadRead | None:
    row = db.get(FacilityLoad, facility_id)
    return to_read(row) if row else None


def loads_by_facility(db: Session) -> dict[int, FacilityLoad]:
    """Indice per id, usato dal piano di triage per non fare una query per struttura."""
    return {row.facility_id: row for row in db.scalars(select(FacilityLoad)).all()}
