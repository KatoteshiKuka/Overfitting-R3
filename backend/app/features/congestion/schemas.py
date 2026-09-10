from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class FacilityLoadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    facility_id: int
    ratio: float
    waiting_minutes: int
    people_waiting: int
    source: str
    updated_at: datetime
    #: `basso` | `medio` | `alto`, derivato da `ratio`.
    level: str

    @field_validator("updated_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        # SQLite perde il fuso: i timestamp sono scritti in UTC.
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class CongestionList(BaseModel):
    items: list[FacilityLoadRead]
    total: int
    source: str
