"""
AI Suggestion & Approval Routes — GULA Platform
================================================
Exposes the human-in-the-loop approval workflow for AI suggestions.

All AI operations require an authenticated user with at least 'doctor' role
to approve or reject. Execution is sandboxed — only whitelisted operations run.

Routes:
  POST /api/ai/suggest          — create an AI suggestion (staff+)
  GET  /api/ai/pending          — list pending approvals (doctor+)
  POST /api/ai/approve/{id}     — approve a suggestion (doctor+)
  POST /api/ai/reject/{id}      — reject a suggestion (doctor+)
  POST /api/ai/execute/{id}     — execute an approved suggestion (doctor+)
  GET  /api/ai/operations       — list whitelisted sandbox operations
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from app.ai.approval import approval_store
from app.ai.guardrails import AIGuardrailViolation, ai_suggest
from app.ai.sandbox import AISandbox
from app.database import get_db
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI Safety Layer"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SuggestRequest(BaseModel):
    operation:   str                  = Field(..., description="e.g. suggest_interpretation")
    payload:     Dict[str, Any]       = Field(default_factory=dict)
    entity_type: str                  = Field(default="")
    entity_id:   Optional[int]        = Field(default=None)
    confidence:  float                = Field(default=0.5, ge=0.0, le=1.0)
    rationale:   str                  = Field(default="")


class ReviewRequest(BaseModel):
    reason: str = Field(default="", description="Required for rejection")


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/suggest")
def create_suggestion(
    body: SuggestRequest,
    current_user=Depends(get_current_user),
):
    """
    Create an AI suggestion. Returns the suggestion ID and its type.
    DISPLAY_ONLY suggestions are auto-approved and can be used immediately.
    SUGGESTION type requires human approval before execution.
    """
    try:
        suggestion = ai_suggest(
            operation=body.operation,
            payload=body.payload,
            ai_model=f"user:{current_user.email}",
            confidence=body.confidence,
            rationale=body.rationale,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
        )
    except AIGuardrailViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    approval = approval_store.submit(suggestion)

    return {
        "suggestion_id":  suggestion.id,
        "approval_id":    approval.id,
        "operation":      suggestion.operation,
        "operation_type": suggestion.operation_type.value,
        "status":         approval.status.value,
        "requires_approval": approval.status.value == "pending",
    }


@router.get("/pending")
def list_pending(current_user=Depends(get_current_user)):
    """List all pending AI approvals for this platform."""
    _require_doctor(current_user)
    pending = approval_store.pending_list()
    return {
        "count": len(pending),
        "items": [
            {
                "approval_id":    a.id,
                "operation":      a.suggestion.operation,
                "operation_type": a.suggestion.operation_type.value,
                "entity_type":    a.suggestion.entity_type,
                "entity_id":      a.suggestion.entity_id,
                "confidence":     a.suggestion.confidence,
                "rationale":      a.suggestion.rationale,
                "submitted_at":   a.submitted_at,
                "expires_in_s":   max(0, 1800 - (import_time() - a.submitted_at)),
            }
            for a in pending
        ],
    }


@router.post("/approve/{approval_id}")
def approve_suggestion(
    approval_id: str,
    current_user=Depends(get_current_user),
):
    """Approve an AI suggestion. Only doctors and above may approve."""
    _require_doctor(current_user)
    try:
        approval = approval_store.approve(approval_id, approver=current_user.email)
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "approval_id": approval.id,
        "status":      approval.status.value,
        "approved_by": approval.reviewed_by,
    }


@router.post("/reject/{approval_id}")
def reject_suggestion(
    approval_id: str,
    body: ReviewRequest,
    current_user=Depends(get_current_user),
):
    """Reject an AI suggestion."""
    _require_doctor(current_user)
    try:
        approval = approval_store.reject(
            approval_id,
            approver=current_user.email,
            reason=body.reason,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "approval_id": approval.id,
        "status":      approval.status.value,
        "rejected_by": approval.reviewed_by,
        "reason":      approval.rejection_reason,
    }


@router.post("/execute/{approval_id}")
def execute_suggestion(
    approval_id: str,
    current_user=Depends(get_current_user),
):
    """
    Execute an approved AI suggestion inside the sandbox.
    Returns the sandboxed output — never changes clinical state directly.
    """
    _require_doctor(current_user)

    approval = approval_store.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")

    if not approval.is_executable:
        raise HTTPException(
            status_code=400,
            detail=f"Approval is not executable (status={approval.status.value})",
        )

    try:
        result = AISandbox.execute(approval)
    except AIGuardrailViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return {
        "approval_id": result.approval_id,
        "operation":   result.operation,
        "success":     result.success,
        "output":      result.output,
        "duration_ms": round(result.duration_ms, 1),
        "error":       result.error or None,
    }


@router.get("/operations")
def list_operations():
    """List all operations the AI sandbox is allowed to execute."""
    return {
        "whitelisted_operations": AISandbox.registered_operations(),
        "note": "Only these operations can be executed by AI after human approval.",
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _require_doctor(user) -> None:
    allowed_roles = {"doctor", "admin", "lab_admin", "province_admin",
                     "ministry_admin", "master_admin"}
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Only doctors and administrators may review AI suggestions.",
        )


def import_time() -> float:
    import time
    return time.time()
