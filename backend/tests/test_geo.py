import os
import unittest

os.environ.setdefault(
    "HEALTHPULSE_DATABASE_URL", f"sqlite:////private/tmp/healthpulse-tests-{os.getpid()}.db"
)

from app.features.triage.geo import _device_position  # noqa: E402


class TestPosizioneDispositivo(unittest.TestCase):
    def test_accetta_coordinate_nel_lazio(self) -> None:
        point = _device_position("geo:41.9028,12.4964")

        self.assertIsNotNone(point)
        assert point is not None
        self.assertEqual(point.label, "Posizione attuale")
        self.assertEqual(point.latitude, 41.9028)
        self.assertEqual(point.longitude, 12.4964)

    def test_rifiuta_coordinate_fuori_dal_lazio(self) -> None:
        self.assertIsNone(_device_position("geo:45.4642,9.1900"))

    def test_rifiuta_formato_non_valido(self) -> None:
        self.assertIsNone(_device_position("geo:coordinate-mancanti"))
        self.assertIsNone(_device_position("Via Nazionale 100, Roma"))


if __name__ == "__main__":
    unittest.main()
