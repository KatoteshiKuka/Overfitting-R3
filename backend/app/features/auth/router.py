from typing import Annotated

from fastapi import APIRouter, Cookie, Response

from app.core.config import get_settings
from app.core.errors import AppError
from app.features.auth import service
from app.features.auth.deps import DbSession
from app.features.auth.providers import (
    HospitalMockAuthProvider,
    MockIdentityProvider,
)
from app.features.auth.schemas import (
    CitizenSession,
    DemoDirectory,
    DemoIdentity,
    HospitalLoginRequest,
    HospitalSession,
    OperatorRead,
    SpidLoginRequest,
    SpidProfileRead,
)
from app.features.citizens import records
from app.features.facilities.models import Facility

router = APIRouter(prefix="/auth", tags=["auth"])

identity_provider = MockIdentityProvider()
hospital_provider = HospitalMockAuthProvider()


def _set_cookie(response: Response, name: str, value: str, max_age_hours: int) -> None:
    # HttpOnly: il JavaScript della pagina non deve poter leggere la sessione.
    # Lax: same-origin attraverso il proxy Vite, quindi funziona in sviluppo.
    response.set_cookie(
        key=name,
        value=value,
        httponly=True,
        samesite="lax",
        max_age=max_age_hours * 3600,
        path="/",
    )


@router.post("/test-spid/login", response_model=CitizenSession)
async def login_citizen(
    db: DbSession,
    payload: SpidLoginRequest,
    response: Response,
    healthpulse_hospital_session: Annotated[str | None, Cookie()] = None,
) -> CitizenSession:
    profile = identity_provider.authenticate(payload.username)
    if profile is None:
        raise AppError(
            "Identità di test non riconosciuta.", code="unknown_identity", status_code=401
        )

    settings = get_settings()
    # Un solo dominio attivo per browser: al refresh non deve riapparire il ruolo precedente.
    service.destroy_session(db, healthpulse_hospital_session)
    response.delete_cookie(service.HOSPITAL_COOKIE, path="/")
    session = service.create_citizen_session(db, profile, identity_provider.name)
    _set_cookie(response, service.CITIZEN_COOKIE, session.session_id, settings.session_hours)

    return CitizenSession(
        provider=identity_provider.name,
        synthetic=True,
        profile=SpidProfileRead(**profile.as_dict()),
        expires_at=session.expires_at,
    )


@router.get("/session", response_model=CitizenSession)
async def read_citizen_session(
    db: DbSession,
    healthpulse_test_session: Annotated[str | None, Cookie()] = None,
) -> CitizenSession:
    session = service.get_session(db, healthpulse_test_session, service.AUDIENCE_CITIZEN)
    if session is None:
        raise AppError("Sessione non valida o scaduta.", code="no_session", status_code=401)

    profile = records.spid_profile_for(session.fiscal_code or "")
    if profile is None:
        # La sessione punta a un'identità che non esiste più nei dati sintetici.
        service.destroy_session(db, session.session_id)
        raise AppError("Identità non più disponibile.", code="no_session", status_code=401)

    return CitizenSession(
        provider=session.provider,
        synthetic=session.synthetic,
        profile=SpidProfileRead(**profile),
        expires_at=session.expires_at,
    )


@router.post("/logout", status_code=204)
async def logout(
    db: DbSession,
    response: Response,
    healthpulse_test_session: Annotated[str | None, Cookie()] = None,
    healthpulse_hospital_session: Annotated[str | None, Cookie()] = None,
) -> None:
    # Idempotente: chiudere una sessione già chiusa non è un errore.
    service.destroy_session(db, healthpulse_test_session)
    service.destroy_session(db, healthpulse_hospital_session)
    response.delete_cookie(service.CITIZEN_COOKIE, path="/")
    response.delete_cookie(service.HOSPITAL_COOKIE, path="/")


@router.post("/hospital/login", response_model=HospitalSession)
async def login_operator(
    db: DbSession,
    payload: HospitalLoginRequest,
    response: Response,
    healthpulse_test_session: Annotated[str | None, Cookie()] = None,
) -> HospitalSession:
    operator = hospital_provider.authenticate(payload.username, payload.facility_id)
    if operator is None:
        raise AppError(
            "Account operatore non riconosciuto.", code="unknown_operator", status_code=401
        )

    facility = db.get(Facility, payload.facility_id)
    if facility is None:
        raise AppError("Struttura non trovata.", code="facility_not_found", status_code=404)

    settings = get_settings()
    service.destroy_session(db, healthpulse_test_session)
    response.delete_cookie(service.CITIZEN_COOKIE, path="/")
    session = service.create_hospital_session(db, operator, hospital_provider.name)
    _set_cookie(response, service.HOSPITAL_COOKIE, session.session_id, settings.session_hours)

    return HospitalSession(
        provider=hospital_provider.name,
        synthetic=True,
        operator=OperatorRead(
            username=operator.username,
            display_name=operator.display_name,
            role=operator.role,
            facility_id=payload.facility_id,
            facility_name=facility.name,
        ),
        expires_at=session.expires_at,
    )


@router.get("/hospital/session", response_model=HospitalSession)
async def read_operator_session(
    db: DbSession,
    healthpulse_hospital_session: Annotated[str | None, Cookie()] = None,
) -> HospitalSession:
    session = service.get_session(db, healthpulse_hospital_session, service.AUDIENCE_HOSPITAL)
    if session is None:
        raise AppError(
            "Sessione operatore non valida o scaduta.", code="no_session", status_code=401
        )

    facility = db.get(Facility, session.facility_id) if session.facility_id else None
    account = hospital_provider.ACCOUNTS.get(session.operator_username or "")

    return HospitalSession(
        provider=session.provider,
        synthetic=session.synthetic,
        operator=OperatorRead(
            username=session.operator_username or "",
            display_name=account.display_name if account else (session.operator_username or ""),
            role=session.operator_role or "OPERATOR_READONLY",
            facility_id=session.facility_id or 0,
            facility_name=facility.name if facility else None,
        ),
        expires_at=session.expires_at,
    )


@router.get("/demo-identities", response_model=DemoDirectory)
async def list_demo_identities() -> DemoDirectory:
    """Identità utilizzabili nella demo. Solo dati sintetici, nessuna password."""
    citizens = [
        DemoIdentity(
            username=row["username"],
            display_name=f"{row['given_name']} {row['family_name']}",
            hero=row.get("hero"),
            care_intent=row["demo_care_intent"],
            note=records.describe_gaps(row),
        )
        for row in records.all_profiles()
    ]
    return DemoDirectory(citizens=citizens, operators=hospital_provider.list_usernames())
