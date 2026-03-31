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

  GET  /api/ai/interpret/{token}        — plain-Arabic explanation for patients (public)
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.approval import approval_store
from app.ai.guardrails import AIGuardrailViolation, ai_suggest
from app.ai.sandbox import AISandbox
from app.database import get_db, SessionLocal
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.ai")

# ── Free AI provider config ───────────────────────────────────────────────────
_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
_GROQ_KEY   = os.getenv("GROQ_API_KEY", "")
_AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "gemini" if _GEMINI_KEY else "groq" if _GROQ_KEY else "none",
)
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

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


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC — Patient-facing result interpretation
# No authentication required.  The result_token itself is the proof of access.
# Rate-limited by nginx (api_limit zone).
# ══════════════════════════════════════════════════════════════════════════════

def _build_interpret_prompt(results_data: list[dict]) -> str:
    lines: list[str] = []
    for r in results_data:
        name  = r.get("test_name", "")
        val   = r.get("value") if r.get("value") is not None else r.get("value_text", "-")
        unit  = r.get("unit", "")
        low   = r.get("normal_range_low")
        high  = r.get("normal_range_high")
        status = ""
        try:
            vf = float(val)
            if low is not None and high is not None:
                status = "(طبيعي)" if float(low) <= vf <= float(high) else (
                    "(منخفض)" if vf < float(low) else "(مرتفع)"
                )
        except (TypeError, ValueError):
            pass
        range_part = f" — المدى الطبيعي: {low}–{high} {unit}" if (low is not None and high is not None) else f" {unit}"
        lines.append(f"• {name}: {val} {unit} {status}{range_part}")

    return (
        "أنت مساعد طبي. اشرح نتائج التحاليل التالية للمريض بأسلوب بسيط وواضح:\n\n"
        + "\n".join(lines)
        + "\n\nتعليمات:\n"
        "- اكتب بالعربية فقط\n"
        "- جملة واحدة مختصرة لكل تحليل (طبيعي أو غير طبيعي وسببه المحتمل)\n"
        "- لا تذكر تشخيصاً أو دواءً محدداً\n"
        "- الرد لا يتجاوز 150 كلمة\n"
        "- انهِ بـ: «هذا الشرح للتوعية فقط ولا يُغني عن استشارة الطبيب.»"
    )


async def _call_gemini_flash(prompt: str) -> str:
    url = _GEMINI_URL.format(key=_GEMINI_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _call_groq_llama(prompt: str) -> str:
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            _GROQ_URL, json=payload,
            headers={"Authorization": f"Bearer {_GROQ_KEY}"},
        )
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


@router.get(
    "/interpret/{token}",
    summary="تفسير نتائج التحليل للمريض (عام)",
    response_class=JSONResponse,
    tags=["AI Public"],
)
async def interpret_result_public(token: str) -> JSONResponse:
    """
    Return a plain-Arabic AI explanation of the lab results identified by
    *token*.  Public endpoint — no login required.

    Returns 503 when no AI provider is configured (set GEMINI_API_KEY or
    GROQ_API_KEY in the environment to enable).
    """
    if _AI_PROVIDER == "none":
        raise HTTPException(
            status_code=503,
            detail="تفسير الذكاء الاصطناعي غير مفعل حالياً.",
        )

    if not token or not re.match(r"^[A-Za-z0-9_-]{10,}$", token):
        raise HTTPException(status_code=400, detail="رمز النتيجة غير صالح")

    # ── Load results from DB (same auth model as /api/r/{token}) ─────────────
    token_hash = sha256(token.encode()).hexdigest()
    db: Session = SessionLocal()
    try:
        result = (
            db.query(LabResult).filter(LabResult.token_hash == token_hash).first()
            or db.query(LabResult).filter(LabResult.token == token).first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="نتيجة التحليل غير موجودة")
        if result.expires_at and result.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="انتهت صلاحية رابط النتيجة")

        all_results = db.query(LabResult).filter(
            LabResult.order_id == result.order_id
        ).all()
        results_data = [
            {
                "test_name":         r.test_name,
                "value":             r.value,
                "value_text":        getattr(r, "value_text", None),
                "unit":              r.unit,
                "normal_range_low":  r.normal_range_low,
                "normal_range_high": r.normal_range_high,
            }
            for r in all_results
        ]
    finally:
        db.close()

    if not results_data:
        raise HTTPException(status_code=404, detail="لا توجد نتائج للتفسير")

    # ── Call free AI provider ─────────────────────────────────────────────────
    prompt = _build_interpret_prompt(results_data)
    try:
        if _AI_PROVIDER == "gemini":
            text = await _call_gemini_flash(prompt)
        else:
            text = await _call_groq_llama(prompt)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        logger.warning("AI provider %s: HTTP %s", _AI_PROVIDER, exc.response.status_code)
        raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")
    except Exception as exc:
        logger.error("AI interpret error: %s", exc)
        raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")

    logger.info("AI interpreted token=%.8s... provider=%s tests=%d", token, _AI_PROVIDER, len(results_data))
    return JSONResponse({"interpretation": text, "provider": _AI_PROVIDER})
