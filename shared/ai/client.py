from __future__ import annotations

import json
import logging
from typing import Any

from shared.ai.provider import AIProvider, AIProviderUnavailable

logger = logging.getLogger("gula.ai")


class AIClient:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or AIProvider()

    def interpret(self, test_name: str, value: float, reference_range: tuple[float, float], unit: str = "") -> dict[str, Any]:
        low, high = reference_range
        prompt = (
            f"Test: {test_name}, Value: {value} {unit}, Reference Range: {low}-{high} {unit}. "
            "Provide: 1) Interpretation (normal/abnormal/flag), 2) Clinical significance, "
            "3) Recommendation. Return valid JSON only."
        )
        try:
            response = self._provider.generate(prompt, temperature=0.2)
            parsed = dict(json.loads(response))
            parsed["engine"] = self._provider.backend
            parsed["ai_generated"] = True
            return parsed
        except AIProviderUnavailable as exc:
            # IA-074: the deterministic fallback below is legitimate clinical
            # logic -- it compares the value against the range the CALLER
            # supplied and invents no reference range, threshold or rule. The
            # defect was that it returned the same shape as an AI
            # interpretation with nothing to distinguish them, so a clinician
            # or a downstream system could not tell which it had received.
            logger.info("AI unavailable, using deterministic range check: %s", exc)
            return self._deterministic_interpretation(value, low, high, reason=str(exc))
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("AI returned unparseable interpretation; falling back")
            return self._deterministic_interpretation(
                value, low, high, reason="model output was not valid JSON",
            )

    @staticmethod
    def _deterministic_interpretation(
        value: float, low: float, high: float, *, reason: str,
    ) -> dict[str, Any]:
        """A range comparison, labelled as exactly that.

        ``ai_generated`` is False and ``engine`` names the method, so no caller
        can mistake this for a model-derived clinical interpretation.
        """
        abnormal = value < low or value > high
        return {
            "interpretation": "Flag: abnormal" if abnormal else "Normal",
            "clinical_significance": f"Value {value} {'outside' if abnormal else 'within'} range",
            "recommendation": "Review by clinician",
            "engine": "deterministic-range-check",
            "ai_generated": False,
            "fallback_reason": reason,
        }

    @property
    def available(self) -> bool:
        """Whether an inference backend exists. Ask before an AI-only path."""
        return self._provider.available

    def analyze(self, prompt: str, temperature: float = 0.3) -> str:
        """Free-text analysis.

        Deliberately propagates AIProviderUnavailable: there is no honest
        non-AI substitute for an open-ended analysis prompt, so returning ""
        would have been a fabricated empty answer.
        """
        return self._provider.generate(prompt, temperature=temperature)

    def analyze_structured(self, prompt: str, temperature: float = 0.2) -> dict[str, Any]:
        response = self._provider.generate(prompt, temperature=temperature)
        try:
            return dict(json.loads(response))
        except (json.JSONDecodeError, TypeError, ValueError):
            # A real reply that is not JSON. Returned under a key that says so.
            return {"response": response, "parsed": False}


__all__ = ["AIClient"]
