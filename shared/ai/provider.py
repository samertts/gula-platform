from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("gula.ai.provider")


class AIProvider:
    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash") -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._model = model
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            logger.warning("No AI API key configured — using stub mode")
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            self._client = genai.GenerativeModel(self._model)
        except ImportError:
            logger.warning("google.generativeai not installed — using raw HTTP fallback")

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        if self._client:
            try:
                response = self._client.generate_content(prompt, generation_config={"temperature": temperature})
                return response.text
            except Exception as exc:
                logger.error("AI generation failed: %s", exc)
        return ""

    def generate_structured(self, prompt: str, schema: type | None = None) -> Any:
        raw = self.generate(prompt, temperature=0.2)
        if not raw:
            return None
        import json
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None


__all__ = ["AIProvider"]
