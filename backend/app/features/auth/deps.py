"""Dipendenze di autenticazione riusabili dalle altre feature.

Stanno qui e non nel router perché arrivals, citizens e hospital devono poter dire
"questa rotta richiede un cittadino autenticato" senza duplicare la logica del cookie.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.features.auth import service
from app.features.auth.models import AuthSession

DbSession = Annotated[Session, Depends(get_db)]


def current_citizen(
    db: DbSession,
    healthpulse_test_session: Annotated[str | None, Cookie()] = None,
) -> AuthSession:
    """Sessione cittadino valida, altrimenti `401`."""
    session = service.get_session(db, healthpulse_test_session, service.AUDIENCE_CITIZEN)
    if session is None:
        raise AppError("Sessione non valida o scaduta.", code="no_session", status_code=401)
    return session


def current_operator(
    db: DbSession,
    healthpulse_hospital_session: Annotated[str | None, Cookie()] = None,
) -> AuthSession:
    """Sessione operatore valida, altrimenti `401`."""
    session = service.get_session(db, healthpulse_hospital_session, service.AUDIENCE_HOSPITAL)
    if session is None:
        raise AppError(
            "Sessione operatore non valida o scaduta.", code="no_session", status_code=401
        )
    return session


CurrentCitizen = Annotated[AuthSession, Depends(current_citizen)]
CurrentOperator = Annotated[AuthSession, Depends(current_operator)]
