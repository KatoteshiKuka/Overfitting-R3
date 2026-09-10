"""Provider di identità.

L'interfaccia esiste perché un domani al posto del mock ci sia SPID/CIE vero senza
riscrivere il resto: la sessione, il join sul codice fiscale e la pre-accettazione
non sanno da dove arriva l'identità.

`MockIdentityProvider` è l'unico operativo e legge gli stessi 15 profili sintetici che
alimentano il profilo sanitario. `SpidTestEnvProvider` è dichiarato ma **non
implementato**: HealthPulse non è configurato come Service Provider SAML, e fingere che
lo sia sarebbe una dichiarazione falsa. Vedi `docs/SPID_TEST.md`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


@dataclass(frozen=True, slots=True)
class SpidProfile:
    """Attributi SPID, con i nomi che usa davvero lo standard."""

    spid_code: str
    name: str
    family_name: str
    fiscal_number: str
    date_of_birth: str
    place_of_birth: str
    county_of_birth: str
    gender: str
    email: str | None
    mobile_phone: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "spidCode": self.spid_code,
            "name": self.name,
            "familyName": self.family_name,
            "fiscalNumber": self.fiscal_number,
            "dateOfBirth": self.date_of_birth,
            "placeOfBirth": self.place_of_birth,
            "countyOfBirth": self.county_of_birth,
            "gender": self.gender,
            "email": self.email,
            "mobilePhone": self.mobile_phone,
        }


class IdentityProvider(Protocol):
    """Contratto minimo: da un nome utente a un'identità verificata."""

    name: str

    def authenticate(self, username: str) -> SpidProfile | None: ...

    def list_usernames(self) -> list[str]: ...


class MockIdentityProvider:
    """Identità sintetiche, lette da `data/preadmission/profiles.mock.json`.

    Gli attributi SPID sono ricavati **dallo stesso file** che alimenta il profilo
    sanitario: è il modo per garantire che `fiscalNumber` e `fiscal_code` coincidano
    sempre, che è il vincolo su cui si regge tutta la catena.
    """

    name = "spid_test_mock"

    def __init__(self, profiles_path: Path | None = None) -> None:
        settings = get_settings()
        self._path = profiles_path or (
            settings.resolved_data_dir / "preadmission" / "profiles.mock.json"
        )
        self._cache: dict[str, SpidProfile] | None = None

    def _load(self) -> dict[str, SpidProfile]:
        if self._cache is not None:
            return self._cache

        profiles: dict[str, SpidProfile] = {}
        if self._path.exists():
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            for row in payload.get("patients", []):
                profiles[row["username"]] = SpidProfile(
                    spid_code=row["spid_code"],
                    name=row["given_name"],
                    family_name=row["family_name"],
                    fiscal_number=row["fiscal_code"],
                    date_of_birth=row["birth_date"],
                    place_of_birth=row["birth_place"],
                    county_of_birth=row["birth_county"],
                    gender=row["gender"],
                    email=row.get("email"),
                    mobile_phone=row.get("mobile_phone"),
                )
        self._cache = profiles
        return profiles

    def authenticate(self, username: str) -> SpidProfile | None:
        return self._load().get((username or "").strip().casefold())

    def list_usernames(self) -> list[str]:
        return sorted(self._load())


class SpidTestEnvProvider:
    """Segnaposto per `italia/spid-testenv2`.

    NON implementato: completare SAML richiede che HealthPulse sia registrato come
    Service Provider con metadata e certificati, cosa che questo repository non ha.
    Scrivere qui un finto scambio SAML darebbe l'impressione di un'integrazione
    funzionante che non esiste, quindi il metodo fallisce in modo esplicito.
    """

    name = "spid_testenv2"

    def authenticate(self, username: str) -> SpidProfile | None:
        raise NotImplementedError(
            "SpidTestEnvProvider non è collegato a un Service Provider SPID verificato."
        )

    def list_usernames(self) -> list[str]:
        return []


@dataclass(frozen=True, slots=True)
class HospitalOperator:
    """Account del personale di struttura. Dominio distinto da quello cittadino."""

    username: str
    display_name: str
    role: str
    facility_id: int | None


# Ruoli previsti, dal più al meno ampio.
HOSPITAL_ROLES = ("HOSPITAL_ADMIN", "PS_COORDINATOR", "DEPARTMENT_LEAD", "OPERATOR_READONLY")


class HospitalMockAuthProvider:
    """Account operatore finti, legati a una struttura.

    Il personale ospedaliero **non** si autentica con SPID: sono domini diversi, e usare
    l'identità del cittadino per l'accesso operativo confonderebbe due cose che devono
    restare separate anche nel modello.
    """

    name = "hospital_mock"

    ACCOUNTS: dict[str, HospitalOperator] = {
        "ps.coordinator": HospitalOperator(
            "ps.coordinator", "Coordinamento PS", "PS_COORDINATOR", None
        ),
        "hospital.admin": HospitalOperator(
            "hospital.admin", "Direzione sanitaria", "HOSPITAL_ADMIN", None
        ),
        "reparto.lead": HospitalOperator(
            "reparto.lead", "Responsabile di reparto", "DEPARTMENT_LEAD", None
        ),
        "sola.lettura": HospitalOperator(
            "sola.lettura", "Consultazione", "OPERATOR_READONLY", None
        ),
    }

    def authenticate(self, username: str, facility_id: int | None) -> HospitalOperator | None:
        account = self.ACCOUNTS.get((username or "").strip().casefold())
        if account is None:
            return None
        # La struttura la sceglie chi accede: gli account demo non sono legati a un PS.
        return HospitalOperator(
            username=account.username,
            display_name=account.display_name,
            role=account.role,
            facility_id=facility_id,
        )

    def list_usernames(self) -> list[str]:
        return sorted(self.ACCOUNTS)
