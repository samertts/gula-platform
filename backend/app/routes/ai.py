"""
AI Suggestion & Approval Routes — GULA Platform
================================================
Human-in-the-loop approval workflow for AI suggestions.

Rules:
  - Any authenticated user may create a suggestion.
  - Only doctors and above may approve, reject, or execute.
  - Execution is sandboxed — only whitelisted read-only operations run.
  - Clinical state is NEVER changed by AI directly.

Routes:
  POST /api/ai/suggest                  — create a suggestion
  GET  /api/ai/pending                  — list pending approvals (doctor+)
  POST /api/ai/approve/{id}             — approve (doctor+)
  POST /api/ai/reject/{id}              — reject with reason (doctor+)
  POST /api/ai/execute/{id}             — run in sandbox (doctor+)
  POST /api/ai/analyze-order/{order_id} — analyze all results in an order (doctor+)
  GET  /api/ai/operations               — list whitelisted sandbox ops
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.approval import approval_store
from app.ai.guardrails import AIGuardrailViolation, ai_suggest
from app.ai.sandbox import AISandbox
from app.database import get_db
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/ai", tags=["AI Safety Layer"])

_DOCTOR_ROLES = {"doctor", "admin", "lab_admin", "province_admin",
                 "ministry_admin", "master_admin"}


def _require_doctor(user) -> None:
    if user.role not in _DOCTOR_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only doctors and administrators may review AI suggestions.",
        )


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SuggestRequest(BaseModel):
    operation:   str             = Field(..., description="e.g. suggest_interpretation")
    payload:     Dict[str, Any]  = Field(default_factory=dict)
    entity_type: str             = Field(default="")
    entity_id:   Optional[int]   = Field(default=None)
    confidence:  float           = Field(default=0.5, ge=0.0, le=1.0)
    rationale:   str             = Field(default="")


class RejectRequest(BaseModel):
    reason: str = Field(default="")


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/suggest")
def create_suggestion(
    body: SuggestRequest,
    current_user=Depends(get_current_user),
):
    """
    Create an AI suggestion. DISPLAY_ONLY suggestions are immediately usable.
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
        "suggestion_id":     suggestion.id,
        "approval_id":       approval.id,
        "operation":         suggestion.operation,
        "operation_type":    suggestion.operation_type.value,
        "status":            approval.status.value,
        "requires_approval": approval.status.value == "pending",
    }


@router.get("/pending")
def list_pending(current_user=Depends(get_current_user)):
    """List all pending AI approvals."""
    _require_doctor(current_user)
    pending = approval_store.pending_list()
    now = time.time()
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
                "expires_in_s":   max(0, 1800 - (now - a.submitted_at)),
            }
            for a in pending
        ],
    }


@router.post("/approve/{approval_id}")
def approve_suggestion(
    approval_id: str,
    current_user=Depends(get_current_user),
):
    """Approve an AI suggestion."""
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
    body: RejectRequest,
    current_user=Depends(get_current_user),
):
    """Reject an AI suggestion with an optional reason."""
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
    Execute an approved suggestion inside the sandbox.
    Output is always display-only — never mutates clinical state.
    """
    _require_doctor(current_user)
    approval = approval_store.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    if not approval.is_executable:
        raise HTTPException(
            status_code=400,
            detail=f"Not executable (status={approval.status.value})",
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


@router.post("/analyze-order/{order_id}")
def analyze_order(
    order_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run clinical pattern analysis on all results in an order.
    Creates an AI suggestion with the detected patterns.
    The suggestion is DISPLAY_ONLY — it does not change the order state.

    Doctors use the output to inform their clinical review, not to replace it.
    """
    _require_doctor(current_user)

    # Load the order, scoped to the user's lab
    order = db.query(LabOrder).filter(
        LabOrder.id == order_id,
        LabOrder.lab_id == current_user.lab_id,
    ).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    results = db.query(LabResult).filter(LabResult.order_id == order_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="No results found for this order")

    result_list = [
        {
            "test_name":       r.test_name,
            "value":           r.value,
            "unit":            r.unit,
            "normal_range_low":  r.normal_range_low,
            "normal_range_high": r.normal_range_high,
        }
        for r in results
    ]

    try:
        suggestion = ai_suggest(
            operation="analyze_order",
            payload={
                "order_id":    order_id,
                "result_list": result_list,
            },
            ai_model="clinical_intelligence_engine",
            confidence=1.0,   # rules-based, deterministic
            rationale="Multi-test clinical pattern analysis (rules-based, not ML)",
            entity_type="order",
            entity_id=order_id,
        )
    except AIGuardrailViolation as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    approval = approval_store.submit(suggestion)

    # Auto-execute since analyze_order is display-only
    if approval.is_executable:
        result = AISandbox.execute(approval)
        return {
            "order_id":       order_id,
            "approval_id":    approval.id,
            "status":         approval.status.value,
            "patterns_found": len(result.output.get("patterns", [])),
            "flag_summary":   result.output.get("flag_summary", {}),
            "patterns":       result.output.get("patterns", []),
            "interpretations": result.output.get("interpretations", []),
            "display_only":   True,
            "disclaimer":     "This analysis is for physician review only. It does not constitute a diagnosis.",
            "disclaimer_ar":  "هذا التحليل للمراجعة الطبية فقط. لا يُشكّل تشخيصاً طبياً.",
        }

    return {
        "order_id":    order_id,
        "approval_id": approval.id,
        "status":      approval.status.value,
        "message":     "Analysis pending approval",
    }


@router.get("/operations")
def list_operations():
    """List all sandbox-whitelisted operations."""
    return {
        "whitelisted_operations": AISandbox.registered_operations(),
        "note": "Only these operations can be executed by AI after human approval.",
    }
