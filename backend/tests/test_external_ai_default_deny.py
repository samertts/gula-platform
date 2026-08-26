from __future__ import annotations

import asyncio

import pytest
from app.gateways import google_ai
from app.routes import ai


def test_google_gateway_requires_explicit_external_ai_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(google_ai, "_EXTERNAL_AI_ENABLED", False)
    monkeypatch.setattr(google_ai, "_API_KEY", "synthetic-key")

    assert google_ai.is_configured() is False
    assert google_ai.provider_info()["external_ai_enabled"] is False

    with pytest.raises(RuntimeError, match="external AI is disabled"):
        asyncio.run(google_ai.generate_clinical("synthetic laboratory explanation"))


def test_groq_is_rejected_before_http_when_external_ai_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ai, "_EXTERNAL_AI_ENABLED", False)
    monkeypatch.setattr(ai, "_GROQ_KEY", "synthetic-key")

    with pytest.raises(RuntimeError, match="external AI is disabled"):
        asyncio.run(ai._call_groq_llama("synthetic prompt"))


def test_local_ollama_remains_the_only_provider_when_external_ai_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def local_response(_prompt: str) -> str:
        return "local synthetic response"

    monkeypatch.setattr(ai, "_EXTERNAL_AI_ENABLED", False)
    monkeypatch.setattr(ai, "_OLLAMA_BASE_URL", "http://local-ollama.invalid")
    monkeypatch.setattr(ai, "_GROQ_KEY", "synthetic-key")
    monkeypatch.setattr(ai, "_call_ollama_clinical", local_response)
    monkeypatch.setattr(google_ai, "_EXTERNAL_AI_ENABLED", False)
    monkeypatch.setattr(google_ai, "_API_KEY", "synthetic-key")

    text, provider = asyncio.run(ai._call_ai_with_fallback("synthetic prompt"))

    assert text == "local synthetic response"
    assert provider == "ollama"
