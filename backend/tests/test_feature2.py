"""Test della feature 2, con `unittest` della libreria standard.

`pytest` non è nella baseline dichiarata e non va aggiunto solo per questi test.

    cd backend && uv run python -m unittest discover -s tests -v

Coprono i punti che, se si rompessero, farebbero cadere la demo senza avvisare:
il codice fiscale, il determinismo del generatore, la sessione, il join sull'identità,
il ciclo dell'impegno di arrivo e il closed loop fino alla console.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

# Condivide un DB temporaneo con gli altri moduli della suite nello stesso processo.
os.environ["HEALTHPULSE_DATABASE_URL"] = (
    f"sqlite:///{tempfile.gettempdir()}/healthpulse-tests-{os.getpid()}.db"
)

BACKEND = Path(__file__).resolve().parents[1]
SCRIPTS = BACKEND.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from codice_fiscale import checksum, encode, is_valid  # noqa: E402
from gen_synthetic_patients import DEFAULT_SEED, build_patients, check  # noqa: E402

from app.features.auth import service as auth_service  # noqa: E402
from app.features.auth.providers import MockIdentityProvider  # noqa: E402
from app.features.citizens import records  # noqa: E402
from app.main import app  # noqa: E402


class TestCodiceFiscale(unittest.TestCase):
    def test_valore_noto(self) -> None:
        # Valore canonico dell'algoritmo per questa combinazione.
        self.assertEqual(
            encode("Rossi", "Mario", date(1980, 1, 1), "M", "H501"), "RSSMRA80A01H501U"
        )

    def test_femminile_somma_quaranta_al_giorno(self) -> None:
        code = encode("Bianchi", "Anna", date(1990, 5, 12), "F", "H501")
        self.assertEqual(code[9:11], "52")  # 12 + 40

    def test_checksum_indipendente(self) -> None:
        self.assertEqual(checksum("RSSMRA80A01H501"), "U")

    def test_rifiuta_codice_storpiato(self) -> None:
        self.assertFalse(is_valid("RSSMRA80A01H501Z"))
        self.assertFalse(is_valid("troppo-corto"))

    def test_nome_con_quattro_consonanti(self) -> None:
        # Con quattro o più consonanti si prendono la prima, la terza e la quarta.
        self.assertTrue(
            encode("Rossi", "Francesco", date(1980, 1, 1), "M", "H501").startswith("RSSFNC")
        )


class TestGeneratorePazienti(unittest.TestCase):
    def setUp(self) -> None:
        self.patients = build_patients(DEFAULT_SEED)

    def test_quindici_profili(self) -> None:
        self.assertEqual(len(self.patients), 15)

    def test_controlli_interni_superati(self) -> None:
        self.assertEqual(check(self.patients), [])

    def test_deterministico(self) -> None:
        again = build_patients(DEFAULT_SEED)
        self.assertEqual([p.fiscal_code for p in self.patients], [p.fiscal_code for p in again])

    def test_seme_diverso_cambia_output(self) -> None:
        other = build_patients(999)
        self.assertNotEqual([p.fiscal_code for p in self.patients], [p.fiscal_code for p in other])

    def test_codici_fiscali_validi_e_unici(self) -> None:
        codes = [p.fiscal_code for p in self.patients]
        self.assertEqual(len(set(codes)), 15)
        for code in codes:
            self.assertTrue(is_valid(code), code)

    def test_dati_mancanti_sono_assenti_non_vuoti(self) -> None:
        senza_medico = [p for p in self.patients if p.gp is None]
        self.assertTrue(senza_medico)
        # Deve essere `None`, non una stringa vuota: l'interfaccia mostra UNAVAILABLE.
        self.assertIsNone(senza_medico[0].gp)

    def test_minorenne_ha_tutore(self) -> None:
        minori = [p for p in self.patients if p.is_minor]
        self.assertTrue(minori)
        for p in minori:
            self.assertIsNotNone(p.guardian)

    def test_episodi_nel_passato_e_dopo_la_nascita(self) -> None:
        for p in self.patients:
            birth = date.fromisoformat(p.birth_date)
            for episode in p.recent_episodes:
                when = date.fromisoformat(episode.episode_date)
                self.assertLess(when, date(2026, 9, 11))
                self.assertGreater(when, birth)

    def test_hero_presenti(self) -> None:
        heroes = {p.hero for p in self.patients if p.hero}
        self.assertEqual(heroes, {"A", "B", "C", "D"})


class TestIdentitaEProfiloCombaciano(unittest.TestCase):
    """Il vincolo su cui si regge l'intera catena: SPID e profilo condividono il CF."""

    def test_join_su_codice_fiscale(self) -> None:
        provider = MockIdentityProvider()
        for username in provider.list_usernames():
            spid = provider.authenticate(username)
            assert spid is not None
            profile = records.profile_for(spid.fiscal_number)
            self.assertIsNotNone(profile, f"nessun profilo per {username}")
            assert profile is not None
            self.assertEqual(profile["fiscal_code"], spid.fiscal_number)


class TestApi(unittest.TestCase):
    """Percorso completo sull'applicazione vera, dal login alla console."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def setUp(self) -> None:
        self.client.cookies.clear()

    # --- autenticazione ---

    def test_login_sconosciuto(self) -> None:
        response = self.client.post("/api/v1/auth/test-spid/login", json={"username": "nessuno"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "unknown_identity")

    def test_directory_demo_espone_solo_profili_sintetici(self) -> None:
        response = self.client.get("/api/v1/auth/demo-identities")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["synthetic"])
        self.assertEqual(len(body["citizens"]), 15)
        self.assertIn("mario.rossi", {item["username"] for item in body["citizens"]})
        self.assertIn("ps.coordinator", body["operators"])
        self.assertNotIn("password", response.text.lower())

    def test_sessione_assente(self) -> None:
        response = self.client.get("/api/v1/auth/session")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "no_session")

    def test_login_sessione_e_logout(self) -> None:
        login = self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        self.assertEqual(login.status_code, 200)
        body = login.json()
        self.assertTrue(body["authenticated"])
        self.assertTrue(body["synthetic"])
        self.assertNotIn("password", login.text.lower())

        # La sessione sopravvive a una nuova richiesta: è il test di persistenza.
        session = self.client.get("/api/v1/auth/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["profile"]["fiscalNumber"], body["profile"]["fiscalNumber"])

        self.assertEqual(self.client.post("/api/v1/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 401)

    def test_sessione_scaduta_non_vale(self) -> None:
        from app.core.database import SessionLocal
        from app.features.auth.models import AuthSession

        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        session_id = self.client.cookies.get(auth_service.CITIZEN_COOKIE)
        assert session_id is not None

        with SessionLocal() as db:
            row = db.get(AuthSession, session_id)
            assert row is not None
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            db.commit()

        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 401)

    def test_profilo_dalla_sessione_non_dal_client(self) -> None:
        self.client.post("/api/v1/auth/test-spid/login", json={"username": "giulia.bianchi"})
        profile = self.client.get("/api/v1/citizens/me/profile")
        self.assertEqual(profile.status_code, 200)
        body = profile.json()
        self.assertEqual(body["hero"], "B")
        # HERO B non ha il medico curante: deve essere null, non stringa vuota.
        self.assertIsNone(body["gp"])
        self.assertTrue(body["synthetic"])

    def test_operatore_non_e_cittadino(self) -> None:
        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        # Con la sola sessione cittadino la console deve restare chiusa.
        self.assertEqual(self.client.get("/api/v1/hospital/console/overview").status_code, 401)

    def test_cambio_profilo_mantiene_un_solo_dominio_attivo(self) -> None:
        facility_id = self._facility_id()

        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        operator_login = self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": facility_id},
        )
        self.assertEqual(operator_login.status_code, 200)
        self.assertEqual(operator_login.json()["operator"]["display_name"], "Dott.ssa Elisa Conti")
        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/auth/hospital/session").status_code, 200)

        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        self.assertEqual(self.client.get("/api/v1/auth/hospital/session").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/auth/session").status_code, 200)

    # --- impegni di arrivo ---

    def _facility_id(self) -> int:
        response = self.client.get(
            "/api/v1/facilities", params={"type": "pronto-soccorso", "limit": 1}
        )
        items = response.json()["items"]
        if not items:
            self.skipTest("nessun pronto soccorso nei dati caricati")
        return int(items[0]["id"])

    def test_commitment_richiede_autenticazione(self) -> None:
        response = self.client.post(
            "/api/v1/arrivals/commitments", json={"facility_id": 1, "eta_minutes": 10}
        )
        self.assertEqual(response.status_code, 401)

    def test_ciclo_commitment_e_revoca(self) -> None:
        facility_id = self._facility_id()
        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})

        created = self.client.post(
            "/api/v1/arrivals/commitments",
            json={
                "facility_id": facility_id,
                "eta_minutes": 18,
                "care_intent": "minor_wound_care",
            },
        )
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertEqual(body["status"], "CONFIRMED")
        self.assertEqual(body["care_cluster"], "minor_trauma")
        self.assertEqual(body["weight"], 0.75)
        self.assertEqual(body["provenance"], "DERIVED")

        mine = self.client.get("/api/v1/arrivals/commitments/mine")
        self.assertEqual(mine.status_code, 200)
        mine_by_id = {item["commitment_id"]: item for item in mine.json()["items"]}
        self.assertEqual(mine_by_id[body["commitment_id"]]["facility_id"], facility_id)
        self.assertEqual(mine_by_id[body["commitment_id"]]["status"], "CONFIRMED")

        cancelled = self.client.post(f"/api/v1/arrivals/commitments/{body['commitment_id']}/cancel")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["status"], "CANCELLED")
        self.assertEqual(cancelled.json()["weight"], 0.0)

        # Nessun campo punitivo deve comparire nel modello.
        self.assertNotIn("no_show", cancelled.text)
        self.assertNotIn("penalt", cancelled.text.lower())

    def test_preadmission_token_monouso(self) -> None:
        facility_id = self._facility_id()
        self.client.post("/api/v1/auth/test-spid/login", json={"username": "mario.rossi"})
        commitment = self.client.post(
            "/api/v1/arrivals/commitments",
            json={"facility_id": facility_id, "eta_minutes": 20, "care_intent": "minor_wound_care"},
        ).json()

        pre = self.client.post(
            "/api/v1/navigation/preadmission",
            json={"commitment_id": commitment["commitment_id"], "contact_phone": "+39 333 1112223"},
        )
        self.assertEqual(pre.status_code, 201)
        payload = pre.json()
        code = payload["code"]
        # HealthPulse non pre-assegna il triage ospedaliero.
        self.assertIsNone(payload["triage_hint"])

        # Serve una sessione operatore per leggere e accettare.
        self.client.cookies.clear()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": facility_id},
        )
        self.assertEqual(self.client.get(f"/api/v1/admission/resolve/{code}").status_code, 200)

        first = self.client.post(f"/api/v1/admission/{code}/accept")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["status"], "accepted")

        second = self.client.post(f"/api/v1/admission/{code}/accept")
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["code"], "token_already_used")

    # --- closed loop ---

    def test_closed_loop_commitment_arriva_in_console(self) -> None:
        facility_id = self._facility_id()

        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": facility_id},
        )
        before = self.client.get("/api/v1/hospital/console/overview")
        self.assertEqual(before.status_code, 200)
        inbound_before = before.json()["inbound"]["next_60_min"]["commitments"]

        # Il cittadino conferma di dirigersi lì.
        self.client.cookies.clear()
        self.client.post("/api/v1/auth/test-spid/login", json={"username": "giuseppe.gallo"})
        created = self.client.post(
            "/api/v1/arrivals/commitments",
            json={
                "facility_id": facility_id,
                "eta_minutes": 15,
                "care_intent": "musculoskeletal_minor",
            },
        )
        self.assertEqual(created.status_code, 201)

        self.client.cookies.clear()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": facility_id},
        )
        after = self.client.get("/api/v1/hospital/console/overview").json()

        self.assertEqual(after["inbound"]["next_60_min"]["commitments"], inbound_before + 1)
        clusters = {row["cluster"] for row in after["care_mix"]}
        self.assertIn("minor_trauma", clusters)
        self.assertIn(after["expected_pressure_level"], ("LOW", "MODERATE", "HIGH", "VERY_HIGH"))
        # La console aggregata non include ancora i resoconti nominativi.
        self.assertNotIn("fiscal_code", after)

    def test_resoconto_visibile_prima_del_check_in_solo_alla_struttura_scelta(self) -> None:
        facilities = self.client.get(
            "/api/v1/facilities", params={"type": "pronto-soccorso", "limit": 2}
        ).json()["items"]
        if len(facilities) < 2:
            self.skipTest("servono due pronto soccorso per verificare l'isolamento")
        selected_id = int(facilities[0]["id"])
        other_id = int(facilities[1]["id"])

        self.client.post("/api/v1/auth/test-spid/login", json={"username": "chiara.esposito"})
        commitment = self.client.post(
            "/api/v1/arrivals/commitments",
            json={
                "facility_id": selected_id,
                "eta_minutes": 12,
                "care_intent": "pronto soccorso",
                "consents": {
                    "share_arrival": True,
                    "share_preadmission": True,
                    "share_reason": True,
                },
            },
        ).json()
        preadmission = self.client.post(
            "/api/v1/navigation/preadmission",
            json={
                "commitment_id": commitment["commitment_id"],
                "triage_summary": {
                    "priority_code": "arancione",
                    "reason": "Ferita con osso esposto, rischio di infezione",
                    "advice": "Non muovere la gamba.",
                    "provider": "groq",
                    "provisional": True,
                },
                "consents": {
                    "share_arrival": True,
                    "share_preadmission": True,
                    "share_reason": True,
                },
            },
        )
        self.assertEqual(preadmission.status_code, 201)

        self.client.cookies.clear()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": selected_id},
        )
        incoming = self.client.get("/api/v1/hospital/incoming-patients")
        self.assertEqual(incoming.status_code, 200)
        by_id = {item["commitment_id"]: item for item in incoming.json()}
        report = by_id[commitment["commitment_id"]]
        self.assertEqual(report["commitment_status"], "CONFIRMED")
        self.assertEqual(report["identity"]["given_name"], "Chiara")
        self.assertEqual(
            report["triage_summary"]["reason"],
            "Ferita con osso esposto, rischio di infezione",
        )

        checked_in = self.client.post(f"/api/v1/admission/{preadmission.json()['code']}/accept")
        self.assertEqual(checked_in.status_code, 200)
        after_check_in = self.client.get("/api/v1/hospital/incoming-patients").json()
        after_by_id = {item["commitment_id"]: item for item in after_check_in}
        self.assertEqual(after_by_id[commitment["commitment_id"]]["commitment_status"], "ARRIVED")
        self.assertNotIn("penalt", str(after_by_id[commitment["commitment_id"]]).lower())

        self.client.cookies.clear()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": other_id},
        )
        other_incoming = self.client.get("/api/v1/hospital/incoming-patients").json()
        other_ids = {item["commitment_id"] for item in other_incoming}
        self.assertNotIn(commitment["commitment_id"], other_ids)

    def test_console_dichiara_carico_e_routing_lo_vede(self) -> None:
        facility_id = self._facility_id()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "ps.coordinator", "facility_id": facility_id},
        )
        updated = self.client.put(
            f"/api/v1/congestion/{facility_id}",
            json={
                "waiting_red": 1,
                "waiting_yellow": 4,
                "waiting_green": 12,
                "waiting_white": 2,
                "in_treatment": 9,
                "in_observation": 3,
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["source"], "dichiarato")
        self.assertEqual(updated.json()["queue"]["totale"], 19)

        # La stessa riga la legge il percorso cittadino: nessuna tabella parallela.
        public = self.client.get(f"/api/v1/congestion/{facility_id}")
        self.assertEqual(public.json()["source"], "dichiarato")

    def test_sola_lettura_non_puo_dichiarare(self) -> None:
        facility_id = self._facility_id()
        self.client.post(
            "/api/v1/auth/hospital/login",
            json={"username": "sola.lettura", "facility_id": facility_id},
        )
        response = self.client.put(
            f"/api/v1/congestion/{facility_id}",
            json={
                "waiting_red": 0,
                "waiting_yellow": 0,
                "waiting_green": 1,
                "waiting_white": 0,
                "in_treatment": 1,
            },
        )
        self.assertEqual(response.status_code, 403)


class TestTriageEsistenteNonRotto(unittest.TestCase):
    """La feature 1 deve continuare a funzionare: le aggiunte sono additive."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)

    def test_endpoint_triage_rispondono(self) -> None:
        self.assertEqual(self.client.get("/api/v1/triage/status").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/facilities/summary").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/system-status").status_code, 200)

    def test_attesa_dipende_dal_codice(self) -> None:
        from app.features.congestion.waiting import Queue, estimate_wait

        queue = Queue(giallo=3, verde=12, in_treatment=8, capacity_hint=15)
        # Chi ha un codice meno grave aspetta almeno quanto chi ne ha uno più grave.
        self.assertGreaterEqual(estimate_wait(queue, "bianco"), estimate_wait(queue, "arancione"))
        self.assertEqual(estimate_wait(queue, "rosso"), 0)


if __name__ == "__main__":
    unittest.main()
