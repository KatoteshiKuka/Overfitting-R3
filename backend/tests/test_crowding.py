"""Verifica che il sistema non mandi tutti nello stesso posto.

È il comportamento più importante da dimostrare: se una struttura è la migliore per una
persona lo è per tutte quelle che chiedono nello stesso momento, e consigliarla venti
volte significa creare lì la coda che si voleva evitare.

    cd backend && uv run python -m unittest tests.test_crowding -v
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from app.features.arrivals import crowding, weights
from app.features.arrivals.models import ArrivalCommitment
from app.features.congestion.waiting import Queue


class TestAffollamentoIndotto(unittest.TestCase):
    def setUp(self) -> None:
        # Pronto soccorso scarico: due persone in coda, otto postazioni che smaltiscono.
        self.queue = Queue(verde=2, in_treatment=8, capacity_hint=15)

    def test_senza_arrivi_nessuna_attesa_aggiuntiva(self) -> None:
        result = crowding.crowding_for(1, 0.0, self.queue, "verde")
        self.assertEqual(result.added_minutes, 0)
        self.assertFalse(result.is_significant)

    def test_attesa_cresce_con_gli_arrivi_gia_indirizzati(self) -> None:
        few = crowding.crowding_for(1, 3 * 0.75, self.queue, "verde")
        many = crowding.crowding_for(1, 20 * 0.75, self.queue, "verde")

        self.assertGreater(many.added_minutes, few.added_minutes)
        # Venti persone indirizzate devono produrre un'attesa che si nota.
        self.assertTrue(many.is_significant, f"20 arrivi -> solo {many.added_minutes} min")

    def test_venti_persone_spostano_la_scelta(self) -> None:
        """Il caso descritto: struttura vicina ma già satura di nostri invii.

        La più vicina costa 5 minuti di viaggio, l'alternativa 20. Se abbiamo già mandato
        venti persone alla prima, il totale deve ribaltare la classifica.
        """
        nearest_travel, nearest_wait = 5, 4
        other_travel, other_wait = 20, 6

        induced = crowding.crowding_for(1, 20 * 0.75, self.queue, "verde")
        nearest_total = nearest_travel + nearest_wait + induced.added_minutes
        other_total = other_travel + other_wait

        self.assertGreater(
            nearest_total,
            other_total,
            f"la più vicina resta preferita ({nearest_total} vs {other_total} min): "
            "l'affollamento indotto non incide abbastanza",
        )

    def test_la_spiegazione_cita_persone_e_minuti(self) -> None:
        result = crowding.crowding_for(1, 20 * 0.75, self.queue, "verde")
        text = crowding.explain(result, "Ospedale Test")
        self.assertIn("Ospedale Test", text)
        self.assertIn(str(result.inbound_people), text)
        self.assertIn(str(result.added_minutes), text)

    def test_struttura_satura_smaltisce_piu_lentamente(self) -> None:
        """A parità di arrivi, dove ci sono meno postazioni l'attesa cresce di più."""
        busy = Queue(verde=18, giallo=4, in_treatment=3, capacity_hint=15)
        light = crowding.crowding_for(1, 10 * 0.75, self.queue, "verde")
        heavy = crowding.crowding_for(1, 10 * 0.75, busy, "verde")
        self.assertGreater(heavy.added_minutes, light.added_minutes)

    def test_codice_urgente_pesa_di_piu(self) -> None:
        """Gli arrivi di chi è più grave occupano le postazioni più a lungo."""
        low = crowding.crowding_for(1, 10 * 0.75, self.queue, "verde")
        high = crowding.crowding_for(1, 10 * 0.75, self.queue, "arancione")
        self.assertGreater(high.added_minutes, low.added_minutes)


class TestFinestraTemporale(unittest.TestCase):
    """Gli arrivi contano solo finché sono davvero imminenti."""

    def _commitment(self, facility_id: int, minutes_ahead: int, status: str = "CONFIRMED"):
        now = datetime.now(UTC)
        return ArrivalCommitment(
            commitment_id=f"cmt_{facility_id}_{minutes_ahead}",
            fiscal_code="TESTCF00A00A000A",
            facility_id=facility_id,
            status=status,
            care_cluster="minor_trauma",
            eta_minutes=minutes_ahead,
            created_at=now,
            expected_arrival_at=now + timedelta(minutes=minutes_ahead),
            updated_at=now,
            weight=weights.weight_for(status),
        )

    def test_pesi_per_stato(self) -> None:
        self.assertEqual(weights.weight_for("CONFIRMED"), 0.75)
        self.assertEqual(weights.weight_for("EN_ROUTE"), 0.90)
        self.assertEqual(weights.weight_for("ARRIVED"), 1.00)
        # Chi ha annullato non pesa: nessuna traccia, nessuna penalità.
        self.assertEqual(weights.weight_for("CANCELLED"), 0.0)
        self.assertEqual(weights.weight_for("EXPIRED"), 0.0)

    def test_un_impegno_non_vale_un_arrivo_certo(self) -> None:
        self.assertLess(weights.weight_for("CONFIRMED"), 1.0)


class TestStruttureSenzaDatiDiCoda(unittest.TestCase):
    """Farmacie e ambulatori non pubblicano l'affluenza: l'effetto va stimato lo stesso.

    Ignorarlo equivarrebbe a trattarli come se avessero capacità infinita, e il
    correttivo non scatterebbe proprio dove il sistema manda più gente.
    """

    def test_effetto_stimato_anche_senza_coda_nota(self) -> None:
        result = crowding.crowding_for(1, 20 * 0.75, None, "verde")
        self.assertGreater(result.added_minutes, 0)
        self.assertTrue(result.is_significant)

    def test_pochi_arrivi_restano_trascurabili(self) -> None:
        result = crowding.crowding_for(1, 1 * 0.75, None, "verde")
        self.assertFalse(result.is_significant)


if __name__ == "__main__":
    unittest.main()
