from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.errors import AppError
from app.features.arrivals import service as arrivals_service
from app.features.arrivals.schemas import IncomingPatientRead
from app.features.auth.deps import CurrentOperator, DbSession
from app.features.congestion.models import FacilityLoad
from app.features.congestion.schemas import FacilityLoadRead
from app.features.congestion.service import to_read
from app.features.congestion.waiting import Queue, load_ratio
from app.features.hospital import service
from app.features.hospital.schemas import CongestionUpdate, ConsoleOverview

router = APIRouter(tags=["hospital"])

# Chi può dichiarare il carico del proprio pronto soccorso.
WRITE_ROLES = {"HOSPITAL_ADMIN", "PS_COORDINATOR"}


@router.get("/hospital/console/overview", response_model=ConsoleOverview)
async def console_overview(db: DbSession, operator: CurrentOperator) -> ConsoleOverview:
    """Vista aggregata della propria struttura. Nessun dato nominativo."""
    if not operator.facility_id:
        raise AppError(
            "Sessione operatore senza struttura.", code="facility_not_found", status_code=400
        )
    return service.overview(db, operator.facility_id)


@router.get("/hospital/incoming-patients", response_model=list[IncomingPatientRead])
async def incoming_patients(db: DbSession, operator: CurrentOperator) -> list[IncomingPatientRead]:
    """Resoconti condivisi con la struttura, disponibili già prima del check-in."""
    if not operator.facility_id:
        raise AppError(
            "Sessione operatore senza struttura.", code="facility_not_found", status_code=400
        )
    return arrivals_service.list_incoming_for_facility(db, operator.facility_id)


@router.put("/congestion/{facility_id}", response_model=FacilityLoadRead)
async def declare_congestion(
    db: DbSession, operator: CurrentOperator, facility_id: int, payload: CongestionUpdate
) -> FacilityLoadRead:
    """L'operatore dichiara il carico reale del proprio pronto soccorso.

    Scrive sulla stessa riga che legge il routing cittadino, quindi l'effetto è
    immediato su tutta l'applicazione: da qui in poi quel presidio non è più uno
    snapshot storico ma un dato osservato.
    """
    if operator.operator_role not in WRITE_ROLES:
        raise AppError(
            "Il tuo ruolo non può dichiarare il carico.", code="forbidden", status_code=403
        )
    if operator.facility_id != facility_id:
        raise AppError("Puoi aggiornare solo la tua struttura.", code="forbidden", status_code=403)

    row = db.get(FacilityLoad, facility_id)
    if row is None:
        row = FacilityLoad(facility_id=facility_id)
        db.add(row)

    row.waiting_red = payload.waiting_red
    row.waiting_yellow = payload.waiting_yellow
    row.waiting_green = payload.waiting_green
    row.waiting_white = payload.waiting_white
    row.waiting_unassigned = payload.waiting_unassigned
    row.waiting_total = (
        payload.waiting_red
        + payload.waiting_yellow
        + payload.waiting_green
        + payload.waiting_white
        + payload.waiting_unassigned
    )
    row.in_treatment = payload.in_treatment
    row.in_observation = payload.in_observation
    row.ratio = load_ratio(
        Queue(
            rosso=payload.waiting_red,
            giallo=payload.waiting_yellow,
            verde=payload.waiting_green,
            bianco=payload.waiting_white,
            non_assegnato=payload.waiting_unassigned,
            in_treatment=payload.in_treatment,
            capacity_hint=row.capacity_hint or 20,
        )
    )
    row.source = "dichiarato"
    row.observed_at = payload.observed_at or datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    db.commit()

    return to_read(row)
