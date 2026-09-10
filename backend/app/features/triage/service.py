"""Orchestrazione del triage: conversazione, valutazione e piano con le strutture."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.features.congestion import service as congestion_service
from app.features.congestion.waiting import level_for
from app.features.facilities.models import Facility
from app.features.triage import geo, llm, rules
from app.features.triage.prompts import (
    PLAN_SCHEMA,
    PLAN_SYSTEM,
    TRIAGE_SCHEMA,
    TRIAGE_SYSTEM,
)
from app.features.triage.schemas import (
    Assessment,
    ChatMessage,
    ChatResponse,
    Origin,
    PlanOption,
    PlanResponse,
    ProviderStatus,
    TriageStatus,
)

# Dove indirizzare ogni codice, quando il modello non lo dice o dice una cosa incoerente.
DEFAULT_SETTING: dict[str, str] = {
    "bianco": "farmacia",
    "verde": "guardia medica",
    "azzurro": "casa della comunità",
    "arancione": "pronto soccorso",
    "rosso": "118",
}

# Tipologie di struttura adatte a ciascun codice, in ordine di preferenza.
CODE_TO_TYPES: dict[str, tuple[str, ...]] = {
    "bianco": ("farmacia", "casa-comunita", "ambulatorio"),
    "verde": ("casa-comunita", "farmacia", "ambulatorio"),
    "azzurro": ("casa-comunita", "ambulatorio", "pronto-soccorso"),
    "arancione": ("pronto-soccorso", "ospedale"),
    "rosso": ("pronto-soccorso", "ospedale"),
}

# Oltre questa soglia il pronto soccorso è considerato congestionato.
BUSY_RATIO = 0.85


def _last_user_text(messages: list[ChatMessage]) -> str:
    return " ".join(m.content for m in messages if m.role == "user")


def _fallback_reply(match: rules.RuleMatch) -> ChatResponse:
    """Risposta senza LLM: le regole bastano a dare un esito utile e prudente."""
    code = match.code
    setting = DEFAULT_SETTING[code]
    assessment = Assessment(
        code=code,
        reason=match.reason,
        care_setting=setting,
        advice=(
            "Chiama subito il 118 e resta dove sei."
            if code == "rosso"
            else f"Rivolgiti a: {setting}. Se i sintomi peggiorano, chiama il 118."
        ),
        escalated=False,
        red_flags=list(match.matched) if match.is_alarming else [],
    )
    return ChatResponse(
        reply=(
            f"{match.reason} In base a quello che mi hai scritto ti conviene rivolgerti a: "
            f"{setting}."
        ),
        done=True,
        assessment=assessment,
        provider="regole",
    )


async def chat(messages: list[ChatMessage]) -> ChatResponse:
    """Un turno di conversazione. Le regole restano sempre l'ultima parola sulla gravità."""
    user_text = _last_user_text(messages)
    rule_match = rules.classify(user_text)

    payload = [{"role": "system", "content": TRIAGE_SYSTEM}]
    payload += [{"role": m.role, "content": m.content} for m in messages]

    try:
        result = await llm.complete_json(payload, TRIAGE_SCHEMA)
    except llm.LlmUnavailableError:
        return _fallback_reply(rule_match)

    data = result.data
    reply = str(data.get("reply") or "").strip()
    if not reply:
        return _fallback_reply(rule_match)

    done = bool(data.get("done"))
    if not done:
        # Ancora in fase di domande: nessuna valutazione da restituire.
        return ChatResponse(reply=reply, done=False, assessment=None, provider=result.provider)

    model_code = str(data.get("code") or "")
    if not rules.is_valid_code(model_code):
        model_code = rule_match.code

    # Le bandiere rosse possono solo alzare la gravità, mai abbassarla.
    final_code = rules.max_code(model_code, rule_match.code) if rule_match.matched else model_code
    raised = final_code != model_code

    # Una correzione da bianco a verde non è un allarme: si segnala solo quando il codice
    # finisce in territorio urgente, altrimenti l'avviso perde credibilità.
    escalated = raised and final_code in {"arancione", "rosso"}

    setting = str(data.get("care_setting") or "").strip() or DEFAULT_SETTING[final_code]
    if raised:
        # Se il codice è stato corretto, il consiglio del modello non vale più.
        setting = DEFAULT_SETTING[final_code]

    assessment = Assessment(
        code=final_code,
        reason=str(data.get("reason") or rule_match.reason).strip(),
        care_setting=setting,
        advice=str(data.get("advice") or "").strip()
        or f"Rivolgiti a: {setting}. Se peggiori, chiama il 118.",
        escalated=escalated,
        # Solo i sintomi davvero preoccupanti: un mal di gola non è una bandiera rossa.
        red_flags=list(rule_match.matched) if rule_match.is_alarming else [],
    )

    if escalated:
        reply = (
            f"{reply}\n\nAttenzione: da quello che hai descritto la situazione può essere più "
            f"seria. Ti indirizzo comunque a: {setting}."
        )

    return ChatResponse(reply=reply, done=True, assessment=assessment, provider=result.provider)


def _candidates(db: Session, code: str) -> list[Facility]:
    """Strutture adatte al codice, solo quelle geolocalizzate: senza coordinate non c'è mappa."""
    preferred = CODE_TO_TYPES.get(code, CODE_TO_TYPES["azzurro"])
    rows = db.scalars(
        select(Facility)
        .where(Facility.type.in_(preferred))
        .where(Facility.latitude.is_not(None))
        .where(Facility.longitude.is_not(None))
    ).all()
    return list(rows)


async def plan(db: Session, address: str, code: str, limit: int) -> PlanResponse:
    """Dalla posizione della persona alle strutture migliori, con tempi calcolati."""
    origin = await geo.geocode(address)
    if origin is None:
        raise AppError(
            "Non ho trovato questo indirizzo nel Lazio. Prova ad aggiungere il comune.",
            code="address_not_found",
            status_code=422,
        )

    facilities = _candidates(db, code)
    if not facilities:
        raise AppError(
            "Nessuna struttura adatta è georeferenziata nei dataset caricati.",
            code="no_geolocated_facility",
            status_code=404,
        )

    loads = congestion_service.loads_by_facility(db)

    # Il percorso stradale si chiede solo per le più vicine in linea d'aria: una chiamata
    # OSRM per ogni struttura del Lazio sarebbe lentissima e inutile.
    def distance(facility: Facility) -> float:
        return geo.haversine_km(
            origin.latitude, origin.longitude, facility.latitude or 0.0, facility.longitude or 0.0
        )

    # Le strutture collocate solo al centro del comune hanno distanze inaffidabili:
    # entrano in classifica soltanto se quelle georeferenziate con precisione non bastano.
    exact = sorted((f for f in facilities if f.geo_precision != "comune"), key=distance)
    approximate = sorted((f for f in facilities if f.geo_precision == "comune"), key=distance)

    wanted = max(limit, 3)
    shortlist = exact[:wanted]
    if len(shortlist) < wanted:
        shortlist += approximate[: wanted - len(shortlist)]

    options: list[PlanOption] = []
    for facility in shortlist:
        route = await geo.route_between(origin, facility.latitude or 0.0, facility.longitude or 0.0)
        load = loads.get(facility.id)
        # L'attesa dipende da chi hai davanti: un codice bianco passa dopo tutti gli altri.
        waiting = congestion_service.waiting_minutes_for(load, code) if load else 0
        ratio = load.ratio if load else 0.0

        options.append(
            PlanOption(
                facility_id=facility.id,
                name=facility.name,
                type=facility.type,
                address=facility.address,
                municipality=facility.municipality,
                latitude=facility.latitude or 0.0,
                longitude=facility.longitude or 0.0,
                distance_km=route.distance_km,
                travel_minutes=route.travel_minutes,
                waiting_minutes=waiting,
                total_minutes=route.travel_minutes + waiting,
                congestion_level=level_for(ratio),
                congestion_ratio=round(ratio, 3),
                route_source=route.source,
                geo_precision=facility.geo_precision,
                route_geometry=[list(point) for point in route.geometry],
            )
        )

    options.sort(key=lambda option: option.total_minutes)
    options = options[:limit]
    if options:
        options[0].recommended = True

    advice, provider = await _plan_advice(code, options)
    return PlanResponse(
        origin=Origin(label=origin.label, latitude=origin.latitude, longitude=origin.longitude),
        options=options,
        advice=advice,
        provider=provider,
    )


def _deterministic_advice(code: str, options: list[PlanOption]) -> str:
    if code == "rosso":
        return (
            "Chiama subito il 118: non metterti in viaggio da solo. "
            "L'ambulanza ti porta alla struttura attrezzata più vicina."
        )
    if not options:
        return "Nessuna struttura disponibile nei dati caricati."

    best = options[0]
    where = f"{best.name} ({best.municipality or 'Lazio'})"
    timing = f"circa {best.travel_minutes} minuti di viaggio e {best.waiting_minutes} di attesa"
    if code in {"bianco", "verde"}:
        return (
            f"Per un problema come il tuo il pronto soccorso non serve: ti conviene {where}, "
            f"{timing}, in tutto circa {best.total_minutes} minuti. Andare al pronto soccorso "
            "significherebbe aspettare molto di più e togliere spazio a chi sta peggio."
        )
    return (
        f"L'opzione più rapida è {where}: {timing}, in tutto circa {best.total_minutes} minuti. "
        "Se durante il tragitto peggiori, chiama il 118."
    )


async def _plan_advice(code: str, options: list[PlanOption]) -> tuple[str, str]:
    """Il consiglio lo scrive l'LLM, ma solo sui numeri già calcolati."""
    fallback = _deterministic_advice(code, options)
    if not options:
        return fallback, "regole"

    summary = "\n".join(
        f"- {o.name} ({o.type}, {o.municipality or 'Lazio'}): {o.distance_km} km, "
        f"{o.travel_minutes} min di viaggio, {o.waiting_minutes} min di attesa, "
        f"totale {o.total_minutes} min, affollamento {o.congestion_level}"
        for o in options
    )
    payload = [
        {"role": "system", "content": PLAN_SYSTEM},
        {
            "role": "user",
            "content": f"Codice di triage: {code}\nStrutture disponibili:\n{summary}",
        },
    ]

    try:
        result = await llm.complete_json(payload, PLAN_SCHEMA)
    except llm.LlmUnavailableError:
        return fallback, "regole"

    advice = str(result.data.get("advice") or "").strip()
    return (advice or fallback), (result.provider if advice else "regole")


async def status() -> TriageStatus:
    providers = await llm.provider_health()
    return TriageStatus(
        providers=[ProviderStatus(**item) for item in providers],
        # Le regole non dipendono da nulla: sono sempre disponibili.
        fallback_ready=True,
    )
