from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ArrivalCommitment(Base):
    """Dichiarazione del cittadino di stare andando in una struttura.

    Non è una prenotazione e non è una promessa vincolante: è revocabile in qualsiasi
    momento, senza conseguenze. Nel modello **non esiste alcun campo punitivo** — niente
    blacklist, niente punteggio, niente segnalazione. Un mancato arrivo serve solo a
    tarare l'affidabilità aggregata delle previsioni, mai a giudicare la persona.
    """

    __tablename__ = "arrival_commitments"

    commitment_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    #: Ricavato dalla sessione autenticata: il client non lo può scegliere.
    fiscal_code: Mapped[str] = mapped_column(String(16), index=True)
    facility_id: Mapped[int] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), index=True
    )

    status: Mapped[str] = mapped_column(String(16), index=True, default="CONFIRMED")
    care_intent: Mapped[str | None] = mapped_column(String(40), default=None)
    #: Raggruppamento di preparazione, non una diagnosi e non un reparto.
    care_cluster: Mapped[str] = mapped_column(String(32), default="other")

    eta_minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expected_arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    share_arrival: Mapped[bool] = mapped_column(Boolean, default=True)
    share_preadmission: Mapped[bool] = mapped_column(Boolean, default=False)
    share_reason: Mapped[bool] = mapped_column(Boolean, default=False)

    #: Peso usato dalle previsioni: un impegno non è un arrivo certo.
    weight: Mapped[float] = mapped_column(Float, default=0.75)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class PreadmissionToken(Base):
    """Token di pre-accettazione, monouso e a scadenza breve.

    Serve a far riconoscere la persona all'accettazione senza che i dati viaggino nel
    QR: nel codice c'è solo un identificativo, il contenuto resta sul server.
    """

    __tablename__ = "preadmission_tokens"

    code: Mapped[str] = mapped_column(String(24), primary_key=True)
    commitment_id: Mapped[str] = mapped_column(
        ForeignKey("arrival_commitments.commitment_id", ondelete="CASCADE"), index=True
    )
    fiscal_code: Mapped[str] = mapped_column(String(16), index=True)

    #: `issued` → `accepted`. Scaduto si legge da `expires_at`.
    status: Mapped[str] = mapped_column(String(16), default="issued")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    accepted_by: Mapped[str | None] = mapped_column(String(64), default=None)

    #: Contatti e consensi inseriti a mano dalla persona, in JSON.
    user_input: Mapped[str] = mapped_column(String(2000), default="{}")
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
