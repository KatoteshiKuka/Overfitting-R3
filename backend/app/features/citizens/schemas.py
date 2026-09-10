from pydantic import BaseModel


class PersonRef(BaseModel):
    given_name: str
    family_name: str
    relationship: str | None = None
    phone: str | None = None


class ExemptionRead(BaseModel):
    code: str
    description: str


class EpisodeRead(BaseModel):
    episode_date: str
    facility: str
    reason: str
    outcome: str


class CitizenProfile(BaseModel):
    """Profilo sanitario sintetico.

    I campi assenti sono `null`, mai stringa vuota: l'interfaccia deve poter mostrare
    `UNAVAILABLE` invece di una riga vuota o di un valore inventato.
    """

    fiscal_code: str
    given_name: str
    family_name: str
    birth_date: str
    birth_place: str
    is_minor: bool
    guardian: PersonRef | None = None
    gp: PersonRef | None = None
    emergency_contact: PersonRef | None = None
    email: str | None = None
    mobile_phone: str | None = None
    exemptions: list[ExemptionRead] = []
    chronic_conditions: list[str] = []
    recent_episodes: list[EpisodeRead] = []
    demo_care_intent: str
    hero: str | None = None
    provenance: str = "SYNTHETIC"
    synthetic: bool = True
