"""AI Guardrails — GULA Platform
==============================
Enforces the fundamental rule of clinical AI safety:

    AI = Suggest
    Human = Approve
    System = Enforce

Every AI output passes through this module before it can influence the system.
An AI suggestion that has not been explicitly approved by a human operator
CANNOT change any clinical state.

Architecture:

    AI Model (external or local)
          ↓
    AISuggestion (immutable, typed, trust=UNTRUSTED)
          ↓
    Guardrail checks (operation allowed? payload safe?)
          ↓
    ApprovalStore.submit() → PendingApproval (awaits human)
          ↓
    Human approves via /api/ai/approve/{id}
          ↓
    AISandbox.execute() → allowed operation runs under audit

Nothing in this module ever writes to the database or changes application state.
It only produces structured, auditable suggestion objects.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum

logger = logging.getLogger("gula.ai.guardrails")


# ─── AI Operation Classification ─────────────────────────────────────────────


class AIOperationType(StrEnum):
    """Every AI action must be classified before it can be submitted for approval.

    DISPLAY_ONLY  — shown to the user, never stored or acted upon.
    ENRICHMENT    — adds non-critical context (e.g., translate, summarize).
    SUGGESTION    — proposes a change; requires human approval before execution.
    BLOCKED       — cannot be performed by AI under any circumstance.
    """

    DISPLAY_ONLY = "display_only"
    ENRICHMENT = "enrichment"
    SUGGESTION = "suggestion"
    BLOCKED = "blocked"


# Operations that AI may NEVER perform, regardless of approval
_ABSOLUTELY_BLOCKED: set[str] = {
    "validate_order",  # clinical sign-off
    "cancel_order",  # destructive workflow change
    "modify_result",  # changing a lab result value
    "delete_patient",  # data destruction
    "create_lab_user",  # privilege escalation via AI
    "change_role",  # RBAC manipulation
    "approve_result",  # doctor responsibility
    "write_audit_log",  # audit integrity
    "export_patient_data",  # privacy
    "send_critical_alert",  # must be triggered by verified clinical logic only
}

# Operations AI may suggest (still require human approval)
_SUGGESTABLE: set[str] = {
    "suggest_interpretation",  # text interpretation of a single result
    "analyze_order",  # multi-test clinical pattern analysis (rules-based)
    "suggest_normal_range",  # proposed reference range update
    "flag_anomaly",  # flag for human review
    "suggest_reorder",  # suggest re-running a test
    "summarize_history",  # patient history summary (display only)
    "translate_report",  # bilingual translation
}


class AIGuardrailViolation(RuntimeError):
    """Raised when AI attempts a blocked operation.
    This must never be silently caught — it indicates a design violation.
    """


# Backward-compatible alias
AIGuardrailViolationError = AIGuardrailViolation


# ─── AI Suggestion ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AISuggestion:
    """An immutable record of what an AI model proposed.

    This object is always in UNTRUSTED state until a human approves it.
    It CANNOT be executed directly — it must go through ApprovalStore.submit().
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str = ""
    operation_type: AIOperationType = AIOperationType.BLOCKED
    payload: dict[str, Any] = field(default_factory=dict)
    ai_model: str = "unknown"
    confidence: float = 0.0  # 0.0–1.0
    rationale: str = ""  # AI's explanation (display only)
    entity_type: str = ""  # e.g. "order", "result", "patient"
    entity_id: int | None = None
    created_at: float = field(default_factory=time.time)
    is_approved: bool = False  # always False at creation

    def __post_init__(self) -> None:
        if self.operation in _ABSOLUTELY_BLOCKED:
            raise AIGuardrailViolation(
                f"AI attempted blocked operation: '{self.operation}'. "
                "This operation can only be performed by authenticated human users.",
            )
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")


def ai_suggest(
    operation: str,
    payload: dict[str, Any],
    *,
    ai_model: str = "internal",
    confidence: float = 0.0,
    rationale: str = "",
    entity_type: str = "",
    entity_id: int | None = None,
) -> AISuggestion:
    """Create an AI suggestion. This is the ONLY way to produce an AISuggestion.

    Raises AIGuardrailViolation if the operation is absolutely blocked.
    """
    if operation in _ABSOLUTELY_BLOCKED:
        logger.error(
            "[AI_GUARDRAIL] BLOCKED operation=%s model=%s entity=%s/%s",
            operation,
            ai_model,
            entity_type,
            entity_id,
        )
        raise AIGuardrailViolation(f"Operation '{operation}' is permanently blocked for AI.")

    op_type = (
        AIOperationType.SUGGESTION if operation in _SUGGESTABLE else AIOperationType.DISPLAY_ONLY
    )

    suggestion = AISuggestion(
        operation=operation,
        operation_type=op_type,
        payload=payload,
        ai_model=ai_model,
        confidence=confidence,
        rationale=rationale,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    logger.info(
        "[AI_SUGGESTION] id=%s operation=%s type=%s model=%s confidence=%.2f entity=%s/%s",
        suggestion.id,
        suggestion.operation,
        suggestion.operation_type.value,
        suggestion.ai_model,
        suggestion.confidence,
        suggestion.entity_type or "—",
        suggestion.entity_id or "—",
    )

    return suggestion
