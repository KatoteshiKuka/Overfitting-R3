from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base


class DatasetLoad(Base):
    """Traccia dell'ultimo caricamento di una cartella di `data/`, letta dallo stato di sistema."""

    __tablename__ = "dataset_loads"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    files: Mapped[int] = mapped_column(Integer, default=0)
    records: Mapped[int] = mapped_column(Integer, default=0)
    last_loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


def record_load(db: Session, name: str, files: int, records: int) -> DatasetLoad:
    entry = db.get(DatasetLoad, name) or DatasetLoad(name=name)
    entry.files = files
    entry.records = records
    entry.last_loaded_at = datetime.now(UTC)
    db.add(entry)
    return entry
