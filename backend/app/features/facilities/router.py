from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.features.facilities import service
from app.features.facilities.schemas import FacilityList, FacilityRead, FacilitySummary

router = APIRouter(prefix="/facilities", tags=["facilities"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=FacilityList)
async def list_facilities(
    db: DbSession,
    q: Annotated[str | None, Query(description="Ricerca su nome, comune, indirizzo, ASL")] = None,
    type: Annotated[str | None, Query(description="Tipologia normalizzata")] = None,
    asl: Annotated[str | None, Query(description="Azienda sanitaria")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FacilityList:
    return service.list_facilities(db, q=q, type_=type, asl=asl, limit=limit, offset=offset)


@router.get("/summary", response_model=FacilitySummary)
async def get_summary(db: DbSession) -> FacilitySummary:
    return service.summarize_facilities(db)


@router.get("/{facility_id}", response_model=FacilityRead)
async def get_facility(db: DbSession, facility_id: int) -> FacilityRead:
    facility = service.get_facility(db, facility_id)
    if facility is None:
        raise AppError("Presidio non trovato.", code="facility_not_found", status_code=404)
    return facility
