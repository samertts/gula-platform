"""
AI Sandbox — GULA Platform
============================
The only place where an approved AI suggestion can be executed.

Safety contract:
  - Only PendingApproval objects with status=APPROVED can enter.
  - Every execution is fully audited before and after.
  - The sandbox holds an explicit whitelist of allowed operations and their handlers.
  - Any operation not in the whitelist is rejected at execution time,
    even if it was somehow approved.
  - No direct DB writes — the sandbox calls internal service functions that
    enforce their own business rules (RBAC, state machine, etc.).

This is the airgap between the AI layer and the clinical core.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from app.ai.approval import ApprovalStatus, PendingApproval, approval_store
from app.ai.guardrails import AIGuardrailViolation

logger = logging.getLogger("gula.ai.sandbox")


# ─── Execution Result ─────────────────────────────────────────────────────────

@dataclass
class SandboxResult:
    approval_id: str
    operation:   str
    success:     bool
    output:      Any
    executed_at: float
    duration_ms: float
    error:       str = ""


# ─── Operation Registry ───────────────────────────────────────────────────────

# Handlers registered via @AISandbox.register(operation_name)
# Signature: (payload: dict) -> Any
_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Any]] = {}


def _register(operation: str) -> Callable:
    """Decorator: register a handler for a sandboxed operation."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[operation] = fn
        return fn
    return decorator


# ─── Built-in Handlers ────────────────────────────────────────────────────────
# These are the ONLY operations the sandbox will execute.
# All handlers are pure read/suggest operations — they never mutate clinical state.

@_register("suggest_interpretation")
def _suggest_interpretation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a text interpretation suggestion for a lab result.
    This is DISPLAY ONLY — the suggestion must be reviewed by a human.
    """
    test_name  = payload.get("test_name", "")
    value      = payload.get("value")
    unit       = payload.get("unit", "")
    normal_low = payload.get("normal_low")
    normal_high = payload.get("normal_high")

    if value is None:
        return {"interpretation": "", "flag": "unknown", "display_only": True}

    flag = "normal"
    if normal_low is not None and value < normal_low:
        flag = "low"
    elif normal_high is not None and value > normal_high:
        flag = "high"

    return {
        "test_name":      test_name,
        "value":          value,
        "unit":           unit,
        "flag":           flag,
        "interpretation": f"{test_name}: {value} {unit} — {flag}",
        "display_only":   True,
        "requires_doctor_review": flag in ("low", "high"),
    }


@_register("summarize_history")
def _summarize_history(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a plain-text summary of patient history data.
    DISPLAY ONLY — never stored without explicit doctor action.
    """
    order_count  = payload.get("order_count", 0)
    recent_tests = payload.get("recent_tests", [])
    return {
        "summary":      f"Patient has {order_count} orders. Recent: {', '.join(recent_tests) or 'none'}",
        "display_only": True,
    }


@_register("flag_anomaly")
def _flag_anomaly(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest flagging a result for human review.
    Returns a flag recommendation — does NOT write anything.
    """
    return {
        "flagged":      True,
        "reason":       payload.get("reason", "AI detected anomaly"),
        "display_only": False,   # this one requires approval to store
        "requires_doctor_review": True,
    }


@_register("translate_report")
def _translate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder for report translation (ENRICHMENT only)."""
    return {
        "translated": payload.get("text", ""),
        "language":   payload.get("target_language", "ar"),
        "display_only": True,
    }


# ─── Sandbox ─────────────────────────────────────────────────────────────────

class AISandbox:
    """
    Executes approved AI operations in an isolated context.

    Usage::

        result = AISandbox.execute(approval)
        if result.success:
            return result.output
    """

    @staticmethod
    def execute(approval: PendingApproval) -> SandboxResult:
        """
        Execute an approved suggestion.

        Raises AIGuardrailViolation if:
          - The approval is not in APPROVED status.
          - The operation is not in the registry whitelist.
        """
        start = time.monotonic()
        op    = approval.suggestion.operation

        # ── Pre-execution safety checks ───────────────────────────────────────

        if not approval.is_executable:
            raise AIGuardrailViolation(
                f"Cannot execute approval {approval.id}: "
                f"status={approval.status.value}"
            )

        if op not in _REGISTRY:
            raise AIGuardrailViolation(
                f"Operation '{op}' is not registered in the AI sandbox. "
                "Only explicitly whitelisted operations can be executed by AI."
            )

        # ── Audit: record intent before execution ─────────────────────────────
        logger.info(
            "[AI_SANDBOX] executing id=%s operation=%s entity=%s/%s approved_by=%s",
            approval.id,
            op,
            approval.suggestion.entity_type or "—",
            approval.suggestion.entity_id or "—",
            approval.reviewed_by or "—",
        )

        # ── Execute ───────────────────────────────────────────────────────────
        handler = _REGISTRY[op]
        try:
            output = handler(approval.suggestion.payload)
            approval_store.mark_executed(approval.id)
            duration_ms = (time.monotonic() - start) * 1000

            logger.info(
                "[AI_SANDBOX] completed id=%s operation=%s duration_ms=%.1f",
                approval.id, op, duration_ms,
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
                approval.id, op, str(exc), duration_ms,
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
        """Decorator to add a custom operation to the sandbox registry."""
        return _register(operation)

    @staticmethod
    def registered_operations() -> list[str]:
        return list(_REGISTRY.keys())
