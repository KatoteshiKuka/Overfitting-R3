"""Console operativa della struttura.

Legge **la stessa** tabella `facility_loads` che usa il routing del cittadino: nessuna
copia parallela dei dati di carico, altrimenti le due metà dell'app racconterebbero
storie diverse sullo stesso pronto soccorso.

La vista è aggregata: nessun nome, nessun codice fiscale. Chi organizza un turno ha
bisogno di sapere quanti arrivi aspettarsi e di che tipo, non chi sono le persone.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.features.arrivals import weights
from app.features.arrivals.models import ArrivalCommitment
from app.features.congestion.models import FacilityLoad
from app.features.congestion.waiting import Queue, level_for
from app.features.facilities.models import Facility
from app.features.hospital import staffing
from app.features.hospital.schemas import (
    CareMixEntry,
    ConsoleOverview,
    DeficitEntry,
    ExcludedEntry,
    FacilityRef,
    InboundRead,
    InboundWindow,
    PressureRead,
    ReadinessEntry,
    StaffingRead,
)

# Ordine dei livelli di prontezza, dal più scarico al più teso.
READINESS_ORDER = ("LOW", "MODERATE", "HIGH", "VERY_HIGH")


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _window(rows: list[ArrivalCommitment], minutes: int) -> InboundWindow:
    limit = _now() + timedelta(minutes=minutes)
    selected = [r for r in rows if (_aware(r.expected_arrival_at) or _now()) <= limit]
    return InboundWindow(
        commitments=len(selected),
        weighted=round(sum(r.weight for r in selected), 2),
    )


def _active_commitments(db: Session, facility_id: int) -> list[ArrivalCommitment]:
    stale_limit = _now() - timedelta(hours=3)
    return list(
        db.scalars(
            select(ArrivalCommitment).where(
                ArrivalCommitment.facility_id == facility_id,
                ArrivalCommitment.status.in_(weights.ACTIVE_STATUSES),
                ArrivalCommitment.expected_arrival_at >= stale_limit,
            )
        ).all()
    )


def _readiness(care_mix: list[CareMixEntry], level: str) -> list[ReadinessEntry]:
    """Da che tipo di arrivi ci si aspetta, quali aree conviene preparare.

    È preparazione, non assegnazione: nessun paziente viene mandato a un reparto qui.
    Il triage vero lo fa il personale all'arrivo.
    """
    base = READINESS_ORDER.index(level) if level in READINESS_ORDER else 1
    scores: Counter[str] = Counter()

    for entry in care_mix:
        for area in weights.CLUSTER_TO_AREAS.get(entry.cluster, ()):
            scores[area] += entry.count

    # Il triage è sempre il primo punto toccato da chiunque arrivi.
    scores["Triage"] += sum(entry.count for entry in care_mix)

    out: list[ReadinessEntry] = []
    for area, score in scores.most_common():
        bump = 1 if score >= 3 else 0
        index = min(len(READINESS_ORDER) - 1, base + bump)
        reason = (
            "1 arrivo atteso che può richiedere quest'area"
            if score == 1
            else f"{score} arrivi attesi che possono richiedere quest'area"
        )
        out.append(
            ReadinessEntry(
                area=area,
                level=READINESS_ORDER[index],
                reason=reason,
            )
        )
    return out


def overview(db: Session, facility_id: int) -> ConsoleOverview:
    facility = db.get(Facility, facility_id)
    if facility is None:
        raise AppError("Struttura non trovata.", code="facility_not_found", status_code=404)

    load = db.get(FacilityLoad, facility_id)
    if load is not None:
        queue = Queue(
            rosso=load.waiting_red,
            giallo=load.waiting_yellow,
            verde=load.waiting_green,
            bianco=load.waiting_white,
            non_assegnato=load.waiting_unassigned,
            in_treatment=load.in_treatment,
            capacity_hint=load.capacity_hint,
        )
        pressure = PressureRead(
            level=level_for(load.ratio),
            ratio=load.ratio,
            waiting_total=queue.total,
            in_treatment=load.in_treatment,
            # Lo snapshot regionale è reale ma del 2021: resta HISTORICAL finché un
            # operatore non dichiara il dato attuale.
            provenance="OBSERVED" if load.source == "dichiarato" else "HISTORICAL",
            observed_at=_aware(load.observed_at),
        )
    else:
        pressure = PressureRead(
            level="basso",
            ratio=0.0,
            waiting_total=0,
            in_treatment=0,
            provenance="UNAVAILABLE",
            observed_at=None,
        )

    commitments = _active_commitments(db, facility_id)
    inbound = InboundRead(
        next_30_min=_window(commitments, 30),
        next_60_min=_window(commitments, 60),
        next_4_hours=_window(commitments, 240),
        weight_formula=weights.WEIGHT_FORMULA,
    )

    mix_counter: Counter[str] = Counter()
    mix_weight: Counter[str] = Counter()
    for row in commitments:
        mix_counter[row.care_cluster] += 1
        mix_weight[row.care_cluster] += row.weight

    care_mix = [
        CareMixEntry(
            cluster=cluster,
            label=weights.CLUSTER_LABELS.get(cluster, cluster),
            count=count,
            weighted=round(mix_weight[cluster], 2),
        )
        for cluster, count in mix_counter.most_common()
    ]

    expected = staffing.pressure_level(pressure.ratio, inbound.next_60_min.weighted)
    available_counts = staffing.counts()
    _, excluded = staffing.eligible_for_extra_shift()

    return ConsoleOverview(
        facility=FacilityRef(
            id=facility.id, name=facility.name, municipality=facility.municipality
        ),
        pressure=pressure,
        inbound=inbound,
        care_mix=care_mix,
        expected_pressure_level=expected,
        readiness=_readiness(care_mix, expected),
        staffing=StaffingRead(
            on_shift=available_counts["on_shift"],
            on_call=available_counts["on_call"],
            resting=available_counts["resting"],
            total=available_counts["total"],
            deficit=[
                DeficitEntry(**item)
                for item in staffing.deficit(expected, inbound.next_60_min.weighted)
            ],
            excluded=[
                ExcludedEntry(
                    id=item.id,
                    qualification=item.qualification,
                    exclusion_reason=item.exclusion_reason,
                )
                for item in excluded
            ],
            formula=staffing.SURGE_FORMULA,
        ),
        generated_at=_now(),
    )
