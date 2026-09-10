from fastapi import APIRouter

from app.core.errors import AppError
from app.features.auth.deps import CurrentCitizen
from app.features.citizens import records
from app.features.citizens.schemas import (
    CitizenProfile,
    EpisodeRead,
    ExemptionRead,
    PersonRef,
)

router = APIRouter(prefix="/citizens", tags=["citizens"])


def _person(raw: dict[str, str] | None) -> PersonRef | None:
    if not raw:
        return None
    return PersonRef(
        given_name=raw["given_name"],
        family_name=raw["family_name"],
        relationship=raw.get("relationship"),
        phone=raw.get("phone"),
    )


@router.get("/me/profile", response_model=CitizenProfile)
async def read_my_profile(session: CurrentCitizen) -> CitizenProfile:
    """Profilo dell'utente autenticato.

    L'identità arriva dalla sessione, non dal client: nessuna dropdown, nessun codice
    fiscale accettato dalla richiesta.
    """
    row = records.profile_for(session.fiscal_code or "")
    if row is None:
        raise AppError("Profilo non trovato.", code="profile_not_found", status_code=404)

    return CitizenProfile(
        fiscal_code=row["fiscal_code"],
        given_name=row["given_name"],
        family_name=row["family_name"],
        birth_date=row["birth_date"],
        birth_place=row["birth_place"],
        is_minor=row["is_minor"],
        guardian=_person(row.get("guardian")),
        gp=_person(row.get("gp")),
        emergency_contact=_person(row.get("emergency_contact")),
        email=row.get("email"),
        mobile_phone=row.get("mobile_phone"),
        exemptions=[ExemptionRead(**e) for e in row.get("exemptions", [])],
        chronic_conditions=list(row.get("chronic_conditions", [])),
        recent_episodes=[EpisodeRead(**e) for e in row.get("recent_episodes", [])],
        demo_care_intent=row["demo_care_intent"],
        hero=row.get("hero"),
    )
