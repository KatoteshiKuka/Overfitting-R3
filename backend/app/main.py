"""Bootstrap dell'applicazione.

FILE GLOBALE — append-only. Si aggiunge una riga `include_router` in fondo, non si
riordina e non si riformatta niente. Vedi AGENTS.md.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.errors import register_error_handlers
from app.features.facilities.seed import seed_facilities

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Il database è un artefatto locale: si ricostruisce dai file in data/.
    Base.metadata.create_all(bind=engine)
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_facilities(db, settings.facilities_dir)
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
register_error_handlers(app)

# --- Registro dei router. Aggiungere in fondo, una riga per feature. ---
from app.features.facilities.router import router as facilities_router  # noqa: E402
from app.features.feature_a.router import router as feature_a_router  # noqa: E402
from app.features.feature_b.router import router as feature_b_router  # noqa: E402
from app.features.status.router import router as status_router  # noqa: E402

app.include_router(status_router, prefix=settings.api_prefix)
app.include_router(facilities_router, prefix=settings.api_prefix)
app.include_router(feature_a_router, prefix=settings.api_prefix)
app.include_router(feature_b_router, prefix=settings.api_prefix)
