from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("gula.ai.embeddings")

_EMBEDDING_API_KEY = os.getenv("GEMINI_API_KEY", "")
_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
_EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
_EMBEDDING_TIMEOUT = float(os.getenv("AI_BUDGET_SECONDS", "6"))

_REST_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={key}"
)


async def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    if _EMBEDDING_API_KEY:
        return await _embed_with_gemini(text, task_type)
    return _embed_fallback(text)


async def embed_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    if not texts:
        return []
    if _EMBEDDING_API_KEY:
        return await _embed_batch_gemini(texts, task_type)
    return [_embed_fallback(t) for t in texts]


async def _embed_with_gemini(text: str, task_type: str) -> list[float]:
    url = _REST_URL.format(model=_EMBEDDING_MODEL, key=_EMBEDDING_API_KEY)
    payload = {
        "model": f"models/{_EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
    }
    async with httpx.AsyncClient(timeout=_EMBEDDING_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    data = r.json()
    return data["embedding"]["values"]


async def _embed_batch_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    import asyncio

    tasks = [embed_text(t, task_type) for t in texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r if isinstance(r, list) else _embed_fallback(texts[i]) for i, r in enumerate(results)]


def _embed_fallback(text: str) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    dims = _EMBEDDING_DIMENSIONS
    vec = [(b / 255.0) * 2 - 1 for b in h]
    if len(vec) < dims:
        vec.extend([0.0] * (dims - len(vec)))
    else:
        vec = vec[:dims]
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def is_configured() -> bool:
    return bool(_EMBEDDING_API_KEY)


def embedding_model_info() -> dict[str, Any]:
    return {
        "configured": is_configured(),
        "model": _EMBEDDING_MODEL,
        "dimensions": _EMBEDDING_DIMENSIONS,
        "provider": "gemini" if _EMBEDDING_API_KEY else "fallback_hash",
    }
