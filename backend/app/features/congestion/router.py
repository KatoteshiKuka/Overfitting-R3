from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.features.congestion import service
from app.features.congestion.schemas import CongestionList, FacilityLoadRead

router = APIRouter(prefix="/congestion", tags=["congestion"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=CongestionList)
async def list_congestion(db: DbSession) -> CongestionList:
    return service.list_loads(db)


@router.get("/{facility_id}", response_model=FacilityLoadRead)
async def get_congestion(db: DbSession, facility_id: int) -> FacilityLoadRead:
    load = service.get_load(db, facility_id)
    if load is None:
        raise AppError("Nessun dato di carico per questo presidio.", "load_not_found", 404)
    return load
