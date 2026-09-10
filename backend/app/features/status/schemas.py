from datetime import UTC, datetime

from pydantic import BaseModel, field_validator


class DatasetStatus(BaseModel):
    name: str
    files: int
    records: int
    last_loaded_at: datetime | None = None

    @field_validator("last_loaded_at")
    @classmethod
    def as_utc(cls, value: datetime | None) -> datetime | None:
        # SQLite perde il fuso: i timestamp sono scritti in UTC, qui glielo si riattacca.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class SystemStatus(BaseModel):
    status: str
    version: str
    data_loaded: bool
    facilities_count: int
    asl_count: int
    datasets: list[DatasetStatus]
