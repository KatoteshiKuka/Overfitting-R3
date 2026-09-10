"""Lettura dei profili sanitari sintetici.

Fa da `MockRecordProvider`: un domani al suo posto ci sarà il Fascicolo Sanitario, e il
resto dell'applicazione non dovrà cambiare perché conosce solo questa interfaccia.

Il join avviene **sempre sul codice fiscale**, mai sul nome: è il vincolo che tiene
insieme identità SPID, profilo sanitario e pre-accettazione, ed è ciò che rende
dimostrabile l'integrazione futura.

I dati sono caricati una volta e tenuti in memoria: sono quindici righe committate nel
repository, non un archivio che cambia sotto i piedi.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings


def _profiles_path() -> Path:
    return get_settings().resolved_data_dir / "preadmission" / "profiles.mock.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, dict[str, Any]]:
    path = _profiles_path()
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["fiscal_code"]: row for row in payload.get("patients", [])}


def reload() -> None:
    """Svuota la cache: serve ai test, che generano profili diversi."""
    _load.cache_clear()


def all_profiles() -> list[dict[str, Any]]:
    return list(_load().values())


def profile_for(fiscal_code: str) -> dict[str, Any] | None:
    return _load().get((fiscal_code or "").strip().upper())


def spid_profile_for(fiscal_code: str) -> dict[str, str | None] | None:
    """Attributi SPID ricostruiti dal profilo, per rispondere a `GET /auth/session`."""
    row = profile_for(fiscal_code)
    if row is None:
        return None
    return {
        "spidCode": row["spid_code"],
        "name": row["given_name"],
        "familyName": row["family_name"],
        "fiscalNumber": row["fiscal_code"],
        "dateOfBirth": row["birth_date"],
        "placeOfBirth": row["birth_place"],
        "countyOfBirth": row["birth_county"],
        "gender": row["gender"],
        "email": row.get("email"),
        "mobilePhone": row.get("mobile_phone"),
    }


def describe_gaps(row: dict[str, Any]) -> str | None:
    """Cosa manca in questo profilo, in una riga. Serve alla schermata di accesso."""
    gaps: list[str] = []
    if row.get("is_minor"):
        gaps.append("minorenne con tutore")
    if row.get("gp") is None:
        gaps.append("senza medico curante")
    if row.get("emergency_contact") is None and row.get("email") is None:
        gaps.append("senza contatti")
    return ", ".join(gaps) if gaps else None
