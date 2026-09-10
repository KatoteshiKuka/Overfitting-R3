"""Classificazione deterministica dei sintomi.

Serve a due cose distinte:

1. **Rete di sicurezza sull'LLM.** Un modello che classifica "bianco" un dolore toracico
   è pericoloso, quindi le bandiere rosse trovate qui possono solo *alzare* la gravità
   decisa dal modello, mai abbassarla.
2. **Fallback.** Se né il modello locale né Groq rispondono, l'app continua a funzionare.

Funzioni pure: nessuna dipendenza da rete o database.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

# Ordine di gravità crescente: l'indice è il livello.
CODE_ORDER: tuple[str, ...] = ("bianco", "verde", "azzurro", "arancione", "rosso")


@dataclass(frozen=True, slots=True)
class RuleMatch:
    code: str
    reason: str
    matched: tuple[str, ...]
    #: `critico` | `urgente` | `comune` | `ignoto`. Distingue una bandiera rossa da un
    #: banale mal di gola: senza, l'interfaccia finirebbe per chiamare "critico" un
    #: raffreddore, e il messaggio di sicurezza perderebbe ogni valore.
    severity: str = "ignoto"

    @property
    def is_alarming(self) -> bool:
        return self.severity in {"critico", "urgente"}


# Sintomi che impongono il 118 o il pronto soccorso, qualunque cosa dica il modello.
RED_FLAGS: tuple[tuple[str, ...], ...] = (
    ("dolore al petto", "dolore toracico", "dolore al torace", "fitta al petto"),
    ("non respiro", "non riesco a respirare", "fiato corto grave", "soffoco", "manca il fiato"),
    ("perdita di coscienza", "svenuto", "svenimento", "non si sveglia", "incosciente"),
    ("ictus", "paralisi", "non muovo il braccio", "bocca storta", "non parlo bene"),
    ("emorragia", "sangue che non si ferma", "perdo molto sangue", "vomito sangue"),
    ("convulsioni", "crisi epilettica", "convulsione"),
    ("trauma cranico", "botta in testa forte", "caduta dall alto"),
    ("labbra blu", "cianosi", "confusione improvvisa"),
    ("pensieri suicidi", "voglio farmi del male", "farla finita"),
)

# Sintomi urgenti ma non immediatamente vitali.
ORANGE_FLAGS: tuple[tuple[str, ...], ...] = (
    ("febbre alta", "febbre a 40", "febbre 39", "febbre molto alta"),
    ("dolore forte", "dolore insopportabile", "dolore acuto", "dolore fortissimo"),
    ("frattura", "osso rotto", "non riesco a camminare", "gamba rotta", "braccio rotto"),
    ("disidratazione", "vomito da giorni", "non trattengo liquidi"),
    ("ferita profonda", "taglio profondo", "servono punti"),
    ("difficolta a respirare", "respiro affannoso", "asma"),
)

# Disturbi comuni, gestibili sul territorio.
LOW_FLAGS: tuple[tuple[str, ...], ...] = (
    ("mal di gola", "raffreddore", "tosse", "naso chiuso", "influenza"),
    ("mal di testa", "cefalea", "emicrania"),
    ("mal di pancia", "mal di stomaco", "nausea", "diarrea"),
    ("graffio", "escoriazione", "piccolo taglio", "livido"),
    ("ricetta", "certificato", "prescrizione", "medicine finite"),
    ("mal di schiena", "dolore lieve", "contrattura"),
    ("congiuntivite", "orzaiolo", "sfogo cutaneo", "puntura di insetto"),
)


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize(text: str) -> str:
    """Minuscolo, senza accenti, punteggiatura ridotta a spazi: il matching diventa stabile."""
    cleaned = strip_accents(text).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in cleaned).split())


def _find(text: str, groups: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    return tuple(phrase for group in groups for phrase in group if phrase in text)


def classify(text: str) -> RuleMatch:
    """Assegna un codice a partire dalle parole chiave. Prudente per costruzione."""
    normalized = normalize(text)

    red = _find(normalized, RED_FLAGS)
    if red:
        return RuleMatch(
            code="rosso",
            reason="Sono presenti sintomi che richiedono soccorso immediato.",
            matched=red,
            severity="critico",
        )

    orange = _find(normalized, ORANGE_FLAGS)
    if orange:
        return RuleMatch(
            code="arancione",
            reason="I sintomi descritti vanno valutati senza rinviare.",
            matched=orange,
            severity="urgente",
        )

    low = _find(normalized, LOW_FLAGS)
    if low:
        return RuleMatch(
            code="verde",
            reason="Disturbo comune, gestibile dalle strutture del territorio.",
            matched=low,
            severity="comune",
        )

    # Nessuna corrispondenza: non si può escludere nulla, quindi si resta nel mezzo.
    return RuleMatch(
        code="azzurro",
        reason="Servono più elementi per valutare: meglio un controllo medico.",
        matched=(),
        severity="ignoto",
    )


def max_code(first: str, second: str) -> str:
    """Il più grave dei due. È così che le regole correggono l'LLM verso l'alto."""
    try:
        return first if CODE_ORDER.index(first) >= CODE_ORDER.index(second) else second
    except ValueError:
        return second if second in CODE_ORDER else "azzurro"


def is_valid_code(code: str) -> bool:
    return code in CODE_ORDER
