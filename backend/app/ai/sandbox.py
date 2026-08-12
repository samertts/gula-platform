"""AI Sandbox — GULA Platform
============================
The only place where an approved AI suggestion can be executed.

Safety contract:
  - Only PendingApproval with status=APPROVED may enter.
  - Every execution is audited before and after.
  - Explicit operation whitelist — anything not registered is rejected at
    execution time, even if it was somehow approved.
  - No direct DB writes — handlers call internal service functions that
    enforce their own business rules.
  - All output is marked display_only=True unless explicitly opted out.

This is the airgap between the AI layer and the clinical core.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.ai.approval import PendingApproval, approval_store
from app.ai.guardrails import AIGuardrailViolation

logger = logging.getLogger("gula.ai.sandbox")

# ─── Execution Result ─────────────────────────────────────────────────────────


@dataclass
class SandboxResult:
    approval_id: str
    operation: str
    success: bool
    output: Any
    executed_at: float
    duration_ms: float
    error: str = ""


# ─── Operation Registry ───────────────────────────────────────────────────────

_REGISTRY: dict[str, Callable[[dict[str, Any]], Any]] = {}


def _register(operation: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[operation] = fn
        return fn

    return decorator


# ─── Handlers ─────────────────────────────────────────────────────────────────
# All handlers are read-only. They never write to the database.
# Output must always be treated as a suggestion for physician review.


@_register("suggest_interpretation")
def _suggest_interpretation(payload: dict[str, Any]) -> dict[str, Any]:
    """Interpret a single lab result using the rules-based interpretation engine.
    Delegates to app.services.interpretation — deterministic, no ML involved.
    """
    from app.services.interpretation import get_flag, interpret_result

    test_name = payload.get("test_name", "")
    value = payload.get("value")
    unit = payload.get("unit", "")
    normal_low = payload.get("normal_low")
    normal_high = payload.get("normal_high")

    if value is None:
        return {"interpretation": None, "flag": "unknown", "display_only": True}

    value = float(value)
    interp = interpret_result(test_name, value, normal_low, normal_high)
    flag = get_flag(value, normal_low, normal_high, test_name)

    return {
        "test_name": test_name,
        "value": value,
        "unit": unit,
        "flag": flag,
        "status": interp.get("status"),
        "interpretation": interp.get("interpretation"),
        "interpretation_ar": interp.get("interpretation_ar"),
        "advice": interp.get("advice"),
        "advice_ar": interp.get("advice_ar"),
        "display_only": True,
        "requires_doctor_review": flag in ("H", "L", "critical"),
    }


@_register("analyze_order")
def _analyze_order(payload: dict[str, Any]) -> dict[str, Any]:
    """Run multi-test clinical pattern analysis on an order's results.
    Uses the rules-based clinical_intelligence engine (deterministic, not ML).

    Returns pattern alerts + per-result flag summary + individual interpretations.
    Everything is display_only — no DB writes.
    """
    from app.services.clinical_intelligence import analyze_results, quick_flag_summary
    from app.services.interpretation import get_flag, interpret_result

    order_id = payload.get("order_id")
    result_list: list[dict] = payload.get("result_list", [])

    # 1. Multi-test pattern analysis (sepsis, DKA, renal failure, etc.)
    patterns = analyze_results(result_list)

    # 2. Flag summary counts
    flag_summary = quick_flag_summary(result_list)

    # 3. Per-result interpretations
    interpretations = []
    for r in result_list:
        value = r.get("value")
        if value is None:
            continue
        value = float(value)
        test_name = r.get("test_name", "")
        normal_low = r.get("normal_range_low")
        normal_high = r.get("normal_range_high")

        interp = interpret_result(test_name, value, normal_low, normal_high)
        flag = get_flag(value, normal_low, normal_high, test_name)

        interpretations.append(
            {
                "test_name": test_name,
                "value": value,
                "unit": r.get("unit", ""),
                "flag": flag,
                "status": interp.get("status"),
                "interpretation": interp.get("interpretation"),
                "interpretation_ar": interp.get("interpretation_ar"),
                "advice": interp.get("advice"),
                "advice_ar": interp.get("advice_ar"),
            },
        )

    return {
        "order_id": order_id,
        "patterns": patterns,
        "flag_summary": flag_summary,
        "interpretations": interpretations,
        "display_only": True,
        "source": "rules_based_engine",
    }


@_register("summarize_history")
def _summarize_history(payload: dict[str, Any]) -> dict[str, Any]:
    """Plain-text summary of patient history (display only)."""
    order_count = payload.get("order_count", 0)
    recent_tests = payload.get("recent_tests", [])
    return {
        "summary": f"Patient has {order_count} orders. Recent: {', '.join(recent_tests) or 'none'}",
        "display_only": True,
    }


@_register("flag_anomaly")
def _flag_anomaly(payload: dict[str, Any]) -> dict[str, Any]:
    """Suggest flagging a result for human review (does not write anything)."""
    return {
        "flagged": True,
        "reason": payload.get("reason", "AI detected anomaly"),
        "display_only": False,
        "requires_doctor_review": True,
    }


@_register("translate_report")
def _translate_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Placeholder for bilingual report translation (ENRICHMENT only)."""
    return {
        "translated": payload.get("text", ""),
        "language": payload.get("target_language", "ar"),
        "display_only": True,
    }


# ─── Sandbox ─────────────────────────────────────────────────────────────────


class AISandbox:
    """Executes approved AI operations in an isolated, audited context.

    Usage::

        result = AISandbox.execute(approval)
        if result.success:
            return result.output   # always display_only
    """

    @staticmethod
    def execute(approval: PendingApproval) -> SandboxResult:
        start = time.monotonic()
        op = approval.suggestion.operation

        if not approval.is_executable:
            raise AIGuardrailViolation(
                f"Cannot execute approval {approval.id}: status={approval.status.value}",
            )

        if op not in _REGISTRY:
            raise AIGuardrailViolation(
                f"Operation '{op}' is not in the AI sandbox whitelist. "
                "Only explicitly registered operations can be executed.",
            )

        logger.info(
            "[AI_SANDBOX] executing id=%s operation=%s entity=%s/%s approved_by=%s",
            approval.id,
            op,
            approval.suggestion.entity_type or "—",
            approval.suggestion.entity_id or "—",
            approval.reviewed_by or "—",
        )

        try:
            output = _REGISTRY[op](approval.suggestion.payload)
            duration_ms = (time.monotonic() - start) * 1000
            approval_store.mark_executed(approval.id)

            logger.info(
                "[AI_SANDBOX] completed id=%s operation=%s duration_ms=%.1f",
                approval.id,
                op,
                duration_ms,
            )

            return SandboxResult(
                approval_id=approval.id,
                operation=op,
                success=True,
                output=output,
                executed_at=time.time(),
                duration_ms=duration_ms,
            )

        except AIGuardrailViolation:
            raise
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.error(
                "[AI_SANDBOX] failed id=%s operation=%s error=%r duration_ms=%.1f",
                approval.id,
                op,
                str(exc),
                duration_ms,
            )
            return SandboxResult(
                approval_id=approval.id,
                operation=op,
                success=False,
                output=None,
                executed_at=time.time(),
                duration_ms=duration_ms,
                error=str(exc),
            )

    @staticmethod
    def register(operation: str) -> Callable:
        """Decorator to add a custom operation to the sandbox whitelist."""
        return _register(operation)

    @staticmethod
    def registered_operations() -> list[str]:
        return list(_REGISTRY.keys())
