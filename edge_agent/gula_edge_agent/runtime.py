"""AI runtime layer — pluggable execution backend.

Two backends out of the box:
  - "noop"   — diagnostic-only; every task succeeds with an echo result
  - "ollama" — calls a local Ollama HTTP server (default localhost:11434)

Production deployments may add custom backends (llama.cpp, ONNX, etc.) by
subclassing `Runtime`.

Importantly, the runtime never trusts task payloads with shell commands — it
only routes by `kind` and reads/writes typed parameters from `payload`.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger("gula.edge.runtime")


class Runtime:
    """Base class. Subclasses implement `run(kind, payload) -> dict`."""

    async def run(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def warmup(self, models: list[dict[str, Any]]) -> None:
        """Pre-load a list of models. Default: no-op."""
        return


class NoopRuntime(Runtime):
    async def run(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"runtime": "noop", "kind": kind, "echo": payload, "ts": time.time()}


class OllamaRuntime(Runtime):
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def warmup(self, models: list[dict[str, Any]]) -> None:
        if not models:
            return
        c = await self._http()
        for m in models:
            name = m.get("name") or m.get("model_uid")
            if not name:
                continue
            try:
                # `pull` on Ollama is idempotent.
                await c.post(f"{self.base_url}/api/pull",
                             json={"name": name}, timeout=600.0)
                logger.info("warmed model: %s", name)
            except Exception as exc:
                logger.warning("warmup failed for %s: %s", name, exc)

    async def run(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        c = await self._http()

        if kind == "ai.summarize_report":
            return await self._chat(c, payload, system=(
                "You are a clinical summarizer. Produce a concise Arabic + "
                "English summary of the lab report. Do not invent values."
            ))

        if kind == "ai.translate":
            target = payload.get("target", "ar")
            return await self._chat(c, payload, system=(
                f"Translate the user's text into {target}. "
                "Preserve numeric values exactly."
            ))

        if kind == "ai.classify":
            return await self._chat(c, payload, system=(
                "Classify the input as one of: normal, abnormal, critical. "
                'Reply with JSON: {"label": ..., "confidence": 0.0-1.0}'
            ))

        if kind == "ai.extract_lab_values":
            return await self._chat(c, payload, system=(
                "Extract lab values from the input text and return JSON: "
                '[{"test": str, "value": number, "unit": str}, ...]'
            ))

        if kind == "ai.embed":
            model = payload.get("model", "nomic-embed-text")
            r = await c.post(f"{self.base_url}/api/embeddings",
                             json={"model": model,
                                   "prompt": payload.get("text", "")})
            r.raise_for_status()
            return {"embedding": r.json().get("embedding", [])}

        if kind == "diag.ping":
            return {"pong": True, "ts": time.time()}

        if kind == "diag.benchmark":
            t0 = time.perf_counter()
            await self._chat(c, {"text": "ping"}, system="Reply with 'pong'.")
            return {"latency_ms": int((time.perf_counter() - t0) * 1000)}

        # Fallback — kind handled by sandbox not the runtime
        raise RuntimeError(f"runtime cannot handle kind={kind}")

    async def _chat(self, c: httpx.AsyncClient, payload: dict, *, system: str) -> dict:
        model = payload.get("model", "qwen2:1.5b")
        text  = payload.get("text", "")
        r = await c.post(f"{self.base_url}/api/chat",
                         json={
                             "model":    model,
                             "messages": [
                                 {"role": "system", "content": system},
                                 {"role": "user",   "content": text},
                             ],
                             "stream":   False,
                         })
        r.raise_for_status()
        body = r.json()
        return {"model": model, "response": body.get("message", {}).get("content", "")}


def make_runtime(name: str, **kwargs: Any) -> Runtime:
    name = name.lower()
    if name == "ollama":
        return OllamaRuntime(base_url=kwargs.get("ollama_url",
                                                 "http://127.0.0.1:11434"))
    if name == "noop":
        return NoopRuntime()
    raise ValueError(f"unknown runtime: {name}")
