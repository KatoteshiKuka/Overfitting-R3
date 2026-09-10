from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CommitmentStatus = Literal["CONFIRMED", "EN_ROUTE", "ARRIVED", "CANCELLED", "EXPIRED"]


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class Consents(BaseModel):
    share_arrival: bool = True
    share_preadmission: bool = False
    share_reason: bool = False


class CommitmentCreate(BaseModel):
    """Il codice fiscale **non** compare: arriva dalla sessione autenticata."""

    facility_id: int = Field(ge=1)
    eta_minutes: int = Field(ge=0, le=600)
    care_intent: str | None = Field(default=None, max_length=40)
    care_cluster: str | None = Field(default=None, max_length=32)
    consents: Consents = Consents()


class CommitmentRead(BaseModel):
    commitment_id: str
    facility_id: int
    facility_name: str | None = None
    status: CommitmentStatus
    care_intent: str | None = None
    care_cluster: str
    eta_minutes: int
    created_at: datetime
    expected_arrival_at: datetime
    weight: float
    weight_formula: str
    provenance: str = "DERIVED"
    synthetic: bool = True

    @field_validator("created_at", "expected_arrival_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        return _as_utc(value) or value


class CommitmentList(BaseModel):
    items: list[CommitmentRead]
    total: int


class PreadmissionCreate(BaseModel):
    commitment_id: str = Field(min_length=1, max_length=40)
    #: Contatti e note aggiunti dalla persona: l'unica parte non derivata dai dati.
    contact_phone: str | None = Field(default=None, max_length=40)
    contact_name: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    consents: Consents = Consents()


class PersonRef(BaseModel):
    given_name: str
    family_name: str
    relationship: str | None = None
    phone: str | None = None


class PreadmissionIdentity(BaseModel):
    given_name: str
    family_name: str
    fiscal_code: str
    birth_date: str
    is_minor: bool
    guardian: PersonRef | None = None


class PreadmissionClinical(BaseModel):
    exemptions: list[dict[str, str]] = []
    chronic_conditions: list[str] = []
    gp: PersonRef | None = None


class PreadmissionProvenance(BaseModel):
    identity: str = "SYNTHETIC"
    clinical: str = "SYNTHETIC"
    input: str = "USER"


class PreadmissionRead(BaseModel):
    code: str
    commitment_id: str
    status: Literal["issued", "accepted", "expired"]
    created_at: datetime
    expires_at: datetime
    #: Sempre `null`: HealthPulse non pre-assegna il triage ospedaliero.
    triage_hint: None = None
    care_cluster: str
    facility_id: int
    facility_name: str | None = None
    identity: PreadmissionIdentity
    clinical_context: PreadmissionClinical
    user_input: dict[str, str | None] = {}
    provenance: PreadmissionProvenance = PreadmissionProvenance()
    synthetic: bool = True

    @field_validator("created_at", "expires_at")
    @classmethod
    def as_utc(cls, value: datetime) -> datetime:
        return _as_utc(value) or value
