"""Peso e raggruppamento degli arrivi previsti.

Due scelte esplicite, entrambe versionate perché finiscono in una previsione mostrata
a chi organizza un pronto soccorso.

**Un impegno non è un arrivo certo.** Contare `1 commitment = 1 paziente` gonfierebbe la
previsione: chi dichiara di mettersi in viaggio a volte cambia idea, e va bene così.
I pesi qui sotto sono `SIMULATED / CONFIGURED`, scelti per la demo e **non validati
statisticamente**: quando ci saranno dati di ritorno andranno ricalibrati.

**Il cluster non è una diagnosi.** Serve solo a dire al pronto soccorso che tipo di
supporto potrebbe servire di più nelle prossime ore. Non assegna reparti, non anticipa
il triage: quello lo fa il personale all'arrivo, e resta l'unico valido.
"""

from __future__ import annotations

WEIGHT_FORMULA = "commitment_weight.v1"

# Quanto vale un impegno nella previsione, per stato.
STATUS_WEIGHTS: dict[str, float] = {
    "CONFIRMED": 0.75,
    "EN_ROUTE": 0.90,
    "ARRIVED": 1.00,
    "CANCELLED": 0.0,
    "EXPIRED": 0.0,
}

ACTIVE_STATUSES = ("CONFIRMED", "EN_ROUTE")

CARE_CLUSTERS: tuple[str, ...] = (
    "minor_trauma",
    "respiratory",
    "chest_pain_like",
    "abdominal",
    "neurological",
    "other",
)

CLUSTER_LABELS: dict[str, str] = {
    "minor_trauma": "Trauma minore",
    "respiratory": "Respiratorio",
    "chest_pain_like": "Dolore toracico",
    "abdominal": "Addominale",
    "neurological": "Neurologico",
    "other": "Altro",
}

# Aree che un certo tipo di accesso tende a sollecitare. È preparazione, non allocazione.
CLUSTER_TO_AREAS: dict[str, tuple[str, ...]] = {
    "minor_trauma": ("Radiologia", "Ortopedia"),
    "respiratory": ("Medicina PS", "OBI"),
    "chest_pain_like": ("Cardiologia", "Medicina PS"),
    "abdominal": ("Chirurgia", "Radiologia"),
    "neurological": ("Medicina PS", "Radiologia"),
    "other": ("Medicina PS",),
}

# Da intenzione di cura a cluster di preparazione.
INTENT_TO_CLUSTER: dict[str, str] = {
    "minor_wound_care": "minor_trauma",
    "musculoskeletal_minor": "minor_trauma",
    "pediatric_non_urgent": "other",
    "prescription_renewal": "other",
    "medication_advice": "other",
    "vaccination": "other",
    "specimen_collection": "other",
    "specialist_referral": "other",
    "chronic_followup": "other",
}


def weight_for(status: str) -> float:
    return STATUS_WEIGHTS.get(status, 0.0)


def cluster_for_intent(intent: str | None) -> str:
    return INTENT_TO_CLUSTER.get(intent or "", "other")


def normalize_cluster(value: str | None) -> str:
    return value if value in CARE_CLUSTERS else "other"
