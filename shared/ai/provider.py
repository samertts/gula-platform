"""The AI inference provider.

IA-074. This module was hardwired to one hosted vendor and reported success
when it had none:

    self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    ...
    def _init_client(self):
        if not self._api_key:
            logger.warning("No AI API key configured — using stub mode")
            return          # self._client stays None
    def generate(self, prompt, temperature=0.3) -> str:
        if self._client:
            ...
        return ""           # <- unconfigured AND failed both land here

Two consequences.

**Ollama could not be used at all.** PROGRAM-CONSTITUTION-001 mandates Local AI
First, Self-Hosted First and Zero Paid Dependency, and
``app/ai_fabric/gateway.py`` already registers an OLLAMA provider with
``api_key_env=""``. But every actual call went through this class, which knew
only ``GEMINI_API_KEY`` and ``google.generativeai``. The constitutional first
choice was unreachable in practice.

**An unconfigured provider was indistinguishable from an empty answer.**
``generate()`` returned ``""`` both when no backend existed and when a real
request failed, and ``generate_structured()`` turned that into ``None``. Every
caller then had to guess. Downstream they guessed wrong, in ways recorded in
IA-074: fabricated embedding vectors, and a reranker that scored every document
0.5.

So: Ollama is supported and preferred, and an unconfigured provider now raises
``AIProviderUnavailable`` instead of answering. ``available`` lets a caller ask
before committing to a path, which is what the honest fallbacks need.

Backend order, and why. Ollama is tried first because it is self-hosted and
free, per the Constitution. Gemini is used when Ollama is absent and a key is
set. No other vendor is added here: ``gateway.py`` already enumerates seven
hosted providers, and giving this class its own competing list would be a
second source of truth.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("gula.ai.provider")

#: Where a self-hosted Ollama is expected. Matches gateway.py's default so the
#: two cannot drift.
DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"

#: Ollama's default chat and embedding models. Small, CPU-runnable, free.
DEFAULT_OLLAMA_MODEL = "llama3.2:1b"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"

#: The second free, self-hosted option. vLLM, llama.cpp's server, LocalAI and
#: text-generation-webui all expose the SAME OpenAI-compatible protocol
#: (/v1/models, /v1/chat/completions, /v1/embeddings), so one backend covers
#: every one of them. gateway.py already names vLLM's variable, so it is reused
#: rather than invented; LOCAL_AI_BASE_URL is accepted as a clearer alias.
DEFAULT_VLLM_BASE_URL = "http://localhost:8001"


class AIProviderUnavailable(RuntimeError):
    """No inference backend is configured, or the configured one failed.

    Raised instead of returning an empty string, so a caller cannot mistake an
    absent provider for a model that had nothing to say. A caller that has a
    legitimate non-AI path should catch this and say in its own result which
    path it took -- see ``shared/ai/client.py``.
    """


class AIProvider:
    """Text generation and embeddings, over Ollama or Gemini.

    ``available`` is False when neither backend is configured. In that state
    every method raises rather than answering.
    """

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        *,
        ollama_base_url: str | None = None,
    ) -> None:
        self._ollama_base_url = (
            ollama_base_url
            or os.getenv("OLLAMA_BASE_URL")
            or DEFAULT_OLLAMA_BASE_URL
        ).rstrip("/")
        self._ollama_model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self._ollama_embed_model = os.getenv(
            "OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL,
        )
        self._local_openai_base_url = (
            os.getenv("LOCAL_AI_BASE_URL")
            or os.getenv("VLLM_BASE_URL")
            or DEFAULT_VLLM_BASE_URL
        ).rstrip("/")
        # vLLM may be started with --api-key; llama.cpp and LocalAI usually are
        # not. Empty is normal and is not treated as "unconfigured".
        self._local_openai_key = os.getenv("VLLM_API_KEY", "")
        self._local_openai_model = os.getenv("LOCAL_AI_MODEL", "")
        self._local_openai_embed_model = os.getenv("LOCAL_AI_EMBED_MODEL", "")

        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._gemini_model = model or os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")

        self._backend: str | None = None
        self._client: Any = None
        self._select_backend()

    # ── backend selection ───────────────────────────────────────────────────

    def _select_backend(self) -> None:
        if self._ollama_reachable():
            self._backend = "ollama"
            logger.info(
                "AI provider: ollama at %s (model=%s, embed=%s) — self-hosted, no key",
                self._ollama_base_url, self._ollama_model, self._ollama_embed_model,
            )
            return

        discovered = self._local_openai_model_name()
        if discovered is not None:
            self._backend = "openai-compatible"
            self._local_openai_model = self._local_openai_model or discovered
            logger.info(
                "AI provider: OpenAI-compatible local server at %s (model=%s) — "
                "self-hosted, no paid dependency",
                self._local_openai_base_url, self._local_openai_model,
            )
            return

        if self._api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(self._gemini_model)
                self._backend = "gemini"
                logger.info("AI provider: gemini (model=%s)", self._gemini_model)
                return
            except ImportError:
                logger.warning(
                    "GEMINI_API_KEY is set but google.generativeai is not installed",
                )

        self._backend = None
        logger.warning(
            "AI provider: NONE available. Ollama not reachable at %s and no usable "
            "GEMINI_API_KEY. Calls will raise AIProviderUnavailable rather than "
            "returning an empty answer. Per PROGRAM-CONSTITUTION-001 the preferred "
            "fix is a self-hosted Ollama: set OLLAMA_BASE_URL.",
            self._ollama_base_url,
        )

    def _ollama_reachable(self) -> bool:
        try:
            import httpx

            response = httpx.get(f"{self._ollama_base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception as exc:  # network error, DNS, bad URL, httpx absent
            logger.debug("Ollama probe failed at %s: %s", self._ollama_base_url, exc)
            return False

    def _local_openai_model_name(self) -> str | None:
        """Probe /v1/models. Returns a servable model id, or None if absent.

        A server that answers with an empty model list is running but has
        nothing loaded, which is not usable -- so that is None too, rather than
        a backend that would fail on first use.
        """
        try:
            import httpx

            headers = (
                {"Authorization": f"Bearer {self._local_openai_key}"}
                if self._local_openai_key
                else {}
            )
            response = httpx.get(
                f"{self._local_openai_base_url}/v1/models", headers=headers, timeout=2.0,
            )
            if response.status_code != 200:
                return None
            models = response.json().get("data") or []
            if not models:
                logger.debug(
                    "OpenAI-compatible server at %s has no models loaded",
                    self._local_openai_base_url,
                )
                return None
            if self._local_openai_model:
                return self._local_openai_model
            return str(models[0].get("id", "")) or None
        except Exception as exc:
            logger.debug(
                "OpenAI-compatible probe failed at %s: %s",
                self._local_openai_base_url, exc,
            )
            return None

    @property
    def available(self) -> bool:
        """Whether any backend is configured. Ask this before an AI-only path."""
        return self._backend is not None

    @property
    def backend(self) -> str | None:
        """``"ollama"``, ``"gemini"`` or None. Goes in result provenance."""
        return self._backend

    def _local_openai_headers(self) -> dict[str, str]:
        """Bearer only when a key was given. vLLM may require one; llama.cpp does not."""
        if self._local_openai_key:
            return {"Authorization": f"Bearer {self._local_openai_key}"}
        return {}

    def _require_backend(self) -> str:
        if self._backend is None:
            raise AIProviderUnavailable(
                "no AI inference backend is configured: Ollama is not reachable at "
                f"{self._ollama_base_url} and no usable GEMINI_API_KEY is set. "
                "See IA-074.",
            )
        return self._backend

    # ── generation ──────────────────────────────────────────────────────────

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate text. Raises rather than returning "" when unavailable."""
        backend = self._require_backend()

        if backend == "ollama":
            try:
                import httpx

                response = httpx.post(
                    f"{self._ollama_base_url}/api/generate",
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": temperature},
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                return str(response.json().get("response", ""))
            except Exception as exc:
                raise AIProviderUnavailable(f"ollama generation failed: {exc}") from exc

        if backend == "openai-compatible":
            try:
                import httpx

                response = httpx.post(
                    f"{self._local_openai_base_url}/v1/chat/completions",
                    headers=self._local_openai_headers(),
                    json={
                        "model": self._local_openai_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                    },
                    timeout=120.0,
                )
                response.raise_for_status()
                choices = response.json().get("choices") or []
                if not choices:
                    raise AIProviderUnavailable(
                        "OpenAI-compatible server returned no choices",
                    )
                return str(choices[0]["message"]["content"])
            except AIProviderUnavailable:
                raise
            except Exception as exc:
                raise AIProviderUnavailable(
                    f"OpenAI-compatible generation failed: {exc}",
                ) from exc

        try:
            result = self._client.generate_content(
                prompt, generation_config={"temperature": temperature},
            )
            return str(result.text)
        except Exception as exc:
            raise AIProviderUnavailable(f"gemini generation failed: {exc}") from exc

    def generate_structured(self, prompt: str, schema: type | None = None) -> Any:
        """Parse the model's reply as JSON.

        Returns None only for genuinely unparseable model output -- which is a
        real answer about the model, not a stand-in for "no provider". An
        unavailable provider raises from ``generate``.
        """
        raw = self.generate(prompt, temperature=0.2)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(
                "%s returned output that is not JSON (%d chars)", self._backend, len(raw),
            )
            return None

    # ── embeddings ──────────────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        """A real embedding vector.

        IA-074: callers used to fake this by prompting a chat model to
        "Generate embedding for: ..." and then returning a constant vector --
        ``[0.5] * 384`` in local_ai.py, ``[hash(raw) % 1000 / 1000.0] * 384``
        in gateway.py. Constant vectors make every pair of texts maximally
        similar, so any similarity search over them is meaningless while
        reporting success. The second was worse: Python salts ``str`` hashes per
        process, so the same text embedded differently after every restart.

        Embeddings need an embedding endpoint, not a chat completion. Ollama
        has one. Gemini's is a different API that this class does not speak, so
        with a Gemini backend this raises rather than inventing a vector.
        """
        backend = self._require_backend()

        if backend == "openai-compatible":
            model = self._local_openai_embed_model or self._local_openai_model
            try:
                import httpx

                response = httpx.post(
                    f"{self._local_openai_base_url}/v1/embeddings",
                    headers=self._local_openai_headers(),
                    json={"model": model, "input": text},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json().get("data") or []
                vector = data[0].get("embedding") if data else None
            except Exception as exc:
                raise AIProviderUnavailable(
                    f"OpenAI-compatible embedding failed: {exc}",
                ) from exc
            if not isinstance(vector, list) or not vector:
                raise AIProviderUnavailable(
                    f"server at {self._local_openai_base_url} returned no embedding "
                    f"for model {model!r}; set LOCAL_AI_EMBED_MODEL to a model that "
                    "serves /v1/embeddings",
                )
            return [float(v) for v in vector]

        if backend != "ollama":
            raise AIProviderUnavailable(
                f"embeddings require an embedding model; the {backend} backend is "
                "configured here for chat only. Run a self-hosted Ollama and set "
                f"OLLAMA_EMBED_MODEL (default {DEFAULT_OLLAMA_EMBED_MODEL}).",
            )

        try:
            import httpx

            response = httpx.post(
                f"{self._ollama_base_url}/api/embeddings",
                json={"model": self._ollama_embed_model, "prompt": text},
                timeout=60.0,
            )
            response.raise_for_status()
            vector = response.json().get("embedding")
        except Exception as exc:
            raise AIProviderUnavailable(f"ollama embedding failed: {exc}") from exc

        if not isinstance(vector, list) or not vector:
            raise AIProviderUnavailable(
                f"ollama returned no embedding for model {self._ollama_embed_model!r}; "
                "the model may not be pulled",
            )
        return [float(v) for v in vector]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed each text. Raises on the first failure rather than padding."""
        return [self.embed(t) for t in texts]


__all__ = ["AIProvider", "AIProviderUnavailable"]
