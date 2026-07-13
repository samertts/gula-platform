"""
Google AI Studio gateway — GULA Platform
Official SDK: https://aistudio.google.com/apikey

Priority: SDK (google-generativeai) → raw HTTP fallback.
The fallback keeps existing deployments working if the package is not yet installed.
"""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger("gula.google_ai")

# ── Configuration ─────────────────────────────────────────────────────────────
_API_KEY = os.getenv("GEMINI_API_KEY", "")
_CLINICAL_MODEL = os.getenv("GEMINI_CLINICAL_MODEL", "gemini-2.0-flash")
_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
_CLINICAL_TOKENS = int(os.getenv("GEMINI_CLINICAL_MAX_TOKENS", "500"))
_CHAT_TOKENS = int(os.getenv("GEMINI_CHAT_MAX_TOKENS", "600"))
_TIMEOUT = float(os.getenv("AI_BUDGET_SECONDS", "6"))

# REST endpoint (fallback when SDK is not installed)
_REST_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)

# ── SDK bootstrap (optional dependency) ──────────────────────────────────────
_genai = None
_sdk_available = False

if _API_KEY:
    try:
        import google.generativeai as genai  # type: ignore[import]

        genai.configure(api_key=_API_KEY)
        _genai = genai
        _sdk_available = True
        logger.info(
            "[GoogleAI] SDK ready — clinical=%s chat=%s",
            _CLINICAL_MODEL,
            _CHAT_MODEL,
        )
    except ImportError:
        logger.info(
            "[GoogleAI] google-generativeai not installed; raw HTTP fallback active. "
            "Install: pip install 'google-generativeai>=0.8.0'"
        )

# ── System instructions ───────────────────────────────────────────────────────
_CLINICAL_SYSTEM = (
    "أنت مساعد توعوي طبي. مهمتك شرح نتائج التحاليل للمريض بأسلوب بسيط ومفهوم. "
    "لا تُشخّص أمراضاً ولا تصف أدوية ولا توصي بعلاجات بأي شكل."
)

_CHAT_SYSTEM = (
    "أنت مساعد ذكي لمنصة GULA للمختبرات الطبية. "
    "تساعد موظفي المختبر وأطباء المختبر على إدارة الطلبات والنتائج والمرضى. "
    "ردودك بالعربية ما لم يُطلب غير ذلك. "
    "لا تُشخّص أمراضاً ولا تصف دواءً — هذا دور الطبيب المعالج. "
    "كن موجزاً ودقيقاً ومفيداً."
)

_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


# ── Public helpers ────────────────────────────────────────────────────────────


def is_configured() -> bool:
    """True when an API key is present (SDK or HTTP both usable)."""
    return bool(_API_KEY)


def sdk_available() -> bool:
    """True only when the google-generativeai SDK is installed and initialised."""
    return _sdk_available


# ── Clinical interpretation ───────────────────────────────────────────────────


async def generate_clinical(prompt: str) -> str:
    """
    Generate a plain-Arabic lab-result explanation.

    Uses the SDK when available (proper system_instruction + safety settings),
    otherwise falls back to raw HTTPS.
    """
    if not _API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    if _sdk_available:
        return await _sdk_clinical(prompt)
    return await _http_clinical(prompt)


async def _sdk_clinical(prompt: str) -> str:
    loop = asyncio.get_event_loop()

    def _call() -> str:
        model = _genai.GenerativeModel(
            model_name=_CLINICAL_MODEL,
            system_instruction=_CLINICAL_SYSTEM,
            safety_settings=_SAFETY_SETTINGS,
            generation_config=_genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=_CLINICAL_TOKENS,
            ),
        )
        resp = model.generate_content(prompt)
        if not resp.candidates:
            raise RuntimeError("Gemini returned no candidates")
        return resp.text.strip()

    return await loop.run_in_executor(None, _call)


async def _http_clinical(prompt: str) -> str:
    url = _REST_URL.format(model=_CLINICAL_MODEL, key=_API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": _CLINICAL_TOKENS},
        "safetySettings": _SAFETY_SETTINGS,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


# ── Assistant chat ────────────────────────────────────────────────────────────


async def generate_chat(message: str, context: str | None = None) -> str:
    """
    Generate an assistant chat reply for lab staff.

    Uses the SDK when available (system_instruction kept separate from user message),
    otherwise falls back to raw HTTPS with an inline system prefix.
    """
    if not _API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    if _sdk_available:
        return await _sdk_chat(message, context)
    return await _http_chat(message, context)


async def _sdk_chat(message: str, context: str | None = None) -> str:
    loop = asyncio.get_event_loop()

    system = _CHAT_SYSTEM
    if context:
        system += f"\nالصفحة الحالية: {context}"

    def _call() -> str:
        model = _genai.GenerativeModel(
            model_name=_CHAT_MODEL,
            system_instruction=system,
            safety_settings=_SAFETY_SETTINGS,
            generation_config=_genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=_CHAT_TOKENS,
            ),
        )
        resp = model.generate_content(message)
        if not resp.candidates:
            raise RuntimeError("Gemini returned no candidates")
        return resp.text.strip()

    return await loop.run_in_executor(None, _call)


async def _http_chat(message: str, context: str | None = None) -> str:
    system = _CHAT_SYSTEM
    if context:
        system += f"\nالصفحة الحالية: {context}"

    url = _REST_URL.format(model=_CHAT_MODEL, key=_API_KEY)
    payload = {
        "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n---\n{message}"}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": _CHAT_TOKENS},
        "safetySettings": _SAFETY_SETTINGS,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini returned unexpected shape: {exc}") from exc


# ── Provider metadata ─────────────────────────────────────────────────────────


def provider_info() -> dict:
    return {
        "name": "gemini",
        "type": "cloud",
        "source": "aistudio.google.com",
        "configured": is_configured(),
        "sdk_available": sdk_available(),
        "clinical_model": _CLINICAL_MODEL,
        "chat_model": _CHAT_MODEL,
        "cost": "free tier (1500 req/day, 15 req/min)",
    }
