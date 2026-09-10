from fastapi import APIRouter

from app.features.arrivals import service
from app.features.arrivals.schemas import (
    CommitmentCreate,
    CommitmentList,
    CommitmentRead,
    PreadmissionCreate,
    PreadmissionRead,
)
from app.features.auth.deps import CurrentCitizen, CurrentOperator, DbSession

router = APIRouter(tags=["arrivals"])


@router.post("/arrivals/commitments", response_model=CommitmentRead, status_code=201)
async def create_commitment(
    db: DbSession, session: CurrentCitizen, payload: CommitmentCreate
) -> CommitmentRead:
    """Il cittadino conferma che si sta dirigendo in una struttura.

    Non viene mai creato in automatico dopo un consiglio: serve un gesto esplicito.
    """
    return service.create_commitment(db, session.fiscal_code or "", payload)


@router.get("/arrivals/commitments/mine", response_model=CommitmentList)
async def list_my_commitments(db: DbSession, session: CurrentCitizen) -> CommitmentList:
    items = service.list_mine(db, session.fiscal_code or "")
    return CommitmentList(items=items, total=len(items))


@router.post("/arrivals/commitments/{commitment_id}/cancel", response_model=CommitmentRead)
async def cancel_commitment(
    db: DbSession, session: CurrentCitizen, commitment_id: str
) -> CommitmentRead:
    """Revoca sempre possibile: nessuna penalità, nessun flag sul cittadino."""
    return service.set_status(db, session.fiscal_code or "", commitment_id, "CANCELLED")


@router.post("/arrivals/commitments/{commitment_id}/en-route", response_model=CommitmentRead)
async def start_travel(
    db: DbSession, session: CurrentCitizen, commitment_id: str
) -> CommitmentRead:
    return service.set_status(db, session.fiscal_code or "", commitment_id, "EN_ROUTE")


@router.post("/navigation/preadmission", response_model=PreadmissionRead, status_code=201)
async def create_preadmission(
    db: DbSession, session: CurrentCitizen, payload: PreadmissionCreate
) -> PreadmissionRead:
    return service.create_preadmission(db, session.fiscal_code or "", payload)


@router.get("/admission/resolve/{code}", response_model=PreadmissionRead)
async def resolve_preadmission(
    db: DbSession, operator: CurrentOperator, code: str
) -> PreadmissionRead:
    """Lettura del codice allo sportello: richiede una sessione operatore."""
    del operator
    return service.resolve_preadmission(db, code)


@router.post("/admission/{code}/accept", response_model=PreadmissionRead)
async def accept_preadmission(
    db: DbSession, operator: CurrentOperator, code: str
) -> PreadmissionRead:
    return service.accept_preadmission(db, code, operator.operator_username or "")
