from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.triage import service
from app.features.triage.schemas import (
    ChatRequest,
    ChatResponse,
    NearbyRequest,
    NearbyResponse,
    PlanRequest,
    PlanResponse,
    TriageStatus,
)

router = APIRouter(prefix="/triage", tags=["triage"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/messages", response_model=ChatResponse)
async def post_message(payload: ChatRequest) -> ChatResponse:
    return await service.chat(payload.messages)


@router.post("/plan", response_model=PlanResponse)
async def post_plan(db: DbSession, payload: PlanRequest) -> PlanResponse:
    return await service.plan(db, payload.address, payload.code, payload.limit)


@router.post("/nearby", response_model=NearbyResponse)
async def post_nearby(db: DbSession, payload: NearbyRequest) -> NearbyResponse:
    return await service.nearby(db, payload.address, payload.limit)


@router.get("/status", response_model=TriageStatus)
async def get_status() -> TriageStatus:
    return await service.status()
