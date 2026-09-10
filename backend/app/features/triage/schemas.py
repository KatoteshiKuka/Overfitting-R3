from typing import Literal

from pydantic import BaseModel, Field

TriageCode = Literal["bianco", "verde", "azzurro", "arancione", "rosso"]

Role = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=2000)


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
