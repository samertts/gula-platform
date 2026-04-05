"""Structured AI Output — JSON schema enforcement + confidence gating.

Problem: Unstructured AI text output is fragile — consumers must parse it,
and hallucinated format breaks downstream systems.

Solution: Ask the AI to return strict JSON matching a defined schema.
Validate the response against the schema. If invalid, fall back to
unstructured text with a flag. Gate on confidence threshold.

Rules Engine remains the final arbiter of all clinical decisions.
AI output is advisory only — this module enforces that invariant.

Usage::

    from app.services.structured_ai import StructuredAIEngine, InterpretationSchema

    engine = StructuredAIEngine()
    result = await engine.interpret(results_data, patient_context=ctx)

    if result.valid and result.confidence >= 0.7:
        # use result.data (guaranteed to match InterpretationSchema)
        ...
    else:
        # show result.text (unstructured fallback) or show nothing
        ...
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger("gula.structured_ai")

# ── Provider configuration ────────────────────────────────────────────────────
_GEMINI_KEY  = os.getenv("GEMINI_API_KEY", "")
_GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
_GEMINI_URL  = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Confidence gate threshold ─────────────────────────────────────────────────
MIN_CONFIDENCE_TO_USE = 0.60   # below this → fall back to unstructured text

# ── JSON schemas ─────────────────────────────────────────────────────────────

# Schema for lab result interpretation
INTERPRETATION_SCHEMA: dict = {
    "type": "object",
    "required": ["summary", "items", "overall_severity", "action_ar", "disclaimer_included"],
    "properties": {
        "summary": {
            "type": "string",
            "description": "One sentence Arabic summary of all results",
            "maxLength": 300,
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["test_name", "status", "explanation_ar"],
                "properties": {
                    "test_name":      {"type": "string"},
                    "status":         {"type": "string", "enum": ["normal", "low", "high", "critical"]},
                    "explanation_ar": {"type": "string", "maxLength": 200},
                },
                "additionalProperties": False,
            },
        },
        "overall_severity":     {"type": "string", "enum": ["normal", "warning", "critical"]},
        "action_ar":            {"type": "string", "maxLength": 200},
        "disclaimer_included":  {"type": "boolean"},
        "confidence_note":      {"type": "string"},
    },
    "additionalProperties": False,
}

# Schema for fraud advisory (AI advisory input to the fraud engine)
FRAUD_ADVISORY_SCHEMA: dict = {
    "type": "object",
    "required": ["risk_score", "explanation", "flags"],
    "properties": {
        "risk_score":  {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "explanation": {"type": "string", "maxLength": 300},
        "flags":       {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10,
        },
        "confidence":  {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
    "additionalProperties": False,
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class AIResult:
    """Output of StructuredAIEngine."""
    valid:        bool            # True = JSON validated against schema
    data:         dict | None     # Validated JSON data (None if invalid)
    text:         str             # Raw AI text (always present for logging)
    confidence:   float           # 0.0–1.0 estimated confidence
    provider:     str             # Which AI provider was used
    schema_errors: list[str] = field(default_factory=list)
    usable:       bool = False    # valid AND confidence >= threshold

    def __post_init__(self) -> None:
        self.usable = self.valid and self.confidence >= MIN_CONFIDENCE_TO_USE


# ── Schema validator (no external dependency) ─────────────────────────────────

def _validate_schema(data: Any, schema: dict, path: str = "") -> list[str]:
    """
    Lightweight JSON schema validator — no jsonschema library required.
    Validates: type, required, enum, minimum, maximum, maxLength, additionalProperties.
    Returns list of error strings (empty = valid).
    """
    errors: list[str] = []

    if schema.get("type") == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object, got {type(data).__name__}"]

        # Check required fields
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}.{req}: required field missing")

        # Check additionalProperties
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            extra = set(data.keys()) - allowed
            if extra:
                errors.append(f"{path}: unexpected fields: {extra}")

        # Recurse into properties
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if prop_name in data:
                sub_errors = _validate_schema(
                    data[prop_name], prop_schema, path=f"{path}.{prop_name}"
                )
                errors.extend(sub_errors)

    elif schema.get("type") == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array, got {type(data).__name__}"]
        max_items = schema.get("maxItems")
        if max_items and len(data) > max_items:
            errors.append(f"{path}: array length {len(data)} > maxItems {max_items}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(data):
                sub_errors = _validate_schema(item, item_schema, path=f"{path}[{i}]")
                errors.extend(sub_errors)

    elif schema.get("type") == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: expected string, got {type(data).__name__}")
        else:
            max_len = schema.get("maxLength")
            if max_len and len(data) > max_len:
                errors.append(f"{path}: string length {len(data)} > maxLength {max_len}")
            enum = schema.get("enum")
            if enum and data not in enum:
                errors.append(f"{path}: value {data!r} not in {enum}")

    elif schema.get("type") == "number":
        if not isinstance(data, (int, float)):
            errors.append(f"{path}: expected number, got {type(data).__name__}")
        else:
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            if minimum is not None and data < minimum:
                errors.append(f"{path}: {data} < minimum {minimum}")
            if maximum is not None and data > maximum:
                errors.append(f"{path}: {data} > maximum {maximum}")

    elif schema.get("type") == "boolean":
        if not isinstance(data, bool):
            errors.append(f"{path}: expected boolean, got {type(data).__name__}")

    return errors


def _extract_json(text: str) -> dict | None:
    """
    Try to extract a JSON object from AI text output.
    Handles:
      - Pure JSON response
      - JSON wrapped in ```json ... ``` code block
      - JSON somewhere in the middle of text
    """
    # Strip markdown code block if present
    code_block = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    candidate = code_block.group(1) if code_block else text.strip()

    # Try direct parse
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find the first { ... } balanced block
    depth = 0
    start = -1
    for i, ch in enumerate(candidate):
        if ch == "{":
            if start == -1:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(candidate[start:i + 1])
                except (json.JSONDecodeError, ValueError):
                    pass
                start = -1
    return None


# ── AI callers ────────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    url = _GEMINI_URL.format(key=_GEMINI_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":    0.1,   # low temp for structured output
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",  # Gemini JSON mode
        },
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _call_groq(prompt: str) -> str:
    payload = {
        "model":       "llama-3.1-8b-instant",
        "messages":    [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens":  800,
        "response_format": {"type": "json_object"},  # Groq JSON mode
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            _GROQ_URL, json=payload,
            headers={"Authorization": f"Bearer {_GROQ_KEY}"},
        )
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# ── Prompt builders ───────────────────────────────────────────────────────────

def _build_interpretation_prompt_json(
    results_data: list[dict],
    patient_context: Optional[dict] = None,
) -> str:
    """Build a prompt that requests a JSON-structured interpretation."""
    ctx_parts = []
    if patient_context:
        if patient_context.get("age"):
            ctx_parts.append(f"age: {patient_context['age']}")
        if patient_context.get("gender"):
            ctx_parts.append(f"gender: {patient_context['gender']}")
    ctx_str = ", ".join(ctx_parts)

    results_lines = []
    for r in results_data:
        val  = r.get("value") or r.get("value_text", "-")
        unit = r.get("unit", "") or ""
        low  = r.get("normal_range_low")
        high = r.get("normal_range_high")
        rng  = f"normal: {low}–{high}" if (low is not None and high is not None) else "no range"
        results_lines.append(f"  - {r.get('test_name','')}: {val} {unit} ({rng})")

    schema_str = json.dumps(INTERPRETATION_SCHEMA, ensure_ascii=False, indent=2)

    return f"""You are a medical lab result interpreter. Output ONLY valid JSON matching this schema:

{schema_str}

Patient context: {ctx_str or 'none'}

Lab results:
{chr(10).join(results_lines)}

Rules:
- explanation_ar must be in Arabic, ≤ 200 chars per item
- summary must be in Arabic, ≤ 300 chars
- No drug names, no diagnoses, no treatment recommendations
- disclaimer_included must be true if summary contains: "هذه النتائج للإعلام فقط"
- overall_severity: "normal" if all normal, "warning" if any out of range, "critical" if any critical
- action_ar: appropriate action guidance in Arabic

Output ONLY the JSON object, no other text."""


def _build_fraud_advisory_prompt_json(
    claim_context: dict,
) -> str:
    """Build a prompt for AI fraud advisory scoring."""
    schema_str = json.dumps(FRAUD_ADVISORY_SCHEMA, ensure_ascii=False, indent=2)
    return f"""You are a medical insurance fraud detection assistant. Output ONLY valid JSON matching:

{schema_str}

Claim context:
{json.dumps(claim_context, ensure_ascii=False, indent=2)}

Analyze this claim for fraud risk. Consider:
- Is the amount proportionate to the tests ordered?
- Are the diagnosis codes consistent with the tests?
- Is the timing suspicious?

risk_score: 0.0 = no risk, 1.0 = definite fraud
Output ONLY the JSON object."""


# ── Main engine ───────────────────────────────────────────────────────────────

class StructuredAIEngine:
    """
    Structured AI output engine.

    Wraps AI provider calls with:
      1. JSON-mode prompt construction
      2. Provider fallback (Gemini → Groq)
      3. JSON extraction from response
      4. Schema validation
      5. Confidence gating
      6. Audit logging
    """

    async def interpret(
        self,
        results_data: list[dict],
        patient_context: Optional[dict] = None,
    ) -> AIResult:
        """
        Generate a structured JSON interpretation of lab results.

        Returns AIResult. Check .usable before trusting .data.
        If not usable, show .text as unstructured fallback.
        """
        prompt = _build_interpretation_prompt_json(results_data, patient_context)
        return await self._call_and_validate(prompt, INTERPRETATION_SCHEMA, "interpret")

    async def fraud_advisory(self, claim_context: dict) -> AIResult:
        """
        Generate an AI fraud advisory score for a claim.

        This is ADVISORY only — the Rules Engine decides final fraud decision.
        Result is logged and stored in FraudScore.ai_explanation.
        """
        prompt = _build_fraud_advisory_prompt_json(claim_context)
        return await self._call_and_validate(prompt, FRAUD_ADVISORY_SCHEMA, "fraud_advisory")

    async def _call_and_validate(
        self,
        prompt: str,
        schema: dict,
        operation: str,
    ) -> AIResult:
        """Core: call AI → extract JSON → validate → gate confidence."""
        t0 = time.monotonic()
        providers = []
        if _GEMINI_KEY:
            providers.append(("gemini", _call_gemini))
        if _GROQ_KEY:
            providers.append(("groq", _call_groq))

        if not providers:
            return AIResult(
                valid=False,
                data=None,
                text="",
                confidence=0.0,
                provider="none",
                schema_errors=["no AI providers configured"],
            )

        raw_text = ""
        provider_used = "none"
        last_exc: Exception | None = None

        for name, caller in providers:
            try:
                raw_text = await caller(prompt)
                provider_used = name
                break
            except Exception as exc:
                logger.warning("[StructuredAI] Provider %s failed (%s): %s", name, operation, exc)
                last_exc = exc

        if not raw_text:
            logger.error("[StructuredAI] All providers failed for %s: %s", operation, last_exc)
            return AIResult(
                valid=False,
                data=None,
                text="",
                confidence=0.0,
                provider="none",
                schema_errors=["all providers failed"],
            )

        # Extract JSON
        parsed = _extract_json(raw_text)
        if parsed is None:
            logger.warning(
                "[StructuredAI] Failed to extract JSON from %s response (len=%d)",
                provider_used, len(raw_text),
            )
            return AIResult(
                valid=False,
                data=None,
                text=raw_text,
                confidence=0.3,
                provider=provider_used,
                schema_errors=["JSON extraction failed"],
            )

        # Validate schema
        errors = _validate_schema(parsed, schema)
        if errors:
            logger.warning(
                "[StructuredAI] Schema validation failed (%d errors) provider=%s: %s",
                len(errors), provider_used, errors[:3],
            )
            return AIResult(
                valid=False,
                data=parsed,   # partial data available
                text=raw_text,
                confidence=0.4,
                provider=provider_used,
                schema_errors=errors,
            )

        # Estimate confidence (basic heuristics)
        confidence = self._estimate_confidence(parsed, schema, provider_used)

        elapsed_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "[StructuredAI] %s OK provider=%s confidence=%.2f elapsed=%.0fms",
            operation, provider_used, confidence, elapsed_ms,
        )

        return AIResult(
            valid=True,
            data=parsed,
            text=raw_text,
            confidence=confidence,
            provider=provider_used,
        )

    @staticmethod
    def _estimate_confidence(data: dict, schema: dict, provider: str) -> float:
        """
        Estimate confidence from response quality signals.
        Higher-quality providers and complete responses get higher confidence.
        """
        score = 0.70   # base

        # Provider bonus (Gemini tends to follow JSON schema more reliably)
        if provider == "gemini":
            score += 0.10
        elif provider == "groq":
            score += 0.05

        # Penalise if items array is empty (no per-test analysis)
        if "items" in data and isinstance(data["items"], list):
            if len(data["items"]) == 0:
                score -= 0.20
            elif len(data["items"]) >= 3:
                score += 0.05

        # Penalise very short summary
        if "summary" in data and isinstance(data["summary"], str):
            if len(data["summary"]) < 20:
                score -= 0.15

        # Bonus for explicit confidence note
        if data.get("confidence_note"):
            score += 0.05

        return min(1.0, max(0.0, score))


# ── Singleton ─────────────────────────────────────────────────────────────────
_engine: StructuredAIEngine | None = None


def get_structured_ai() -> StructuredAIEngine:
    global _engine
    if _engine is None:
        _engine = StructuredAIEngine()
    return _engine
