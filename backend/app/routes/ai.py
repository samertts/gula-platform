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
from app.models.audit_log import AuditLog
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
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

import json

_SEVERITY_NORMAL   = "طبيعي"
_SEVERITY_WARNING  = "تنبيه"
_SEVERITY_CRITICAL = "حرج"

# ── Clinical Weighting Table ──────────────────────────────────────────────────
# Tests where even small deviations carry high clinical risk get a weight > 1.
# The critical threshold is divided by this weight, so a 2.0-weight test
# triggers حرج at half the deviation ratio of a normal test.
#
# Format: lowercase substring match → weight
_TEST_WEIGHTS: dict[str, float] = {
    # Electrolytes — narrow therapeutic window, arrhythmia risk
    "potassium": 2.5, "k+": 2.5,
    "sodium": 2.0, "na+": 2.0,
    "calcium": 2.0, "ca2+": 2.0,
    "magnesium": 1.8,
    # Acid-base
    "ph": 2.5, "bicarbonate": 2.0, "hco3": 2.0,
    # Cardiac markers
    "troponin": 2.5, "bnp": 2.5, "nt-probnp": 2.5, "ck-mb": 2.0,
    # Glucose / Diabetes
    "glucose": 2.0, "blood sugar": 2.0, "سكر": 2.0, "hba1c": 1.8,
    # Coagulation
    "inr": 2.0, "pt": 1.8, "ptt": 1.8, "aptt": 1.8,
    # Renal
    "creatinine": 1.8, "كرياتينين": 1.8, "egfr": 2.0, "gfr": 2.0,
    "urea": 1.5, "bun": 1.5,
    # Hematology
    "hemoglobin": 1.5, "hgb": 1.5, "هيموغلوبين": 1.5,
    "platelets": 1.8, "plt": 1.8, "صفائح": 1.8, "wbc": 1.5,
    # Thyroid
    "tsh": 1.5, "t3": 1.3, "t4": 1.3,
    # Liver
    "alt": 1.3, "ast": 1.3, "bilirubin": 1.4, "albumin": 1.5,
}

# Baseline deviation ratio thresholds (before weight adjustment)
_BASE_WARN_RATIO     = 0.25
_BASE_CRITICAL_RATIO = 0.75


def _get_test_weight(test_name: str) -> float:
    """Return clinical weight for a test name via substring match. Default 1.0."""
    name_lower = (test_name or "").lower()
    best = 1.0
    for key, w in _TEST_WEIGHTS.items():
        if key in name_lower:
            best = max(best, w)
    return best


def _classify_severity(val_raw, low_raw, high_raw, weight: float = 1.0) -> str:
    """
    Return طبيعي / تنبيه / حرج for a single result.
    Clinical weight lowers the critical threshold proportionally.
    """
    try:
        vf   = float(val_raw)
        lf   = float(low_raw)
        hf   = float(high_raw)
        span = hf - lf
        if lf <= vf <= hf:
            return _SEVERITY_NORMAL
        deviation = (lf - vf) if vf < lf else (vf - hf)
        ratio = deviation / span if span > 0 else 1.0
        critical_threshold = _BASE_CRITICAL_RATIO / max(weight, 1.0)
        return _SEVERITY_CRITICAL if ratio >= critical_threshold else _SEVERITY_WARNING
    except (TypeError, ValueError):
        pass
    return _SEVERITY_WARNING


def _compute_severities(results_data: list[dict]) -> list[dict]:
    """Return per-result severity enriched records including clinical weight."""
    enriched = []
    for r in results_data:
        val    = r.get("value") if r.get("value") is not None else r.get("value_text")
        low    = r.get("normal_range_low")
        high   = r.get("normal_range_high")
        weight = _get_test_weight(r.get("test_name", ""))
        if val is None:
            sev = _SEVERITY_NORMAL
        elif low is not None and high is not None:
            sev = _classify_severity(val, low, high, weight)
        else:
            sev = _SEVERITY_NORMAL
        enriched.append({**r, "severity": sev, "weight": weight})
    return enriched


def _overall_severity(enriched: list[dict]) -> str:
    sevs = {r["severity"] for r in enriched}
    if _SEVERITY_CRITICAL in sevs:
        return _SEVERITY_CRITICAL
    if _SEVERITY_WARNING in sevs:
        return _SEVERITY_WARNING
    return _SEVERITY_NORMAL


def _action_guidance(overall_sev: str) -> dict:
    """Return a clear action instruction for the patient — no diagnosis, urgency only."""
    if overall_sev == _SEVERITY_CRITICAL:
        return {
            "ar":           "⚠️ راجع الطبيب فوراً — لا تتأخر في التواصل مع مزودك الصحي.",
            "urgency":      "immediate",
            "within_hours": 24,
        }
    if overall_sev == _SEVERITY_WARNING:
        return {
            "ar":           "📅 راجع طبيبك خلال أسبوع لمناقشة هذه النتائج.",
            "urgency":      "soon",
            "within_hours": 168,
        }
    return {
        "ar":           "✅ جميع نتائجك ضمن الحدود الطبيعية. استمر في المتابعة الدورية.",
        "urgency":      "routine",
        "within_hours": None,
    }


def _emit_critical_alert(
    db: Session,
    order_id: int,
    critical_tests: list[str],
    token_prefix: str,
) -> None:
    """
    Write a critical-result alert to audit_logs so lab staff can track it.
    Non-fatal — any failure is logged and swallowed.
    """
    if not critical_tests:
        return
    try:
        entry = AuditLog(
            user_id=None,
            user_role="system:ai",
            action="critical_result_alert",
            resource_type="lab_order",
            resource_id=order_id,
            details=json.dumps({
                "critical_tests": critical_tests,
                "token_prefix":   token_prefix,
                "source":         "ai_interpret",
            }, ensure_ascii=False),
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.error("[AI] Failed to write critical_result_alert audit entry: %s", exc)


def _build_interpret_prompt(
    results_data: list[dict],
    patient_context: Optional[dict] = None,
) -> str:
    """
    Build a strict structured prompt that:
    1. Includes patient age/gender for context-aware interpretation
    2. Annotates each test with severity + clinical weight
    3. Enforces numbered-list output format, one sentence per test
    4. Provides action guidance tier (immediate / soon / routine) to anchor output
    5. Forbids: diagnosis, drug names, disease names by name, speculation
    6. Requires critical-alert opening line when حرج results exist
    7. Hard-caps at 220 words; disclaimer must be the final line
    """
    enriched     = _compute_severities(results_data)
    has_critical = any(r["severity"] == _SEVERITY_CRITICAL for r in enriched)
    overall_sev  = _overall_severity(enriched)
    action       = _action_guidance(overall_sev)

    # ── Patient context block ─────────────────────────────────────────────────
    ctx_lines: list[str] = []
    if patient_context:
        if patient_context.get("age"):
            ctx_lines.append(f"عمر المريض: {patient_context['age']} سنة")
        if patient_context.get("gender"):
            gender_ar = "ذكر" if patient_context["gender"].upper() == "M" else "أنثى"
            ctx_lines.append(f"الجنس: {gender_ar}")
    context_block = ("سياق المريض:\n" + "\n".join(ctx_lines) + "\n\n") if ctx_lines else ""

    # ── Results block ─────────────────────────────────────────────────────────
    result_lines: list[str] = []
    for r in enriched:
        name      = r.get("test_name", "")
        val       = r.get("value") if r.get("value") is not None else r.get("value_text", "-")
        unit      = r.get("unit", "") or ""
        low       = r.get("normal_range_low")
        high      = r.get("normal_range_high")
        sev       = r["severity"]
        range_str = (
            f"المدى الطبيعي: {low}–{high} {unit}".strip()
            if (low is not None and high is not None) else unit
        )
        result_lines.append(f"[{sev}] {name}: {val} {unit} — {range_str}")

    # ── Dynamic instructions ──────────────────────────────────────────────────
    critical_rule = (
        "\n- ابدأ الرد بسطر: «⚠️ تنبيه: بعض النتائج تستوجب مراجعة طبية فورية.»"
        if has_critical else ""
    )
    action_rule = f"\n- أنهِ الرد بهذه الجملة حرفياً — التوجيه: «{action['ar']}»"

    return (
        "أنت مساعد توعوي طبي. مهمتك شرح نتائج التحاليل للمريض بأسلوب بسيط ومفهوم.\n\n"
        + context_block
        + "النتائج:\n"
        + "\n".join(result_lines)
        + "\n\n"
        "قواعد صارمة — لا استثناء:\n"
        "1. اكتب بالعربية حصراً.\n"
        "2. اكتب جملة واحدة مرقّمة لكل تحليل (1. … 2. … إلخ).\n"
        "3. في كل جملة: اسم التحليل + هل هو طبيعي أو خارج المدى + توضيح بسيط لما يعنيه.\n"
        "4. محظور تماماً: ذكر أي دواء بالاسم، أي مرض بالاسم، أي تشخيص، أي توصية علاجية.\n"
        "5. محظور تماماً: اختلاق معلومات غير موجودة في البيانات.\n"
        "6. لا تستخدم «ربما» أو «قد» إلا لتوصيف الشعور وليس للتشخيص.\n"
        "7. الرد لا يتجاوز 220 كلمة."
        + critical_rule
        + action_rule
        + "\n8. آخر سطر حرفياً: «هذا الشرح للتوعية فقط ولا يُغني عن استشارة الطبيب.»\n"
        "\nابدأ الآن:"
    )


async def _call_ai_provider(prompt: str) -> str:
    """Call the configured AI provider."""
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

    # ── Load results + patient context from DB ────────────────────────────────
    token_hash = sha256(token.encode()).hexdigest()
    db: Session = SessionLocal()
    patient_context: Optional[dict] = None
    order_id_for_alert: int = 0
    try:
        result = (
            db.query(LabResult).filter(LabResult.token_hash == token_hash).first()
            or db.query(LabResult).filter(LabResult.token == token).first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="نتيجة التحليل غير موجودة")
        if result.expires_at and result.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="انتهت صلاحية رابط النتيجة")

        order_id_for_alert = result.order_id
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

        # Load patient age/gender for context-aware prompt
        order = db.query(LabOrder).filter(LabOrder.id == result.order_id).first()
        if order and order.patient_id:
            patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
            if patient:
                age = None
                if patient.birth_date:
                    today = datetime.now(timezone.utc).date()
                    age = today.year - patient.birth_date.year - (
                        (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
                    )
                patient_context = {
                    "age":    age,
                    "gender": patient.gender,
                }
    finally:
        db.close()

    if not results_data:
        raise HTTPException(status_code=404, detail="لا توجد نتائج للتفسير")

    # ── Compute severity before hitting AI ───────────────────────────────────
    enriched         = _compute_severities(results_data)
    overall_sev      = _overall_severity(enriched)
    critical_flags   = [r["test_name"] for r in enriched if r["severity"] == _SEVERITY_CRITICAL]
    results_severity = [{"test": r["test_name"], "severity": r["severity"]} for r in enriched]
    action           = _action_guidance(overall_sev)

    # ── Write critical alert to audit log (non-fatal, async-safe) ────────────
    if critical_flags:
        db2: Session = SessionLocal()
        try:
            _emit_critical_alert(db2, order_id_for_alert, critical_flags, token[:8])
        finally:
            db2.close()

    # ── Call free AI provider ─────────────────────────────────────────────────
    prompt = _build_interpret_prompt(results_data, patient_context=patient_context)
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
        "action_guidance":  action,
    })
