from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class SpidLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class SpidProfileRead(BaseModel):
    """Attributi SPID, con i nomi dello standard. Nessuna password, mai."""

    spidCode: str  # noqa: N815 — nome imposto dallo standard SPID
    name: str
    familyName: str  # noqa: N815
    fiscalNumber: str  # noqa: N815
    dateOfBirth: str  # noqa: N815
    placeOfBirth: str  # noqa: N815
    countyOfBirth: str  # noqa: N815
    gender: str
    email: str | None = None
    mobilePhone: str | None = None  # noqa: N815


class CitizenSession(BaseModel):
    authenticated: Literal[True] = True
    provider: str
    synthetic: bool
    profile: SpidProfileRead
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        return _as_utc(value) or value


class HospitalLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    facility_id: int = Field(ge=1)


class OperatorRead(BaseModel):
    username: str
    display_name: str
    role: str
    facility_id: int
    facility_name: str | None = None


class HospitalSession(BaseModel):
    authenticated: Literal[True] = True
    provider: str
    synthetic: bool
    operator: OperatorRead
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        return _as_utc(value) or value


class DemoIdentity(BaseModel):
    """Identità utilizzabili nella demo, mostrate nella schermata di accesso."""

    username: str
    display_name: str
    hero: str | None = None
    care_intent: str
    note: str | None = None


class DemoDirectory(BaseModel):
    citizens: list[DemoIdentity]
    operators: list[str]
    synthetic: bool = True
