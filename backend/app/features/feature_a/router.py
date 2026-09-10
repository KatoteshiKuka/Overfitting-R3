"""Slot feature A — da assegnare in TASKS.md.

Chi prende questo slot: definisci il contratto in STATE.md, poi sostituisci questo router
con quello vero e aggiungi `schemas.py`, `models.py`, `service.py` in questa cartella.
Il prefisso e la registrazione in `main.py` esistono già: non serve toccare file globali.
"""

from fastapi import APIRouter

from app.core.errors import AppError

router = APIRouter(prefix="/feature-a", tags=["feature-a"])


@router.get("", response_model=dict[str, str])
async def placeholder() -> dict[str, str]:
    raise AppError(
        "Feature A non ancora assegnata. Vedi TASKS.md.",
        code="not_implemented",
        status_code=501,
    )
