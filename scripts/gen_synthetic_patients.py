#!/usr/bin/env python3
"""Genera i 15 pazienti sintetici che alimentano identità, profilo e pre-accettazione.

    python3 scripts/gen_synthetic_patients.py [--seed 577156] [--check]

Solo libreria standard. A parità di seme l'output è **byte-identico**: i file sono
committati e non devono cambiare a ogni esecuzione, altrimenti ogni rigenerazione
sporcherebbe il diff.

CSV e JSON derivano dagli **stessi oggetti Python nella stessa esecuzione**: non
esistono due generatori da tenere allineati.

Tutti i profili portano `synthetic: true`. Nessuna persona reale, nessun dato vero:
i codici fiscali sono formalmente validi ma appartengono a identità inventate, e non
vanno usati per interrogare nessun servizio esterno.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from codice_fiscale import encode, is_valid  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "preadmission"

DEFAULT_SEED = 577156

TODAY = date(2026, 9, 10)

# Comuni del Lazio con il rispettivo codice catastale, usato dal codice fiscale.
BIRTHPLACES: list[tuple[str, str, str]] = [
    ("Roma", "RM", "H501"),
    ("Latina", "LT", "E472"),
    ("Frosinone", "FR", "D810"),
    ("Viterbo", "VT", "M082"),
    ("Rieti", "RI", "H282"),
    ("Tivoli", "RM", "L182"),
    ("Anzio", "RM", "A323"),
    ("Velletri", "RM", "L719"),
]

CARE_INTENTS: tuple[str, ...] = (
    "minor_wound_care",
    "prescription_renewal",
    "vaccination",
    "specimen_collection",
    "specialist_referral",
    "chronic_followup",
    "pediatric_non_urgent",
    "musculoskeletal_minor",
    "medication_advice",
)

CHRONIC_CONDITIONS = ("ipertensione", "diabete tipo 2", "asma", "ipotiroidismo", "emicrania cronica")

# Codici di esenzione realmente in uso, con la relativa descrizione.
EXEMPTIONS = (
    ("013", "Diabete mellito"),
    ("031", "Ipertensione arteriosa"),
    ("048", "Patologia oncologica in follow-up"),
    ("007", "Asma bronchiale"),
    ("027", "Ipotiroidismo congenito"),
)

EPISODE_OUTCOMES = ("dimesso", "dimesso con indicazioni", "inviato al medico curante")


@dataclass
class Guardian:
    given_name: str
    family_name: str
    relationship: str
    phone: str


@dataclass
class Contact:
    given_name: str
    family_name: str
    relationship: str
    phone: str


@dataclass
class Gp:
    given_name: str
    family_name: str
    phone: str


@dataclass
class Exemption:
    code: str
    description: str


@dataclass
class Episode:
    episode_date: str
    facility: str
    reason: str
    outcome: str


@dataclass
class Patient:
    """Un paziente sintetico completo. `None` significa dato realmente assente."""

    profile_id: str
    username: str
    spid_code: str
    fiscal_code: str
    given_name: str
    family_name: str
    birth_date: str
    birth_place: str
    birth_county: str
    gender: str
    email: str | None
    mobile_phone: str | None
    is_minor: bool
    demo_care_intent: str
    hero: str | None = None
    guardian: Guardian | None = None
    gp: Gp | None = None
    emergency_contact: Contact | None = None
    exemptions: list[Exemption] = field(default_factory=list)
    chronic_conditions: list[str] = field(default_factory=list)
    recent_episodes: list[Episode] = field(default_factory=list)
    synthetic: bool = True

    @property
    def display_name(self) -> str:
        return f"{self.given_name} {self.family_name}"


# Nomi inventati, scelti per non corrispondere a persone note.
GIVEN_NAMES_M = ("Mario", "Luca", "Giuseppe", "Andrea", "Marco", "Davide", "Simone", "Pietro")
GIVEN_NAMES_F = ("Anna", "Giulia", "Elena", "Chiara", "Sara", "Martina", "Laura", "Federica")
FAMILY_NAMES = (
    "Rossi", "Bianchi", "Ferrari", "Esposito", "Romano", "Colombo", "Ricci", "Marino",
    "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano",
)  # fmt: skip

GP_FAMILY_NAMES = ("Moretti", "Barbieri", "Fontana", "Santoro", "Mariani", "Rinaldi")

FACILITY_NAMES = (
    "Pol. Univ. Umberto I — Pronto Soccorso",
    "Sant'Andrea — Pronto Soccorso",
    "Casa della Comunità Prati",
    "Ospedale dei Castelli — Pronto Soccorso",
)


def _slug(given: str, family: str) -> str:
    return f"{given}.{family}".lower().replace(" ", "").replace("'", "")


def build_patients(seed: int) -> list[Patient]:
    """Costruisce i 15 profili. L'ordine e i valori dipendono solo dal seme."""
    rng = random.Random(seed)
    patients: list[Patient] = []

    # I quattro profili "hero" sono fissati: la demo deve poterli richiamare a colpo sicuro.
    # Il resto è generato, ma sempre nello stesso modo a parità di seme.
    plan: list[dict[str, object]] = [
        {"hero": "A", "intent": "minor_wound_care", "gap": "none", "age": 34, "gender": "M"},
        {"hero": "B", "intent": "musculoskeletal_minor", "gap": "gp", "age": 47, "gender": "F"},
        {"hero": "C", "intent": "pediatric_non_urgent", "gap": "none", "age": 9, "gender": "M"},
        # HERO D: nessuna struttura del dataset documenta il prelievo campioni.
        {"hero": "D", "intent": "specimen_collection", "gap": "none", "age": 58, "gender": "F"},
        {"hero": None, "intent": "prescription_renewal", "gap": "contact", "age": 71, "gender": "M"},
        {"hero": None, "intent": "vaccination", "gap": "none", "age": 28, "gender": "F"},
        {"hero": None, "intent": "specialist_referral", "gap": "none", "age": 52, "gender": "M"},
        {"hero": None, "intent": "chronic_followup", "gap": "none", "age": 66, "gender": "F"},
        {"hero": None, "intent": "medication_advice", "gap": "none", "age": 39, "gender": "F"},
        # Caso semplice: nessuna esenzione, nessuna patologia cronica.
        {"hero": None, "intent": "minor_wound_care", "gap": "simple", "age": 23, "gender": "M"},
        {"hero": None, "intent": "musculoskeletal_minor", "gap": "none", "age": 44, "gender": "M"},
        {"hero": None, "intent": "pediatric_non_urgent", "gap": "none", "age": 6, "gender": "F"},
        {"hero": None, "intent": "medication_advice", "gap": "gp", "age": 81, "gender": "F"},
        {"hero": None, "intent": "vaccination", "gap": "contact", "age": 35, "gender": "M"},
        {"hero": None, "intent": "chronic_followup", "gap": "none", "age": 59, "gender": "M"},
    ]

    used_codes: set[str] = set()

    for index, spec in enumerate(plan, start=1):
        gender = str(spec["gender"])
        age = int(spec["age"])
        gap = str(spec["gap"])
        intent = str(spec["intent"])

        pool = GIVEN_NAMES_M if gender == "M" else GIVEN_NAMES_F
        given = pool[(index - 1) % len(pool)]
        family = FAMILY_NAMES[(index - 1) % len(FAMILY_NAMES)]

        # Data di nascita stabile: si parte dall'età voluta e si sposta di qualche giorno.
        birth = date(TODAY.year - age, 1, 1) + timedelta(days=rng.randrange(0, 364))
        place, county, cadastral = BIRTHPLACES[(index - 1) % len(BIRTHPLACES)]

        fiscal = encode(family, given, birth, gender, cadastral)
        # Due profili con stesse iniziali e stessa data collidono: si sposta la nascita.
        while fiscal in used_codes:
            birth += timedelta(days=1)
            fiscal = encode(family, given, birth, gender, cadastral)
        used_codes.add(fiscal)

        is_minor = (TODAY - birth).days < 18 * 365.25

        # `None` è un dato realmente assente, non una stringa vuota: l'interfaccia
        # deve poter distinguere "non disponibile" da "vuoto".
        email: str | None = f"{_slug(given, family)}@example.test"
        phone: str | None = f"+39 333 {1000000 + index:07d}"
        gp: Gp | None = Gp(
            given_name=GIVEN_NAMES_F[index % len(GIVEN_NAMES_F)],
            family_name=GP_FAMILY_NAMES[index % len(GP_FAMILY_NAMES)],
            phone=f"+39 06 {5000000 + index * 37:07d}",
        )
        contact: Contact | None = Contact(
            given_name=GIVEN_NAMES_M[(index + 3) % len(GIVEN_NAMES_M)],
            family_name=family,
            relationship="familiare",
            phone=f"+39 340 {2000000 + index:07d}",
        )

        if gap == "gp":
            gp = None
        elif gap == "contact":
            contact = None
            email = None

        guardian: Guardian | None = None
        if is_minor:
            guardian = Guardian(
                given_name=GIVEN_NAMES_F[(index + 1) % len(GIVEN_NAMES_F)],
                family_name=family,
                relationship="genitore",
                phone=f"+39 349 {3000000 + index:07d}",
            )
            # Un minorenne non ha un proprio recapito: si passa da chi ne ha la tutela.
            email = None
            phone = None

        exemptions: list[Exemption] = []
        chronic: list[str] = []
        if gap != "simple" and not is_minor and rng.random() < 0.6:
            code, description = EXEMPTIONS[index % len(EXEMPTIONS)]
            exemptions.append(Exemption(code=code, description=description))
            chronic.append(CHRONIC_CONDITIONS[index % len(CHRONIC_CONDITIONS)])

        episodes: list[Episode] = []
        for step in range(rng.randrange(0, 3)):
            # Sempre nel passato e sempre dopo la nascita: un episodio futuro sarebbe
            # un errore che i test devono poter cogliere.
            days_ago = rng.randrange(20, 900) + step * 40
            when = TODAY - timedelta(days=days_ago)
            if when <= birth:
                continue
            episodes.append(
                Episode(
                    episode_date=when.isoformat(),
                    facility=FACILITY_NAMES[(index + step) % len(FACILITY_NAMES)],
                    reason=CARE_INTENTS[(index + step) % len(CARE_INTENTS)],
                    outcome=EPISODE_OUTCOMES[(index + step) % len(EPISODE_OUTCOMES)],
                )
            )

        patients.append(
            Patient(
                profile_id=f"SYN-{index:03d}",
                username=_slug(given, family),
                spid_code=f"TESTSP{index:05d}",
                fiscal_code=fiscal,
                given_name=given,
                family_name=family,
                birth_date=birth.isoformat(),
                birth_place=place,
                birth_county=county,
                gender=gender,
                email=email,
                mobile_phone=phone,
                is_minor=is_minor,
                demo_care_intent=intent,
                hero=spec["hero"] if isinstance(spec["hero"], str) else None,
                guardian=guardian,
                gp=gp,
                emergency_contact=contact,
                exemptions=exemptions,
                chronic_conditions=chronic,
                recent_episodes=episodes,
            )
        )

    return patients


def _cell(value: object) -> str:
    """Nei CSV il dato assente resta vuoto; il JSON conserva `null`."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([_cell(cell) for cell in row])


def write_outputs(patients: list[Patient]) -> dict[str, int]:
    write_csv(
        OUT / "profiles.mock.csv",
        [
            "profile_id", "username", "spid_code", "fiscal_code", "given_name", "family_name",
            "birth_date", "birth_place", "birth_county", "gender", "email", "mobile_phone",
            "is_minor", "guardian_given_name", "guardian_family_name", "guardian_relationship",
            "guardian_phone", "gp_given_name", "gp_family_name", "gp_phone",
            "contact_given_name", "contact_family_name", "contact_relationship", "contact_phone",
            "demo_care_intent", "hero", "synthetic",
        ],  # fmt: skip
        [
            [
                p.profile_id, p.username, p.spid_code, p.fiscal_code, p.given_name, p.family_name,
                p.birth_date, p.birth_place, p.birth_county, p.gender, p.email, p.mobile_phone,
                p.is_minor,
                p.guardian.given_name if p.guardian else None,
                p.guardian.family_name if p.guardian else None,
                p.guardian.relationship if p.guardian else None,
                p.guardian.phone if p.guardian else None,
                p.gp.given_name if p.gp else None,
                p.gp.family_name if p.gp else None,
                p.gp.phone if p.gp else None,
                p.emergency_contact.given_name if p.emergency_contact else None,
                p.emergency_contact.family_name if p.emergency_contact else None,
                p.emergency_contact.relationship if p.emergency_contact else None,
                p.emergency_contact.phone if p.emergency_contact else None,
                p.demo_care_intent, p.hero, p.synthetic,
            ]  # fmt: skip
            for p in patients
        ],
    )

    write_csv(
        OUT / "exemptions.mock.csv",
        ["fiscal_code", "code", "description", "synthetic"],
        [[p.fiscal_code, e.code, e.description, True] for p in patients for e in p.exemptions],
    )

    write_csv(
        OUT / "clinical.mock.csv",
        ["fiscal_code", "condition", "synthetic"],
        [[p.fiscal_code, c, True] for p in patients for c in p.chronic_conditions],
    )

    write_csv(
        OUT / "episodes.mock.csv",
        ["fiscal_code", "episode_date", "facility", "reason", "outcome", "synthetic"],
        [
            [p.fiscal_code, e.episode_date, e.facility, e.reason, e.outcome, True]
            for p in patients
            for e in p.recent_episodes
        ],
    )

    payload = {
        "generator": "gen_synthetic_patients.py",
        "provenance": "SYNTHETIC",
        "synthetic": True,
        "note": (
            "Identità inventate. I codici fiscali sono formalmente validi ma non "
            "appartengono a nessuna persona reale e non vanno usati con servizi esterni."
        ),
        "patients": [asdict(p) for p in patients],
    }
    (OUT / "profiles.mock.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    return {
        "profili": len(patients),
        "esenzioni": sum(len(p.exemptions) for p in patients),
        "patologie": sum(len(p.chronic_conditions) for p in patients),
        "episodi": sum(len(p.recent_episodes) for p in patients),
    }


def check(patients: list[Patient]) -> list[str]:
    """Controlli che devono valere sempre. Ritorna l'elenco dei problemi trovati."""
    problems: list[str] = []

    if len(patients) != 15:
        problems.append(f"attesi 15 profili, trovati {len(patients)}")

    codes = [p.fiscal_code for p in patients]
    if len(set(codes)) != len(codes):
        problems.append("codici fiscali duplicati")
    for p in patients:
        if not is_valid(p.fiscal_code):
            problems.append(f"{p.profile_id}: codice fiscale non valido ({p.fiscal_code})")

    covered = {p.demo_care_intent for p in patients}
    missing = set(CARE_INTENTS) - covered
    if missing:
        problems.append(f"care intent non coperti: {sorted(missing)}")

    if not any(p.gp is None for p in patients):
        problems.append("nessun profilo senza medico curante")
    if not any(p.emergency_contact is None and p.email is None for p in patients):
        problems.append("nessun profilo senza contatti")
    if not any(not p.exemptions and not p.chronic_conditions for p in patients):
        problems.append("nessun profilo semplice (senza esenzioni né patologie)")

    minors = [p for p in patients if p.is_minor]
    if not minors:
        problems.append("nessun minorenne")
    for p in minors:
        if p.guardian is None:
            problems.append(f"{p.profile_id}: minorenne senza tutore")

    for hero in ("A", "B", "C", "D"):
        if not any(p.hero == hero for p in patients):
            problems.append(f"profilo HERO {hero} mancante")

    for p in patients:
        birth = date.fromisoformat(p.birth_date)
        for episode in p.recent_episodes:
            when = date.fromisoformat(episode.episode_date)
            if when > TODAY:
                problems.append(f"{p.profile_id}: episodio nel futuro ({episode.episode_date})")
            if when <= birth:
                problems.append(f"{p.profile_id}: episodio precedente alla nascita")
        if not p.synthetic:
            problems.append(f"{p.profile_id}: synthetic non impostato")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gen_synthetic_patients")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--check", action="store_true", help="Verifica soltanto, non scrive")
    args = parser.parse_args(argv)

    patients = build_patients(args.seed)
    problems = check(patients)

    if problems:
        print("PROBLEMI:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if args.check:
        print(f"Controlli superati su {len(patients)} profili (seme {args.seed}).")
        return 0

    counts = write_outputs(patients)
    print(f"Generati con seme {args.seed}:")
    for label, value in counts.items():
        print(f"  {label}: {value}")
    print(f"  scritti in {OUT.relative_to(ROOT)}/")
    for p in patients:
        if p.hero:
            gaps = []
            if p.gp is None:
                gaps.append("senza medico curante")
            if p.emergency_contact is None:
                gaps.append("senza contatti")
            if p.is_minor:
                gaps.append("minorenne con tutore")
            suffix = f" ({', '.join(gaps)})" if gaps else ""
            print(f"  HERO {p.hero}: {p.username} — {p.demo_care_intent}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
