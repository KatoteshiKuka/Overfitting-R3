"""Arrival Commitment e pre-accettazione."""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.features.arrivals import weights
from app.features.arrivals.models import ArrivalCommitment, PreadmissionToken
from app.features.arrivals.schemas import (
    CommitmentCreate,
    CommitmentRead,
    IncomingPatientRead,
    PersonRef,
    PreadmissionClinical,
    PreadmissionCreate,
    PreadmissionIdentity,
    PreadmissionRead,
)
from app.features.citizens import records
from app.features.facilities.models import Facility

# La pre-accettazione vale per la durata del viaggio più un margine, non di più:
# un codice che resta valido per giorni non è un token, è un identificativo permanente.
PREADMISSION_TTL = timedelta(hours=6)

# Alfabeto senza caratteri confondibili: il codice va letto ad alta voce allo sportello.
CODE_ALPHABET = "ACDEFGHJKLMNPQRTUVWXY34679"


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _commitment_id() -> str:
    return f"cmt_{secrets.token_hex(10)}"


def _preadmission_code() -> str:
    body = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    return f"PA-{body[:4]}-{body[4:]}"


def _to_read(row: ArrivalCommitment, facility_name: str | None) -> CommitmentRead:
    return CommitmentRead(
        commitment_id=row.commitment_id,
        facility_id=row.facility_id,
        facility_name=facility_name,
        status=row.status,  # type: ignore[arg-type]
        care_intent=row.care_intent,
        care_cluster=row.care_cluster,
        eta_minutes=row.eta_minutes,
        created_at=_aware(row.created_at),
        expected_arrival_at=_aware(row.expected_arrival_at),
        weight=row.weight,
        weight_formula=weights.WEIGHT_FORMULA,
    )


def create_commitment(db: Session, fiscal_code: str, payload: CommitmentCreate) -> CommitmentRead:
    facility = db.get(Facility, payload.facility_id)
    if facility is None:
        raise AppError("Struttura non trovata.", code="facility_not_found", status_code=404)

    cluster = weights.normalize_cluster(
        payload.care_cluster or weights.cluster_for_intent(payload.care_intent)
    )
    now = _now()

    row = ArrivalCommitment(
        commitment_id=_commitment_id(),
        fiscal_code=fiscal_code,
        facility_id=payload.facility_id,
        status="CONFIRMED",
        care_intent=payload.care_intent,
        care_cluster=cluster,
        eta_minutes=payload.eta_minutes,
        created_at=now,
        expected_arrival_at=now + timedelta(minutes=payload.eta_minutes),
        updated_at=now,
        share_arrival=payload.consents.share_arrival,
        share_preadmission=payload.consents.share_preadmission,
        share_reason=payload.consents.share_reason,
        weight=weights.weight_for("CONFIRMED"),
    )
    db.add(row)
    db.commit()
    return _to_read(row, facility.name)


def list_mine(db: Session, fiscal_code: str) -> list[CommitmentRead]:
    rows = db.scalars(
        select(ArrivalCommitment)
        .where(ArrivalCommitment.fiscal_code == fiscal_code)
        .order_by(ArrivalCommitment.created_at.desc())
    ).all()
    names = _facility_names(db, [row.facility_id for row in rows])
    return [_to_read(row, names.get(row.facility_id)) for row in rows]


def _facility_names(db: Session, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    rows = db.execute(select(Facility.id, Facility.name).where(Facility.id.in_(set(ids)))).all()
    return {row[0]: row[1] for row in rows}


def set_status(db: Session, fiscal_code: str, commitment_id: str, status: str) -> CommitmentRead:
    row = db.get(ArrivalCommitment, commitment_id)
    if row is None or row.fiscal_code != fiscal_code:
        raise AppError("Impegno non trovato.", code="commitment_not_found", status_code=404)

    if row.status in {"CANCELLED", "EXPIRED", "ARRIVED"}:
        raise AppError("Questo impegno è già concluso.", code="commitment_closed", status_code=409)

    row.status = status
    row.weight = weights.weight_for(status)
    row.updated_at = _now()
    db.commit()

    facility = db.get(Facility, row.facility_id)
    return _to_read(row, facility.name if facility else None)


def expire_stale(db: Session) -> int:
    """Chiude gli impegni la cui finestra è passata da un pezzo.

    Senza questo, la previsione degli arrivi continuerebbe a contare gente che non
    arriverà mai. Non è una penalità: è solo pulizia della finestra temporale.
    """
    limit = _now() - timedelta(hours=3)
    rows = db.scalars(
        select(ArrivalCommitment).where(
            ArrivalCommitment.status.in_(weights.ACTIVE_STATUSES),
            ArrivalCommitment.expected_arrival_at < limit,
        )
    ).all()
    for row in rows:
        row.status = "EXPIRED"
        row.weight = 0.0
        row.updated_at = _now()
    if rows:
        db.commit()
    return len(rows)


# --- Pre-accettazione ---------------------------------------------------------------


def _person(raw: dict[str, str] | None) -> PersonRef | None:
    if not raw:
        return None
    return PersonRef(
        given_name=raw["given_name"],
        family_name=raw["family_name"],
        relationship=raw.get("relationship"),
        phone=raw.get("phone"),
    )


def _build_read(
    db: Session, token: PreadmissionToken, commitment: ArrivalCommitment
) -> PreadmissionRead:
    profile = records.profile_for(token.fiscal_code) or {}
    facility = db.get(Facility, commitment.facility_id)
    user_input = json.loads(token.user_input or "{}")
    triage_summary = user_input.pop("triage_summary", None)

    status = token.status
    if status == "issued" and _aware(token.expires_at) <= _now():
        status = "expired"

    return PreadmissionRead(
        code=token.code,
        commitment_id=token.commitment_id,
        status=status,  # type: ignore[arg-type]
        created_at=_aware(token.created_at),
        expires_at=_aware(token.expires_at),
        triage_hint=None,
        care_cluster=commitment.care_cluster,
        facility_id=commitment.facility_id,
        facility_name=facility.name if facility else None,
        identity=PreadmissionIdentity(
            given_name=profile.get("given_name", ""),
            family_name=profile.get("family_name", ""),
            fiscal_code=token.fiscal_code,
            birth_date=profile.get("birth_date", ""),
            is_minor=bool(profile.get("is_minor")),
            guardian=_person(profile.get("guardian")),
            email=profile.get("email"),
            mobile_phone=profile.get("mobile_phone"),
        ),
        clinical_context=PreadmissionClinical(
            exemptions=list(profile.get("exemptions", [])),
            chronic_conditions=list(profile.get("chronic_conditions", [])),
            gp=_person(profile.get("gp")),
        ),
        user_input=user_input,
        triage_summary=triage_summary if commitment.share_reason else None,
    )


def create_preadmission(
    db: Session, fiscal_code: str, payload: PreadmissionCreate
) -> PreadmissionRead:
    commitment = db.get(ArrivalCommitment, payload.commitment_id)
    if commitment is None or commitment.fiscal_code != fiscal_code:
        raise AppError("Impegno non trovato.", code="commitment_not_found", status_code=404)
    if commitment.status not in weights.ACTIVE_STATUSES:
        raise AppError("L'impegno non è più attivo.", code="commitment_closed", status_code=409)

    existing = db.scalar(
        select(PreadmissionToken).where(
            PreadmissionToken.commitment_id == commitment.commitment_id,
            PreadmissionToken.status == "issued",
        )
    )
    if existing is not None and _aware(existing.expires_at) > _now():
        # Un secondo codice per lo stesso viaggio confonderebbe solo l'accettazione.
        existing_input = json.loads(existing.user_input or "{}")
        if payload.contact_name is not None:
            existing_input["contact_name"] = payload.contact_name
        if payload.contact_phone is not None:
            existing_input["contact_phone"] = payload.contact_phone
        if payload.notes is not None:
            existing_input["notes"] = payload.notes
        if payload.triage_summary is not None:
            existing_input["triage_summary"] = payload.triage_summary.model_dump()
        existing.user_input = json.dumps(existing_input, ensure_ascii=False)
        commitment.share_preadmission = payload.consents.share_preadmission
        commitment.share_reason = payload.consents.share_reason
        db.commit()
        return _build_read(db, existing, commitment)

    token = PreadmissionToken(
        code=_preadmission_code(),
        commitment_id=commitment.commitment_id,
        fiscal_code=fiscal_code,
        status="issued",
        created_at=_now(),
        expires_at=_now() + PREADMISSION_TTL,
        user_input=json.dumps(
            {
                "contact_name": payload.contact_name,
                "contact_phone": payload.contact_phone,
                "notes": payload.notes,
                "triage_summary": (
                    payload.triage_summary.model_dump() if payload.triage_summary else None
                ),
            },
            ensure_ascii=False,
        ),
    )
    db.add(token)

    commitment.share_preadmission = payload.consents.share_preadmission
    commitment.share_reason = payload.consents.share_reason
    db.commit()

    return _build_read(db, token, commitment)


def list_incoming_for_facility(db: Session, facility_id: int) -> list[IncomingPatientRead]:
    """Resoconti già condivisi con la struttura, disponibili prima del check-in."""
    rows = db.execute(
        select(PreadmissionToken, ArrivalCommitment)
        .join(
            ArrivalCommitment,
            ArrivalCommitment.commitment_id == PreadmissionToken.commitment_id,
        )
        .where(
            ArrivalCommitment.facility_id == facility_id,
            ArrivalCommitment.status.in_((*weights.ACTIVE_STATUSES, "ARRIVED")),
            ArrivalCommitment.share_preadmission.is_(True),
            PreadmissionToken.expires_at >= _now(),
        )
        .order_by(ArrivalCommitment.expected_arrival_at.asc())
    ).all()

    return [
        IncomingPatientRead(
            **_build_read(db, token, commitment).model_dump(),
            commitment_status=commitment.status,
            eta_minutes=commitment.eta_minutes,
            expected_arrival_at=_aware(commitment.expected_arrival_at),
        )
        for token, commitment in rows
    ]


def resolve_preadmission(db: Session, code: str) -> PreadmissionRead:
    token = db.get(PreadmissionToken, code.strip().upper())
    if token is None:
        raise AppError("Codice non trovato.", code="token_not_found", status_code=404)
    if _aware(token.expires_at) <= _now() and token.status == "issued":
        raise AppError("Codice scaduto.", code="token_expired", status_code=410)

    commitment = db.get(ArrivalCommitment, token.commitment_id)
    if commitment is None:
        raise AppError("Impegno non trovato.", code="commitment_not_found", status_code=404)
    return _build_read(db, token, commitment)


def accept_preadmission(db: Session, code: str, operator: str) -> PreadmissionRead:
    token = db.get(PreadmissionToken, code.strip().upper())
    if token is None:
        raise AppError("Codice non trovato.", code="token_not_found", status_code=404)
    if token.status == "accepted":
        raise AppError("Codice già utilizzato.", code="token_already_used", status_code=409)
    if _aware(token.expires_at) <= _now():
        raise AppError("Codice scaduto.", code="token_expired", status_code=410)

    commitment = db.get(ArrivalCommitment, token.commitment_id)
    if commitment is None:
        raise AppError("Impegno non trovato.", code="commitment_not_found", status_code=404)

    token.status = "accepted"
    token.accepted_at = _now()
    token.accepted_by = operator
    # Chi è stato accettato è arrivato: l'impegno vale ora al cento per cento.
    commitment.status = "ARRIVED"
    commitment.weight = weights.weight_for("ARRIVED")
    commitment.updated_at = _now()
    db.commit()

    return _build_read(db, token, commitment)
