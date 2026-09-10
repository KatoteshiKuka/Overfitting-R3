"""Client per i modelli linguistici, con catena di fallback.

Si prova nell'ordine: modello locale (LM Studio), Groq, poi niente — a quel punto
il chiamante usa le regole deterministiche di `rules.py`. Entrambi i provider parlano
lo stesso dialetto OpenAI, quindi cambia solo l'URL e la chiave.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LlmReply:
    """Risposta del modello, già ridotta a JSON. `provider` finisce in UI per trasparenza."""

    data: dict[str, Any]
    provider: str


class LlmUnavailableError(RuntimeError):
    """Nessun provider ha risposto: il chiamante deve ricadere sulle regole."""


def extract_json(raw: str) -> dict[str, Any] | None:
    """I modelli piccoli incapsulano il JSON in un blocco markdown o lo circondano di testo."""
    text = raw.strip()
    if not text:
        return None

    if text.startswith("```"):
        # Toglie ```json ... ``` lasciando solo il corpo.
        text = text.split("```")[1] if text.count("```") >= 2 else text.lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Ultimo tentativo: il primo oggetto bilanciato dentro il testo.
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(text[start : index + 1])
                        break
                    except json.JSONDecodeError:
                        return None
        else:
            return None

    return parsed if isinstance(parsed, dict) else None


async def _call_openai_compatible(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
    schema: dict[str, Any],
    api_key: str = "",
    max_tokens: int = 1400,
) -> dict[str, Any] | None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        # I modelli con catena di pensiero consumano molti token prima di rispondere:
        # con un budget stretto `content` torna vuoto.
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "triage", "strict": True, "schema": schema},
        },
    }

    response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    body = response.json()

    choices = body.get("choices") or []
    if not choices:
        return None
    content = (choices[0].get("message") or {}).get("content") or ""
    return extract_json(content)


async def complete_json(messages: list[dict[str, Any]], schema: dict[str, Any]) -> LlmReply:
    """Interroga i provider in ordine e restituisce il primo JSON valido."""
    settings = get_settings()

    providers: list[tuple[str, str, str, str]] = [
        ("locale", settings.llm_base_url, settings.llm_model, ""),
    ]
    if settings.groq_api_key:
        providers.append(
            ("groq", settings.groq_base_url, settings.groq_model, settings.groq_api_key)
        )

    errors: list[str] = []

    for name, base_url, model, api_key in providers:
        timeout = settings.llm_timeout_seconds
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                data = await _call_openai_compatible(
                    client, base_url, model, messages, schema, api_key
                )
            if data is not None:
                return LlmReply(data=data, provider=name)
            errors.append(f"{name}: risposta senza JSON utilizzabile")
        except (httpx.HTTPError, ValueError) as exc:
            errors.append(f"{name}: {type(exc).__name__}")
            logger.warning("Provider LLM '%s' non disponibile: %s", name, exc)

    raise LlmUnavailableError("; ".join(errors) or "nessun provider configurato")


async def provider_health() -> list[dict[str, Any]]:
    """Stato dei provider, mostrato in UI perché si capisca chi ha risposto."""
    settings = get_settings()
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            response = await client.get(f"{settings.llm_base_url}/models")
            ok = response.status_code == 200
        except httpx.HTTPError:
            ok = False
        results.append({"name": "locale", "model": settings.llm_model, "available": ok})

    results.append(
        {
            "name": "groq",
            "model": settings.groq_model,
            "available": bool(settings.groq_api_key),
        }
    )
    return results
