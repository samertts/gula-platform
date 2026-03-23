"""
AI Approval Workflow — GULA Platform
=====================================
Human-in-the-loop gate between AI suggestions and system execution.

Flow:
    ai_suggest(...)              → AISuggestion (UNTRUSTED, is_approved=False)
          ↓
    ApprovalStore.submit()       → PendingApproval (stored, awaits human)
          ↓
    Human: POST /api/ai/approve  → ApprovalStore.approve(id, approver)
          ↓
    AISandbox.execute(approval)  → runs the approved operation under audit

An AISuggestion that has not been explicitly approved CANNOT change state.
Approvals expire after TTL_SECONDS to prevent stale approvals being used later.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from app.ai.guardrails import AISuggestion, AIOperationType

logger = logging.getLogger("gula.ai.approval")

# Approvals expire after 30 minutes — prevents delayed misuse
TTL_SECONDS = 1800


class ApprovalStatus(str, Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED  = "expired"
    EXECUTED = "executed"


@dataclass
class PendingApproval:
    id:           str
    suggestion:   AISuggestion
    status:       ApprovalStatus = ApprovalStatus.PENDING
    submitted_at: float          = field(default_factory=time.time)
    reviewed_at:  Optional[float] = None
    reviewed_by:  Optional[str]   = None   # user email / id
    rejection_reason: str         = ""

    @property
    def is_expired(self) -> bool:
        return (
            self.status == ApprovalStatus.PENDING
            and time.time() - self.submitted_at > TTL_SECONDS
        )

    @property
    def is_executable(self) -> bool:
        return (
            self.status == ApprovalStatus.APPROVED
            and not self.is_expired
        )


class ApprovalStore:
    """
    In-memory store for pending AI approvals.

    In production, persist to the database via AuditLog or a dedicated table
    so approvals survive restarts and are fully auditable.
    """

    def __init__(self) -> None:
        self._store: Dict[str, PendingApproval] = {}

    def submit(self, suggestion: AISuggestion) -> PendingApproval:
        """
        Submit an AI suggestion for human review.
        DISPLAY_ONLY operations are auto-approved (they don't change state).
        """
        if suggestion.operation_type == AIOperationType.DISPLAY_ONLY:
            # Display-only: no approval needed, no state change possible
            approval = PendingApproval(
                id=str(uuid.uuid4()),
                suggestion=suggestion,
                status=ApprovalStatus.APPROVED,
                reviewed_at=time.time(),
                reviewed_by="system:display_only_auto",
            )
            logger.debug(
                "[AI_APPROVAL] auto-approved display_only id=%s operation=%s",
                approval.id, suggestion.operation,
            )
            return approval

        approval = PendingApproval(
            id=str(uuid.uuid4()),
            suggestion=suggestion,
        )
        self._store[approval.id] = approval

        logger.info(
            "[AI_APPROVAL] submitted id=%s operation=%s entity=%s/%s confidence=%.2f",
            approval.id,
            suggestion.operation,
            suggestion.entity_type or "—",
            suggestion.entity_id or "—",
            suggestion.confidence,
        )
        return approval

    def approve(self, approval_id: str, approver: str) -> PendingApproval:
        approval = self._get_or_raise(approval_id)

        if approval.is_expired:
            approval.status = ApprovalStatus.EXPIRED
            raise ValueError(f"Approval {approval_id} has expired")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Approval {approval_id} is not pending (status={approval.status.value})"
            )

        approval.status      = ApprovalStatus.APPROVED
        approval.reviewed_at = time.time()
        approval.reviewed_by = approver

        logger.info(
            "[AI_APPROVAL] approved id=%s operation=%s by=%s",
            approval_id, approval.suggestion.operation, approver,
        )
        return approval

    def reject(self, approval_id: str, approver: str, reason: str = "") -> PendingApproval:
        approval = self._get_or_raise(approval_id)

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Approval {approval_id} is not pending (status={approval.status.value})"
            )

        approval.status           = ApprovalStatus.REJECTED
        approval.reviewed_at      = time.time()
        approval.reviewed_by      = approver
        approval.rejection_reason = reason

        logger.info(
            "[AI_APPROVAL] rejected id=%s operation=%s by=%s reason=%r",
            approval_id, approval.suggestion.operation, approver, reason,
        )
        return approval

    def mark_executed(self, approval_id: str) -> None:
        approval = self._get_or_raise(approval_id)
        approval.status = ApprovalStatus.EXECUTED

    def get(self, approval_id: str) -> Optional[PendingApproval]:
        approval = self._store.get(approval_id)
        if approval and approval.is_expired:
            approval.status = ApprovalStatus.EXPIRED
        return approval

    def pending_list(self) -> list[PendingApproval]:
        result = []
        for a in self._store.values():
            if a.is_expired:
                a.status = ApprovalStatus.EXPIRED
            if a.status == ApprovalStatus.PENDING:
                result.append(a)
        return result

    def _get_or_raise(self, approval_id: str) -> PendingApproval:
        approval = self._store.get(approval_id)
        if approval is None:
            raise KeyError(f"Approval {approval_id!r} not found")
        return approval


# Module-level singleton (injected into routes)
approval_store = ApprovalStore()
