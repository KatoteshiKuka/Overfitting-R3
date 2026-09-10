from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.dataset_state import record_load
from app.features.facilities.loader import load_directory
from app.features.facilities.models import Facility

DATASET_NAME = "facilities"


def seed_facilities(db: Session, directory: Path, reset: bool = False) -> int:
    """Carica i presidi da `data/facilities/`. Ritorna il numero di record scritti.

    Idempotente: senza `reset` non fa nulla se il censimento è già popolato, così
    riavviare il server non duplica i dati.
    """
    existing = db.scalar(select(Facility.id).limit(1))
    if existing is not None and not reset:
        return 0

    if reset:
        db.execute(delete(Facility))

    records, files = load_directory(directory)
    db.add_all([Facility(**record.as_dict()) for record in records])
    record_load(db, DATASET_NAME, files=len(files), records=len(records))
    db.commit()
    return len(records)
