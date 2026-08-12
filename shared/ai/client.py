from __future__ import annotations

import json
import logging
from typing import Any

from shared.ai.provider import AIProvider

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
        response = self._provider.generate(prompt, temperature=0.2)
        try:
            return dict(json.loads(response))
        except (json.JSONDecodeError, TypeError, ValueError):
            abnormal = value < low or value > high
            return {
                "interpretation": "Flag: abnormal" if abnormal else "Normal",
                "clinical_significance": f"Value {value} {'outside' if abnormal else 'within'} range",
                "recommendation": "Review by clinician",
            }

    def analyze(self, prompt: str, temperature: float = 0.3) -> str:
        return self._provider.generate(prompt, temperature=temperature)

    def analyze_structured(self, prompt: str, temperature: float = 0.2) -> dict[str, Any]:
        response = self._provider.generate(prompt, temperature=temperature)
        try:
            return dict(json.loads(response))
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"response": response}


__all__ = ["AIClient"]
