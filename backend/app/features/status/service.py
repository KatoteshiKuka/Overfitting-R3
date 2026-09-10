from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dataset_state import DatasetLoad
from app.features.facilities.models import Facility
from app.features.status.schemas import DatasetStatus, SystemStatus

# Cartelle di `data/` che l'interfaccia mostra sempre, anche quando sono ancora vuote:
# così chi clona il repo vede subito quali dataset mancano.
KNOWN_DATASETS = ("facilities", "congestion")


def get_system_status(db: Session) -> SystemStatus:
    settings = get_settings()

    facilities_count = db.scalar(select(func.count()).select_from(Facility)) or 0
    asl_count = (
        db.scalar(select(func.count(func.distinct(Facility.asl))).where(Facility.asl.is_not(None)))
        or 0
    )

    loaded = {row.name: row for row in db.scalars(select(DatasetLoad)).all()}
    datasets = [
        DatasetStatus(
            name=name,
            files=loaded[name].files if name in loaded else 0,
            records=loaded[name].records if name in loaded else 0,
            last_loaded_at=loaded[name].last_loaded_at if name in loaded else None,
        )
        for name in KNOWN_DATASETS
    ]

    return SystemStatus(
        status="ok",
        version=settings.version,
        data_loaded=facilities_count > 0,
        facilities_count=facilities_count,
        asl_count=asl_count,
        datasets=datasets,
    )
