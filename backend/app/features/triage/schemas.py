import base64
import binascii
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TriageCode = Literal["bianco", "verde", "azzurro", "arancione", "rosso"]

Role = Literal["user", "assistant"]


class ChatImage(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    data_url: str = Field(min_length=32, max_length=2_666_720)

    @field_validator("data_url")
    @classmethod
    def validate_data_url(cls, value: str) -> str:
        header, separator, encoded = value.partition(",")
        allowed_headers = {
            "data:image/jpeg;base64",
            "data:image/png;base64",
            "data:image/webp;base64",
        }
        if separator != "," or header not in allowed_headers:
            raise ValueError("La foto deve essere JPEG, PNG o WebP")
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("La foto non contiene dati base64 validi") from exc
        if len(decoded) > 2_000_000:
            raise ValueError("La foto non può superare 2 MB")
        return value


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=2000)
    image: ChatImage | None = None

    @model_validator(mode="after")
    def image_only_from_user(self) -> "ChatMessage":
        if self.image is not None and self.role != "user":
            raise ValueError("Solo i messaggi dell'utente possono contenere una foto")
        return self


class Assessment(BaseModel):
    """Esito della valutazione. `escalated` dice se le regole hanno corretto l'LLM."""

    code: TriageCode
    reason: str
    care_setting: str
    advice: str
    escalated: bool = False
    red_flags: list[str] = []


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ChatResponse(BaseModel):
    reply: str
    #: `True` quando la valutazione è conclusa e si può passare alla mappa.
    done: bool
    assessment: Assessment | None = None
    #: `locale`, `groq` o `regole`: mostrato in UI per trasparenza sulla provenienza.
    provider: str


class PlanRequest(BaseModel):
    address: str = Field(min_length=3, max_length=200)
    code: TriageCode
    limit: int = Field(default=5, ge=1, le=20)


class NearbyRequest(BaseModel):
    address: str = Field(min_length=3, max_length=200)
    limit: int = Field(default=8, ge=1, le=20)


class NearbyFacility(BaseModel):
    facility_id: int
    name: str
    type: str
    address: str | None = None
    municipality: str | None = None
    latitude: float
    longitude: float
    distance_km: float
    geo_precision: str | None = None


class PlanOption(BaseModel):
    facility_id: int
    name: str
    type: str
    address: str | None = None
    municipality: str | None = None
    latitude: float
    longitude: float
    distance_km: float
    travel_minutes: int
    waiting_minutes: int
    total_minutes: int
    congestion_level: str
    congestion_ratio: float
    #: `osrm` se il tragitto è reale, `stimato` se in linea d'aria.
    route_source: str
    #: `esatta` o `comune`: quanto è precisa la posizione della struttura.
    geo_precision: str | None = None
    #: Punti [lat, lon] del tragitto, per tracciarlo sulla mappa.
    route_geometry: list[tuple[float, float]] = []
    #: Persone che HealthPulse ha già indirizzato qui e non sono ancora arrivate.
    inbound_people: int = 0
    #: Minuti di attesa in più dovuti a quegli arrivi già promessi.
    inbound_wait_minutes: int = 0
    recommended: bool = False


class Origin(BaseModel):
    label: str
    latitude: float
    longitude: float


class NearbyResponse(BaseModel):
    origin: Origin
    facilities: list[NearbyFacility]


class PlanResponse(BaseModel):
    origin: Origin
    options: list[PlanOption]
    advice: str
    provider: str
    #: Perché la struttura più vicina non è quella consigliata, quando succede.
    crowding_note: str | None = None
    crowding_formula: str = "induced_crowding.v1"


class ProviderStatus(BaseModel):
    name: str
    model: str
    available: bool


class TriageStatus(BaseModel):
    providers: list[ProviderStatus]
    fallback_ready: bool
