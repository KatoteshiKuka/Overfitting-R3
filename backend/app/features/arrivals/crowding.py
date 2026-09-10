"""Effetto dei consigli di HealthPulse sulle strutture consigliate.

Il problema che questo modulo risolve.

Se una struttura è la più conveniente secondo i criteri — vicina, poco affollata — lo è
**per tutti quelli che chiedono nello stesso momento**. Consigliarla a venti persone
significa creare lì la coda che stavamo cercando di evitare: il sistema produrrebbe
esattamente il male che dice di curare, e la ventesima persona arriverebbe trovando
un'attesa che nessuno le aveva annunciato.

La correzione è semplice e volutamente deterministica: prima di ordinare le opzioni si
guarda quante persone HealthPulse ha **già** indirizzato verso ciascuna struttura e non
sono ancora arrivate, e si somma quell'attesa a quella osservata. Una struttura non viene
mai nascosta: viene solo mostrata con il tempo che avrà davvero quando ci arrivi.

Niente apprendimento e niente pesi opachi: la formula è versionata e ogni numero che
compare in interfaccia si può ricondurre a un conteggio.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.arrivals import weights
from app.features.arrivals.models import ArrivalCommitment
from app.features.congestion.waiting import SERVICE_MINUTES, Queue, throughput

CROWDING_FORMULA = "induced_crowding.v1"

# Finestra entro cui un arrivo già promesso pesa sulla coda che troverai.
# Oltre le due ore l'effetto si è esaurito: chi è arrivato è già stato smaltito.
HORIZON_MINUTES = 120

# Capacità presunta di una struttura di cui non conosciamo la coda.
#
# Solo i pronto soccorso hanno dati di affluenza pubblicati: farmacie, ambulatori e
# ospedali senza pronto soccorso non ne hanno. Trattarli come se avessero capacità
# infinita — che è ciò che accade restituendo zero — significherebbe poterci mandare
# chiunque senza mai segnalare la coda che stiamo creando, e il correttivo non
# scatterebbe proprio dove serve. Meglio una capacità prudente e dichiarata.
ASSUMED_CAPACITY = 18


@dataclass(frozen=True, slots=True)
class Crowding:
    """Pressione che HealthPulse stessa sta generando su una struttura."""

    facility_id: int
    inbound_people: int
    inbound_weighted: float
    added_minutes: int

    @property
    def is_significant(self) -> bool:
        """Sotto i cinque minuti non vale la pena dirlo: sarebbe rumore."""
        return self.added_minutes >= 5


@dataclass(frozen=True, slots=True)
class InboundDemand:
    """Numero reale di conferme e relativo peso previsionale."""

    people: int
    weighted: float


def inbound_by_facility(
    db: Session, horizon_minutes: int = HORIZON_MINUTES
) -> dict[int, InboundDemand]:
    """Arrivi già promessi e non ancora avvenuti, per struttura, pesati per stato."""
    now = datetime.now(UTC)
    limit = now + timedelta(minutes=horizon_minutes)
    stale_limit = now - timedelta(hours=3)

    rows = db.scalars(
        select(ArrivalCommitment).where(
            ArrivalCommitment.status.in_(weights.ACTIVE_STATUSES),
        )
    ).all()

    totals: dict[int, tuple[int, float]] = {}
    for row in rows:
        expected = row.expected_arrival_at
        if expected.tzinfo is None:
            expected = expected.replace(tzinfo=UTC)
        if expected > limit or expected < stale_limit:
            continue
        count, weighted = totals.get(row.facility_id, (0, 0.0))
        totals[row.facility_id] = (count + 1, weighted + row.weight)
    return {
        facility_id: InboundDemand(people=count, weighted=round(weighted, 2))
        for facility_id, (count, weighted) in totals.items()
    }


def crowding_for(
    facility_id: int, inbound: InboundDemand, queue: Queue | None, app_code: str
) -> Crowding:
    """Minuti di attesa aggiuntivi dovuti a chi HealthPulse ha già indirizzato lì.

    Si usa lo stesso modello dell'attesa osservata — lavoro da smaltire diviso postazioni
    che smaltiscono — così i due numeri sono commensurabili invece di essere due stime
    scollegate.
    """
    if inbound.weighted <= 0:
        return Crowding(facility_id, inbound.people, 0.0, 0)

    # Senza dati di coda si assume una capacità prudente invece di ignorare l'effetto.
    queue = queue or Queue(capacity_hint=ASSUMED_CAPACITY)

    # Chi arriva tramite HealthPulse ha in genere un problema a bassa intensità: si usa
    # il tempo di servizio del colore corrispondente, non quello di un'emergenza.
    colour = "verde" if app_code in {"verde", "azzurro", "bianco"} else "giallo"
    added = inbound.weighted * SERVICE_MINUTES[colour] / throughput(queue)

    return Crowding(
        facility_id=facility_id,
        inbound_people=inbound.people,
        inbound_weighted=round(inbound.weighted, 2),
        added_minutes=int(round(added)),
    )


def explain(crowding: Crowding, facility_name: str) -> str:
    """Frase da mostrare a chi si vede consigliare una struttura più lontana."""
    return (
        f"{facility_name} sarebbe più vicina, ma abbiamo già indirizzato lì "
        f"{crowding.inbound_people} persone in arrivo nelle prossime due ore: ci troveresti circa "
        f"{crowding.added_minutes} minuti di attesa in più."
    )
