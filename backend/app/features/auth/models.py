from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuthSession(Base):
    """Sessione di accesso, tenuta lato server.

    Nel browser resta soltanto un identificativo opaco in un cookie `HttpOnly`: codice
    fiscale e dati sanitari non escono mai dal backend, e il client non può cambiare
    identità modificando il proprio `localStorage`.
    """

    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    #: `citizen` o `hospital`: due domini distinti, mai intercambiabili.
    audience: Mapped[str] = mapped_column(String(16), index=True, default="citizen")
    provider: Mapped[str] = mapped_column(String(32), default="spid_test_mock")

    #: Identità del cittadino. È la chiave di join con i dati sintetici.
    fiscal_code: Mapped[str | None] = mapped_column(String(16), index=True, default=None)

    #: Identità dell'operatore di struttura.
    operator_username: Mapped[str | None] = mapped_column(String(64), default=None)
    operator_role: Mapped[str | None] = mapped_column(String(32), default=None)
    facility_id: Mapped[int | None] = mapped_column(Integer, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
