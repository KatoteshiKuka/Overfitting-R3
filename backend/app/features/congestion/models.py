from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FacilityLoad(Base):
    """Carico di un presidio: chi c'è in coda, per codice colore, e quanto si aspetta.

    I dati arrivano dal dataset regionale "Pronto Soccorso - accessi in tempo reale"
    (`data/congestion/`), che è una fotografia reale delle code. La tabella è scrivibile
    perché il portale non espone un feed aggiornato: quando la feature dedicata al
    personale sarà pronta, saranno gli operatori ad aggiornare queste righe.

    Le code sono tenute divise per colore, non aggregate: l'attesa di chi arriva dipende
    da quante persone più gravi ha davanti, ed è l'unico modo per calcolarla davvero.
    """

    __tablename__ = "facility_loads"

    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), primary_key=True
    )

    waiting_red: Mapped[int] = mapped_column(Integer, default=0)
    waiting_yellow: Mapped[int] = mapped_column(Integer, default=0)
    waiting_green: Mapped[int] = mapped_column(Integer, default=0)
    waiting_white: Mapped[int] = mapped_column(Integer, default=0)
    waiting_unassigned: Mapped[int] = mapped_column(Integer, default=0)
    waiting_total: Mapped[int] = mapped_column(Integer, default=0)

    #: Persone già prese in carico: è la misura della capacità di smaltimento attuale.
    in_treatment: Mapped[int] = mapped_column(Integer, default=0)
    in_observation: Mapped[int] = mapped_column(Integer, default=0)
    #: Postazioni tipiche della tipologia (PS, DEA I, DEA II).
    capacity_hint: Mapped[int] = mapped_column(Integer, default=20)

    #: Rapporto 0–1 tra coda e capacità di smaltimento.
    ratio: Mapped[float] = mapped_column(Float, default=0.0)
    #: `open-data` quando viene dal dataset regionale, `dichiarato` se aggiornato a mano.
    source: Mapped[str] = mapped_column(String(32), default="open-data")
    #: Momento a cui si riferisce la fotografia, non quello del caricamento.
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
