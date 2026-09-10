from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class FacilityRef(BaseModel):
    id: int
    name: str
    municipality: str | None = None


class PressureRead(BaseModel):
    level: str
    ratio: float
    waiting_total: int
    in_treatment: int
    provenance: str
    observed_at: datetime | None = None

    @field_validator("observed_at")
    @classmethod
    def as_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class InboundWindow(BaseModel):
    commitments: int
    weighted: float


class InboundRead(BaseModel):
    next_30_min: InboundWindow
    next_60_min: InboundWindow
    next_4_hours: InboundWindow
    provenance: str = "DERIVED"
    weight_formula: str


class CareMixEntry(BaseModel):
    cluster: str
    label: str
    count: int
    weighted: float


class ReadinessEntry(BaseModel):
    area: str
    level: str
    reason: str


class DeficitEntry(BaseModel):
    qualification: str
    additional_shifts_suggested: int
    candidates_available: int
    reason: str


class ExcludedEntry(BaseModel):
    id: str
    qualification: str
    exclusion_reason: str


class StaffingRead(BaseModel):
    on_shift: int
    on_call: int
    resting: int
    total: int
    deficit: list[DeficitEntry] = []
    excluded: list[ExcludedEntry] = []
    provenance: str = "SIMULATED"
    policy: str = "SIMULATED HR POLICY"
    formula: str


class ConsoleOverview(BaseModel):
    facility: FacilityRef
    pressure: PressureRead
    inbound: InboundRead
    care_mix: list[CareMixEntry]
    expected_pressure_level: str
    readiness: list[ReadinessEntry]
    staffing: StaffingRead
    generated_at: datetime


class CongestionUpdate(BaseModel):
    """Carico dichiarato dall'operatore. Sostituisce lo snapshot storico."""

    waiting_red: int = Field(ge=0, le=500)
    waiting_yellow: int = Field(ge=0, le=500)
    waiting_green: int = Field(ge=0, le=500)
    waiting_white: int = Field(ge=0, le=500)
    waiting_unassigned: int = Field(default=0, ge=0, le=500)
    in_treatment: int = Field(ge=0, le=500)
    in_observation: int = Field(default=0, ge=0, le=500)
    observed_at: datetime | None = None
