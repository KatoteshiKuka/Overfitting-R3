from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.facilities.models import Facility
from app.features.facilities.schemas import (
    AslCount,
    FacilityList,
    FacilityRead,
    FacilitySummary,
    TypeCount,
)


def list_facilities(
    db: Session,
    q: str | None = None,
    type_: str | None = None,
    asl: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> FacilityList:
    stmt = select(Facility)

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Facility.name.ilike(pattern),
                Facility.municipality.ilike(pattern),
                Facility.address.ilike(pattern),
                Facility.asl.ilike(pattern),
            )
        )
    if type_:
        stmt = stmt.where(Facility.type == type_)
    if asl:
        stmt = stmt.where(Facility.asl == asl)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Facility.name).limit(limit).offset(offset)).all()

    return FacilityList(
        items=[FacilityRead.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_facility(db: Session, facility_id: int) -> FacilityRead | None:
    row = db.get(Facility, facility_id)
    return FacilityRead.model_validate(row) if row else None


def summarize_facilities(db: Session) -> FacilitySummary:
    total = db.scalar(select(func.count()).select_from(Facility)) or 0

    type_rows = db.execute(
        select(Facility.type, func.count())
        .group_by(Facility.type)
        .order_by(func.count().desc(), Facility.type)
    ).all()

    asl_rows = db.execute(
        select(Facility.asl, func.count())
        .where(Facility.asl.is_not(None))
        .group_by(Facility.asl)
        .order_by(func.count().desc(), Facility.asl)
    ).all()

    municipalities = (
        db.scalar(
            select(func.count(func.distinct(Facility.municipality))).where(
                Facility.municipality.is_not(None)
            )
        )
        or 0
    )

    return FacilitySummary(
        total=total,
        by_type=[TypeCount(type=row[0], count=row[1]) for row in type_rows],
        by_asl=[AslCount(asl=row[0], count=row[1]) for row in asl_rows],
        municipalities=municipalities,
    )
