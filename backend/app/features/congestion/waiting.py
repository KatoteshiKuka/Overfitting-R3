"""Stima dell'attesa in pronto soccorso a partire dalle code reali.

Il modello è volutamente semplice e leggibile: quante persone hai davanti, diviso per
quante ne stanno smaltendo, per il tempo medio di una presa in carico. Nessun numero
inventato e nessuna stima affidata a un modello linguistico — tutto deriva dai conteggi
pubblicati dalla Regione.

La differenza che conta: in pronto soccorso **non si aspetta in ordine di arrivo**.
Chi arriva con un codice bianco ha davanti tutti i rossi, i gialli e i verdi presenti,
mentre un rosso passa subito. Per questo l'attesa si calcola sempre rispetto al codice
della persona, e non è un numero unico per struttura.
"""

from __future__ import annotations

from dataclasses import dataclass

# Priorità decrescente: i codici del dataset regionale (che usa il modello a 4 colori)
# mappati sulla scala a 5 codici usata dall'app.
APP_CODE_TO_QUEUE: dict[str, str] = {
    "rosso": "rosso",
    "arancione": "giallo",
    "azzurro": "verde",
    "verde": "verde",
    "bianco": "bianco",
}

QUEUE_ORDER: tuple[str, ...] = ("rosso", "giallo", "verde", "bianco")

# Minuti medi di occupazione di una postazione per colore: più è grave, più tempo serve.
SERVICE_MINUTES: dict[str, int] = {
    "rosso": 45,
    "giallo": 35,
    "verde": 20,
    "bianco": 12,
}


@dataclass(frozen=True, slots=True)
class Queue:
    """Code presenti in una struttura, per colore."""

    rosso: int = 0
    giallo: int = 0
    verde: int = 0
    bianco: int = 0
    non_assegnato: int = 0
    in_treatment: int = 0
    capacity_hint: int = 20

    @property
    def total(self) -> int:
        return self.rosso + self.giallo + self.verde + self.bianco + self.non_assegnato

    def count(self, colour: str) -> int:
        return int(getattr(self, colour, 0))


def throughput(queue: Queue) -> int:
    """Postazioni che stanno effettivamente smaltendo.

    Si usa il numero di persone in trattamento, che è il dato osservato; se è zero
    (struttura scarica) si ricade sulla capacità tipica della tipologia, altrimenti
    l'attesa risulterebbe infinita proprio quando il pronto soccorso è vuoto.
    """
    return max(1, queue.in_treatment or max(1, queue.capacity_hint // 3))


def people_ahead(queue: Queue, app_code: str) -> int:
    """Quante persone verrebbero chiamate prima di chi arriva con questo codice.

    A parità di colore si assume di mettersi in fondo alla coda, quindi i pari grado
    contano: è l'ipotesi prudente.
    """
    target = APP_CODE_TO_QUEUE.get(app_code, "verde")
    ahead = queue.non_assegnato  # i non ancora valutati vengono comunque visti prima
    for colour in QUEUE_ORDER:
        ahead += queue.count(colour)
        if colour == target:
            break
    return ahead


def work_ahead_minutes(queue: Queue, app_code: str) -> int:
    """Minuti-postazione necessari a smaltire chi ti precede.

    Ogni persona in coda occupa una postazione per un tempo che dipende **dal suo**
    colore, non dal tuo: un giallo davanti costa 35 minuti anche a chi arriva bianco.
    """
    target = APP_CODE_TO_QUEUE.get(app_code, "verde")
    # I non ancora valutati si trattano come verdi: è il caso più frequente.
    total = queue.non_assegnato * SERVICE_MINUTES["verde"]
    for colour in QUEUE_ORDER:
        total += queue.count(colour) * SERVICE_MINUTES[colour]
        if colour == target:
            break
    return total


def estimate_wait(queue: Queue, app_code: str) -> int:
    """Minuti di attesa stimati per chi arriva adesso con quel codice."""
    if app_code == "rosso":
        # Un'emergenza entra subito: l'attesa non è la variabile rilevante.
        return 0

    work = work_ahead_minutes(queue, app_code)
    if work == 0:
        return 0

    return int(round(work / throughput(queue)))


def load_ratio(queue: Queue) -> float:
    """Quanto è carica la struttura: coda rapportata alla capacità di smaltimento."""
    if queue.capacity_hint <= 0:
        return 0.0
    return round(min(1.0, queue.total / queue.capacity_hint), 3)


def level_for(ratio: float) -> str:
    if ratio < 0.4:
        return "basso"
    if ratio < 0.75:
        return "medio"
    return "alto"
