"""Copertura dei turni e stima del fabbisogno.

Principio che regge tutto il modulo: **HealthPulse misura, segnala e propone; decide una
persona.** Nessuna chiamata automatica, nessuna assegnazione: la console produce una
proposta che un responsabile deve rivedere e approvare.

I turni sono `SIMULATED` e i vincoli applicati (riposo minimo, soglia settimanale) sono
parametri di demo, non una verifica di conformità normativa. Chi non è eleggibile viene
scartato **conservando il motivo**: un'esclusione senza spiegazione è inutilizzabile.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings

SURGE_FORMULA = "surge_deficit.v1"

# Quante persone in più servono, per livello di pressione, ogni dieci arrivi attesi.
# Valori di demo, non tarati su dati reali.
STAFF_PER_TEN_ARRIVALS: dict[str, float] = {
    "LOW": 0.0,
    "MODERATE": 1.0,
    "HIGH": 2.0,
    "VERY_HIGH": 3.0,
}

LEVELS = ("LOW", "MODERATE", "HIGH", "VERY_HIGH")


@dataclass(frozen=True, slots=True)
class Excluded:
    id: str
    qualification: str
    exclusion_reason: str


def _path() -> Path:
    return get_settings().resolved_data_dir / "staffing" / "internal_shifts.mock.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    path = _path()
    if not path.exists():
        return {"staff": [], "minimum_rest_hours": 11, "weekly_hours_threshold": 44}
    return json.loads(path.read_text(encoding="utf-8"))


def reload() -> None:
    _load.cache_clear()


def roster() -> list[dict[str, Any]]:
    return list(_load().get("staff", []))


def counts() -> dict[str, int]:
    people = roster()
    return {
        "on_shift": sum(1 for p in people if p["status"] == "IN_TURNO"),
        "on_call": sum(1 for p in people if p["status"] == "REPERIBILE"),
        "resting": sum(1 for p in people if p["status"] == "RIPOSO"),
        "total": len(people),
    }


def eligible_for_extra_shift() -> tuple[list[dict[str, Any]], list[Excluded]]:
    """Chi potrebbe coprire un turno aggiuntivo, e chi no e perché.

    Si valutano solo le persone non già in turno: chiamare chi sta lavorando non
    aggiunge copertura.
    """
    data = _load()
    min_rest = int(data.get("minimum_rest_hours", 11))
    weekly_max = int(data.get("weekly_hours_threshold", 44))

    available: list[dict[str, Any]] = []
    excluded: list[Excluded] = []

    for person in roster():
        if person["status"] == "IN_TURNO":
            continue

        rest = person.get("hours_since_last_shift")
        if rest is not None and rest < min_rest:
            excluded.append(
                Excluded(
                    id=person["id"],
                    qualification=person["qualification"],
                    exclusion_reason=f"Riposo minimo non rispettato ({rest}h su {min_rest}h)",
                )
            )
            continue

        weekly = int(person.get("weekly_hours", 0))
        if weekly >= weekly_max:
            excluded.append(
                Excluded(
                    id=person["id"],
                    qualification=person["qualification"],
                    exclusion_reason=f"Soglia settimanale raggiunta ({weekly}h)",
                )
            )
            continue

        available.append(person)

    return available, excluded


def pressure_level(load_ratio: float, weighted_inbound: float) -> str:
    """Livello di pressione atteso, in categorie.

    Deliberatamente non una percentuale: dietro non c'è un modello validato, e mostrare
    un "85% previsto" darebbe una precisione che non abbiamo.
    """
    score = load_ratio + min(1.0, weighted_inbound / 10.0)
    if score < 0.6:
        return "LOW"
    if score < 1.1:
        return "MODERATE"
    if score < 1.6:
        return "HIGH"
    return "VERY_HIGH"


def deficit(level: str, weighted_inbound: float) -> list[dict[str, Any]]:
    """Turni aggiuntivi suggeriti, per qualifica. Da rivedere e approvare a mano."""
    per_ten = STAFF_PER_TEN_ARRIVALS.get(level, 0.0)
    if per_ten <= 0 or weighted_inbound <= 0:
        return []

    needed = max(1, round(per_ten * weighted_inbound / 10.0))
    available, _ = eligible_for_extra_shift()

    proposals: list[dict[str, Any]] = []
    # Gli infermieri sono il collo di bottiglia in pronto soccorso, quindi si parte da lì.
    for qualification, share in (("INFERMIERE", 0.6), ("MEDICO", 0.3), ("OSS", 0.1)):
        suggested = round(needed * share)
        if suggested <= 0:
            continue
        pool = [p for p in available if p["qualification"] == qualification]
        proposals.append(
            {
                "qualification": qualification,
                "additional_shifts_suggested": min(suggested, len(pool)),
                "candidates_available": len(pool),
                "reason": (f"Pressione attesa {level} con {weighted_inbound:.1f} arrivi ponderati"),
            }
        )
    return proposals
