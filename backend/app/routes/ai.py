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

_SEVERITY_NORMAL   = "طبيعي"
_SEVERITY_WARNING  = "تنبيه"
_SEVERITY_CRITICAL = "حرج"

# Deviation ratio thresholds (fraction of the normal range width beyond the limit)
_WARN_RATIO     = 0.25   # >25% of range width outside limit → تنبيه
_CRITICAL_RATIO = 0.75   # >75% of range width outside limit → حرج


def _classify_severity(val_raw, low_raw, high_raw) -> str:
    """Return severity string for one result.  Falls back to تنبيه when range is missing."""
    try:
        vf   = float(val_raw)
        lf   = float(low_raw)
        hf   = float(high_raw)
        span = hf - lf
        if lf <= vf <= hf:
            return _SEVERITY_NORMAL
        deviation = (lf - vf) if vf < lf else (vf - hf)
        ratio = deviation / span if span > 0 else 1.0
        return _SEVERITY_CRITICAL if ratio >= _CRITICAL_RATIO else _SEVERITY_WARNING
    except (TypeError, ValueError):
        pass
    # Value outside range but no numeric range → warn
    return _SEVERITY_WARNING


def _compute_severities(results_data: list[dict]) -> list[dict]:
    """Return per-result severity enriched records."""
    enriched = []
    for r in results_data:
        val   = r.get("value") if r.get("value") is not None else r.get("value_text")
        low   = r.get("normal_range_low")
        high  = r.get("normal_range_high")
        if val is None:
            sev = _SEVERITY_NORMAL
        elif low is not None and high is not None:
            sev = _classify_severity(val, low, high)
        else:
            sev = _SEVERITY_NORMAL
        enriched.append({**r, "severity": sev})
    return enriched


def _overall_severity(enriched: list[dict]) -> str:
    sevs = {r["severity"] for r in enriched}
    if _SEVERITY_CRITICAL in sevs:
        return _SEVERITY_CRITICAL
    if _SEVERITY_WARNING in sevs:
        return _SEVERITY_WARNING
    return _SEVERITY_NORMAL


def _build_interpret_prompt(results_data: list[dict]) -> str:
    """
    Build a strict structured prompt that:
    1. Annotates each test with its severity tier
    2. Enforces numbered-list output format (one sentence per test)
    3. Forbids diagnosis, drug names, disease names, and speculation
    4. Requires a critical-alert line when حرج results exist
    5. Hard-caps at 200 words and mandates the disclaimer as the LAST line
    """
    enriched = _compute_severities(results_data)
    has_critical = any(r["severity"] == _SEVERITY_CRITICAL for r in enriched)

    lines: list[str] = []
    for r in enriched:
        name  = r.get("test_name", "")
        val   = r.get("value") if r.get("value") is not None else r.get("value_text", "-")
        unit  = r.get("unit", "") or ""
        low   = r.get("normal_range_low")
        high  = r.get("normal_range_high")
        sev   = r["severity"]
        range_str = f"المدى الطبيعي: {low}–{high} {unit}".strip() if (low is not None and high is not None) else unit
        lines.append(f"[{sev}] {name}: {val} {unit} — {range_str}")

    critical_instruction = (
        "\n- يوجد نتيجة واحدة أو أكثر مصنّفة [حرج]. "
        "ابدأ الرد بسطر تنبيه واضح: «⚠️ تنبيه: بعض النتائج تستوجب مراجعة طبية فورية.»"
        if has_critical else ""
    )

    return (
        "أنت مساعد توعوي طبي. مهمتك شرح نتائج التحاليل للمريض بأسلوب بسيط.\n\n"
        "النتائج:\n"
        + "\n".join(lines)
        + "\n\n"
        "قواعد صارمة — لا استثناء:\n"
        "1. اكتب بالعربية حصراً.\n"
        "2. اكتب جملة واحدة مرقّمة لكل تحليل (1. … 2. … إلخ).\n"
        "3. في كل جملة: اذكر اسم التحليل + هل هو طبيعي أو خارج المدى + توضيح بسيط لما يعنيه ذلك.\n"
        "4. محظور تماماً: ذكر أي دواء، أي مرض بالاسم، أي تشخيص، أي توصية علاجية.\n"
        "5. محظور تماماً: استخدام عبارات مثل «ربما»، «قد يكون»، «يُحتمل» خارج السياق الطبي المباشر.\n"
        "6. لا تخترع معلومات غير موجودة في البيانات أعلاه.\n"
        "7. الرد لا يتجاوز 200 كلمة.\n"
        + critical_instruction
        + "\n8. آخر سطر حرفياً: «هذا الشرح للتوعية فقط ولا يُغني عن استشارة الطبيب.»\n"
        "\nابدأ الآن:"
    )


async def _call_ai_provider(prompt: str) -> str:
    """Call the configured AI provider, retrying the fallback once on failure."""
    if _AI_PROVIDER == "gemini":
        return await _call_gemini_flash(prompt)
    return await _call_groq_llama(prompt)


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

    # ── Compute severity before hitting AI ───────────────────────────────────
    enriched      = _compute_severities(results_data)
    overall_sev   = _overall_severity(enriched)
    critical_flags = [
        r["test_name"]
        for r in enriched
        if r["severity"] == _SEVERITY_CRITICAL
    ]
    results_severity = [
        {"test": r["test_name"], "severity": r["severity"]}
        for r in enriched
    ]

    # ── Call free AI provider ─────────────────────────────────────────────────
    prompt = _build_interpret_prompt(results_data)
    try:
        text = await _call_ai_provider(prompt)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        logger.warning("AI provider %s: HTTP %s", _AI_PROVIDER, exc.response.status_code)
        raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")
    except Exception as exc:
        logger.error("AI interpret error: %s", exc)
        raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")

    # Safety gate: strip any stray diagnostic phrases the model might slip in
    _FORBIDDEN_PHRASES = ["تشخيص:", "العلاج:", "الدواء:", "يُنصح بتناول", "جرعة"]
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in text:
            logger.warning("AI response contained forbidden phrase '%s' — stripped", phrase)
            text = text.replace(phrase, "")

    # Ensure disclaimer is present (model sometimes omits it)
    _DISCLAIMER = "هذا الشرح للتوعية فقط ولا يُغني عن استشارة الطبيب."
    if _DISCLAIMER not in text:
        text = text.rstrip() + "\n" + _DISCLAIMER

    logger.info(
        "AI interpreted token=%.8s... provider=%s tests=%d severity=%s critical=%d",
        token, _AI_PROVIDER, len(results_data), overall_sev, len(critical_flags),
    )
    return JSONResponse({
        "interpretation":   text,
        "provider":         _AI_PROVIDER,
        "severity":         overall_sev,
        "critical_flags":   critical_flags,
        "results_severity": results_severity,
    })
