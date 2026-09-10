from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.status import service
from app.features.status.schemas import SystemStatus

router = APIRouter(tags=["status"])


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(db: Annotated[Session, Depends(get_db)]) -> SystemStatus:
    return service.get_system_status(db)
