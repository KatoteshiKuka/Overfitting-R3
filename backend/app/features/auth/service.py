"""Gestione delle sessioni di accesso.

Due domini separati sotto la stessa tabella: `citizen` e `hospital`. Non sono
intercambiabili — un operatore non diventa cittadino cambiando cookie, perché ogni
lettura filtra sull'`audience` attesa.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.features.auth.models import AuthSession
from app.features.auth.providers import HospitalOperator, SpidProfile

CITIZEN_COOKIE = "healthpulse_test_session"
HOSPITAL_COOKIE = "healthpulse_hospital_session"

AUDIENCE_CITIZEN = "citizen"
AUDIENCE_HOSPITAL = "hospital"


def _now() -> datetime:
    return datetime.now(UTC)


def _expiry() -> datetime:
    return _now() + timedelta(hours=get_settings().session_hours)


def _new_id() -> str:
    # Identificativo opaco: nel cookie non finisce nessun dato personale.
    return secrets.token_urlsafe(32)


def create_citizen_session(db: Session, profile: SpidProfile, provider: str) -> AuthSession:
    session = AuthSession(
        session_id=_new_id(),
        audience=AUDIENCE_CITIZEN,
        provider=provider,
        fiscal_code=profile.fiscal_number,
        expires_at=_expiry(),
        synthetic=True,
    )
    db.add(session)
    db.commit()
    return session


def create_hospital_session(db: Session, operator: HospitalOperator, provider: str) -> AuthSession:
    session = AuthSession(
        session_id=_new_id(),
        audience=AUDIENCE_HOSPITAL,
        provider=provider,
        operator_username=operator.username,
        operator_role=operator.role,
        facility_id=operator.facility_id,
        expires_at=_expiry(),
        synthetic=True,
    )
    db.add(session)
    db.commit()
    return session


def get_session(db: Session, session_id: str | None, audience: str) -> AuthSession | None:
    """Sessione valida per quel dominio, oppure `None`.

    Una sessione scaduta viene rimossa qui: è il momento in cui ce ne accorgiamo, e
    lasciarla in tabella significherebbe solo accumulare righe morte.
    """
    if not session_id:
        return None

    session = db.get(AuthSession, session_id)
    if session is None or session.audience != audience:
        return None

    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)

    if expires <= _now():
        db.delete(session)
        db.commit()
        return None

    session.last_seen_at = _now()
    db.commit()
    return session


def destroy_session(db: Session, session_id: str | None) -> None:
    """Chiude la sessione. Idempotente: il logout non deve mai fallire."""
    if not session_id:
        return
    db.execute(delete(AuthSession).where(AuthSession.session_id == session_id))
    db.commit()


def purge_expired(db: Session) -> int:
    rows = db.scalars(select(AuthSession).where(AuthSession.expires_at <= _now())).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)
