"""Bootstrap dell'applicazione.

FILE GLOBALE — append-only. Si aggiunge una riga `include_router` in fondo, non si
riordina e non si riformatta niente. Vedi AGENTS.md.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.errors import register_error_handlers
from app.core.schema import ensure_schema
from app.features.congestion.service import seed_loads
from app.features.facilities.seed import seed_facilities

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Il database è un artefatto locale: si ricostruisce dai file in data/. Se lo schema
    # non corrisponde più ai modelli lo si rifà da zero, così nessuno resta bloccato con
    # un `no such column` dopo un git pull.
    rebuilt = ensure_schema(engine)
    if settings.auto_seed:
        with SessionLocal() as db:
            seed_facilities(db, settings.facilities_dir, reset=rebuilt)
            # Il carico dipende dai presidi, quindi va generato dopo di loro.
            seed_loads(db, reset=rebuilt)
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
register_error_handlers(app)

# --- Registro dei router. Aggiungere in fondo, una riga per feature. ---
from app.features.facilities.router import router as facilities_router  # noqa: E402
from app.features.feature_b.router import router as feature_b_router  # noqa: E402
from app.features.status.router import router as status_router  # noqa: E402

app.include_router(status_router, prefix=settings.api_prefix)
app.include_router(facilities_router, prefix=settings.api_prefix)
app.include_router(feature_b_router, prefix=settings.api_prefix)

from app.features.congestion.router import router as congestion_router  # noqa: E402
from app.features.triage.router import router as triage_router  # noqa: E402

app.include_router(congestion_router, prefix=settings.api_prefix)
app.include_router(triage_router, prefix=settings.api_prefix)

# --- Feature 2: identità, arrivi e console ospedaliera ---
from app.features.arrivals.router import router as arrivals_router  # noqa: E402
from app.features.auth.router import router as auth_router  # noqa: E402
from app.features.citizens.router import router as citizens_router  # noqa: E402
from app.features.hospital.router import router as hospital_router  # noqa: E402

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(citizens_router, prefix=settings.api_prefix)
app.include_router(arrivals_router, prefix=settings.api_prefix)
app.include_router(hospital_router, prefix=settings.api_prefix)
