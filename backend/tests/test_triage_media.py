from __future__ import annotations

import base64
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

os.environ.setdefault(
    "HEALTHPULSE_DATABASE_URL",
    f"sqlite:///{tempfile.gettempdir()}/healthpulse-tests-{os.getpid()}.db",
)

from app.features.triage import llm, service  # noqa: E402
from app.features.triage.schemas import ChatImage, ChatMessage  # noqa: E402


def sample_image() -> ChatImage:
    encoded = base64.b64encode(b"temporary-image-bytes").decode("ascii")
    return ChatImage(name="ferita.jpg", data_url=f"data:image/jpeg;base64,{encoded}")


class TestFotoTemporanea(unittest.IsolatedAsyncioTestCase):
    def test_accetta_solo_formati_immagine_previsti(self) -> None:
        image = sample_image()
        self.assertTrue(image.data_url.startswith("data:image/jpeg;base64,"))

        with self.assertRaises(ValidationError):
            ChatImage(name="allegato.svg", data_url="data:image/svg+xml;base64,PHN2Zz4=")

    def test_foto_ammessa_solo_per_utente(self) -> None:
        with self.assertRaises(ValidationError):
            ChatMessage(role="assistant", content="Risposta", image=sample_image())

    async def test_foto_inoltrata_al_modello_senza_cambiare_la_risposta(self) -> None:
        reply = llm.LlmReply(
            data={"reply": "Da quanto tempo sanguina?", "done": False}, provider="locale"
        )
        mocked = AsyncMock(return_value=reply)
        message = ChatMessage(
            role="user",
            content="Mi sono tagliato la mano da dieci minuti.",
            image=sample_image(),
        )

        with patch.object(llm, "complete_json", mocked):
            response = await service.chat([message])

        self.assertFalse(response.done)
        payload = mocked.await_args.args[0]
        user_content = payload[1]["content"]
        self.assertIsInstance(user_content, list)
        self.assertEqual(user_content[0]["type"], "text")
        self.assertEqual(user_content[1]["type"], "image_url")
        self.assertEqual(user_content[1]["image_url"]["url"], message.image.data_url)


if __name__ == "__main__":
    unittest.main()
