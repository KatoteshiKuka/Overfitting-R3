from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FacilityLoad(Base):
    """Carico di un presidio: quanto è affollato e quanto si aspetta.

    Oggi i valori sono generati in modo deterministico (vedi `service.py`) perché gli
    Open Data non espongono la saturazione in tempo reale. La tabella è scrivibile
    proprio per questo: quando arriveranno i dataset reali — o la feature dedicata al
    personale di reparto — basterà aggiornare le righe senza toccare il resto.
    """

    __tablename__ = "facility_loads"

    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), primary_key=True
    )
    #: Rapporto 0–1 tra occupazione e capienza.
    ratio: Mapped[float] = mapped_column(Float, default=0.0)
    waiting_minutes: Mapped[int] = mapped_column(Integer, default=0)
    people_waiting: Mapped[int] = mapped_column(Integer, default=0)
    #: `stimato` finché non arrivano dati reali, poi `dichiarato` o `open-data`.
    source: Mapped[str] = mapped_column(String(32), default="stimato")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
