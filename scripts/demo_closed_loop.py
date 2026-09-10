#!/usr/bin/env python3
"""Dimostrazione end-to-end: percorre l'intero flusso e stampa cosa succede.

    uv run --with httpx python scripts/demo_closed_loop.py

Serve a due cose: verificare che la catena regga davvero, e avere in demo una prova
riproducibile che la logica funziona — invece di doverla raccontare a parole.

Richiede backend su :8000. Non tocca il codice: usa solo le API pubbliche, esattamente
come farebbe l'interfaccia.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

API = "http://localhost:8000/api/v1"
ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "data" / "preadmission" / "profiles.mock.json"

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"

failures: list[str] = []


def step(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")


def ok(message: str) -> None:
    print(f"  {GREEN}✓{RESET} {message}")


def ko(message: str) -> None:
    failures.append(message)
    print(f"  {RED}✗{RESET} {message}")


def note(message: str) -> None:
    print(f"    {DIM}{message}{RESET}")


def usernames() -> list[str]:
    payload = json.loads(PROFILES.read_text(encoding="utf-8"))
    return [row["username"] for row in payload["patients"]]


def main() -> int:  # noqa: PLR0915 — è uno script lineare, spezzarlo lo renderebbe peggio
    citizen = httpx.Client(base_url=API, timeout=60)
    operator = httpx.Client(base_url=API, timeout=60)

    # --- 1. Autenticazione -----------------------------------------------------------
    step("1. AUTENTICAZIONE")
    response = citizen.post("/auth/test-spid/login", json={"username": "mario.rossi"})
    if response.status_code != 200:
        ko(f"login fallito: {response.status_code} {response.text[:200]}")
        return 1
    profile = response.json()["profile"]
    ok(f"login SPID: {profile['name']} {profile['familyName']} — {profile['fiscalNumber']}")

    session = citizen.get("/auth/session")
    if session.status_code == 200:
        ok("sessione persistente sulla richiesta successiva")
    else:
        ko(f"sessione non mantenuta: {session.status_code}")

    anon = httpx.get(f"{API}/auth/session", timeout=30)
    if anon.status_code == 401:
        ok("senza cookie: 401, come deve essere")
    else:
        ko(f"senza cookie ci si aspetta 401, ottenuto {anon.status_code}")

    # --- 2. Profilo dalla sessione ---------------------------------------------------
    step("2. PROFILO SANITARIO DALLA SESSIONE")
    me = citizen.get("/citizens/me/profile").json()
    ok(f"{me['given_name']} {me['family_name']}, intento «{me['demo_care_intent']}»")
    note(f"medico curante: {me['gp']['family_name'] if me['gp'] else 'UNAVAILABLE'}")
    note(f"il codice fiscale non è mai stato inviato dal client: {me['fiscal_code']}")

    # --- 3. Concorrenza di raccomandazione -------------------------------------------
    step("3. CONCORRENZA DI RACCOMANDAZIONE")
    address = {"address": "Via Nazionale 100, Roma", "code": "arancione", "limit": 5}
    before = citizen.post("/triage/plan", json=address).json()

    print("  prima di saturare:")
    for option in before["options"][:3]:
        note(
            f"{option['name'][:36]:38} totale {option['total_minutes']:3} min "
            f"(viaggio {option['travel_minutes']}, attesa {option['waiting_minutes']}, "
            f"indotta {option['inbound_wait_minutes']})"
        )

    target = before["options"][0]
    print(f"\n  invio 20 persone verso «{target['name'][:40]}»…")
    for index, username in enumerate((usernames() * 2)[:20]):
        other = httpx.Client(base_url=API, timeout=60)
        login = other.post("/auth/test-spid/login", json={"username": username})
        if login.status_code != 200:
            continue
        other.post(
            "/arrivals/commitments",
            json={
                "facility_id": target["facility_id"],
                "eta_minutes": 20 + index % 5,
                "care_intent": "musculoskeletal_minor",
            },
        )
        other.close()
    ok("20 impegni di arrivo creati")

    after = citizen.post("/triage/plan", json=address).json()
    print("\n  dopo la saturazione:")
    for option in after["options"][:3]:
        marker = " ←" if option["facility_id"] == target["facility_id"] else ""
        note(
            f"{option['name'][:36]:38} totale {option['total_minutes']:3} min "
            f"(viaggio {option['travel_minutes']}, attesa {option['waiting_minutes']}, "
            f"indotta {option['inbound_wait_minutes']}){marker}"
        )

    saturated = next(
        (o for o in after["options"] if o["facility_id"] == target["facility_id"]), None
    )
    added = saturated["inbound_wait_minutes"] if saturated else 0
    if added > 0:
        ok(f"attesa indotta riconosciuta sulla struttura satura: +{added} min")
    else:
        ko("l'affollamento indotto non ha avuto effetto")

    if after["options"][0]["facility_id"] != target["facility_id"]:
        ok(f"raccomandazione spostata su «{after['options'][0]['name'][:40]}»")
    else:
        ko("la raccomandazione non è cambiata nonostante 20 invii")

    if after.get("crowding_note"):
        ok("al paziente viene spiegato perché non la più vicina")
        note(after["crowding_note"])
    else:
        ko("manca la spiegazione sull'affollamento")

    note(f"formula: {after['crowding_formula']}")

    # --- 4. Conferma e pre-accettazione ----------------------------------------------
    step("4. CONFERMA ARRIVO E CODICE PER IL CHECK-IN")
    chosen = after["options"][0]
    commitment = citizen.post(
        "/arrivals/commitments",
        json={
            "facility_id": chosen["facility_id"],
            "eta_minutes": chosen["travel_minutes"],
            "care_intent": me["demo_care_intent"],
        },
    ).json()
    ok(
        f"impegno {commitment['commitment_id'][:16]}… stato {commitment['status']}, "
        f"peso {commitment['weight']}"
    )

    preadmission = citizen.post(
        "/navigation/preadmission",
        json={"commitment_id": commitment["commitment_id"], "contact_phone": "+39 333 1112223"},
    ).json()
    code = preadmission["code"]
    ok(f"pre-accettazione {code} — QR generato dall'interfaccia su questo codice")
    if preadmission["triage_hint"] is None:
        ok("triage_hint è null: il triage lo assegna il personale")
    else:
        ko("triage_hint valorizzato: HealthPulse non deve pre-assegnare il triage")

    # --- 5. Console della struttura ---------------------------------------------------
    step("5. CONSOLE DELLA STRUTTURA")
    operator.post(
        "/auth/hospital/login",
        json={"username": "ps.coordinator", "facility_id": chosen["facility_id"]},
    )
    console = operator.get("/hospital/console/overview").json()
    inbound = console["inbound"]
    ok(f"struttura: {console['facility']['name'][:44]}")
    ok(
        f"arrivi 30/60/240 min: {inbound['next_30_min']['commitments']}/"
        f"{inbound['next_60_min']['commitments']}/{inbound['next_4_hours']['commitments']}"
    )
    if console["care_mix"]:
        ok("care mix: " + ", ".join(f"{c['label']} {c['count']}" for c in console["care_mix"]))
    ok(f"pressione prevista: {console['expected_pressure_level']}")

    suggested = sum(x["additional_shifts_suggested"] for x in console["staffing"]["deficit"])
    if suggested > 0:
        ok(f"turni aggiuntivi proposti: {suggested}")
        for entry in console["staffing"]["deficit"]:
            note(
                f"+{entry['additional_shifts_suggested']} {entry['qualification']} "
                f"({entry['candidates_available']} candidati) — {entry['reason']}"
            )
    else:
        note("nessun turno aggiuntivo proposto per la pressione attesa")

    excluded = console["staffing"]["excluded"]
    if excluded:
        ok(f"{len(excluded)} persone escluse, ognuna con il motivo")
        note(f"es. {excluded[0]['id']}: {excluded[0]['exclusion_reason']}")

    for entry in console["readiness"][:3]:
        note(f"prontezza {entry['area']}: {entry['level']}")

    # --- 6. Accettazione allo sportello -----------------------------------------------
    step("6. ACCETTAZIONE CON I DATI DEL PAZIENTE")
    resolved = operator.get(f"/admission/resolve/{code}")
    if resolved.status_code != 200:
        ko(f"lettura del codice fallita: {resolved.status_code} {resolved.text[:160]}")
        return 1
    record = resolved.json()
    identity = record["identity"]
    clinical = record["clinical_context"]
    ok(f"{identity['given_name']} {identity['family_name']} — {identity['fiscal_code']}")
    note(f"nato il {identity['birth_date']}, minorenne: {identity['is_minor']}")
    note(f"medico curante: {clinical['gp']['family_name'] if clinical['gp'] else 'UNAVAILABLE'}")
    note(f"esenzioni: {[e['code'] for e in clinical['exemptions']] or 'nessuna'}")
    note(f"patologie croniche: {clinical['chronic_conditions'] or 'nessuna'}")
    note(f"recapito indicato: {record['user_input'].get('contact_phone')}")

    accepted = operator.post(f"/admission/{code}/accept")
    if accepted.status_code == 200 and accepted.json()["status"] == "accepted":
        ok("arrivo registrato")
    else:
        ko(f"accettazione fallita: {accepted.status_code}")

    again = operator.post(f"/admission/{code}/accept")
    if again.status_code == 409:
        ok(f"riuso del codice rifiutato ({again.json()['code']})")
    else:
        ko(f"il codice andava rifiutato al secondo uso, ottenuto {again.status_code}")

    # --- 7. Revoca senza conseguenze ---------------------------------------------------
    step("7. REVOCA SENZA CONSEGUENZE")
    spare = citizen.post(
        "/arrivals/commitments",
        json={"facility_id": chosen["facility_id"], "eta_minutes": 30},
    ).json()
    cancelled = citizen.post(f"/arrivals/commitments/{spare['commitment_id']}/cancel").json()
    if cancelled["status"] == "CANCELLED" and cancelled["weight"] == 0.0:
        ok("annullato: non pesa più sulle previsioni")
    else:
        ko(f"revoca non applicata: {cancelled['status']}")

    body = json.dumps(cancelled).lower()
    if any(word in body for word in ("no_show", "penal", "blacklist", "reputation")):
        ko("il modello contiene un campo punitivo")
    else:
        ok("nessun campo punitivo: chi cambia idea non viene segnalato")

    citizen.close()
    operator.close()

    print()
    if failures:
        print(f"{RED}{len(failures)} verifiche fallite:{RESET}")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"{GREEN}Tutte le verifiche superate.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
