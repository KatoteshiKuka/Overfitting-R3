from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


def _as_utc(value: datetime | None) -> datetime | None:
    # SQLite perde il fuso: i timestamp sono scritti in UTC.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class QueueBreakdown(BaseModel):
    """Composizione reale della coda, per codice colore del dataset regionale."""

    rosso: int
    giallo: int
    verde: int
    bianco: int
    non_assegnato: int
    totale: int


class FacilityLoadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    facility_id: int
    queue: QueueBreakdown
    in_treatment: int
    in_observation: int
    ratio: float
    #: `basso` | `medio` | `alto`, derivato da `ratio`.
    level: str
    source: str
    observed_at: datetime | None = None
    updated_at: datetime

    @field_validator("observed_at", "updated_at")
    @classmethod
    def as_utc(cls, value: datetime | None) -> datetime | None:
        return _as_utc(value)


class CongestionList(BaseModel):
    items: list[FacilityLoadRead]
    total: int
    source: str
    observed_at: datetime | None = None

    @field_validator("observed_at")
    @classmethod
    def as_utc(cls, value: datetime | None) -> datetime | None:
        return _as_utc(value)
