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
  GET  /api/ai/critical-alerts          — recent حرج alerts for this lab (doctor+)

  GET  /api/ai/interpret/{token}        — plain-Arabic explanation for patients (public)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Callable, Dict, Optional

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

# Hard timeout budget for every external AI HTTP call.  Keeps p99 latency ≤6s
# and prevents a slow provider from blocking a gunicorn worker indefinitely.
_AI_BUDGET_S = float(os.getenv("AI_BUDGET_SECONDS", "6"))

# Ollama — completely free, runs locally on the server (no API key required).
# Install: curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2:3b
_OLLAMA_BASE_URL      = os.getenv("OLLAMA_BASE_URL",      "")
_OLLAMA_CLINICAL_MODEL = os.getenv("OLLAMA_CLINICAL_MODEL", "llama3.2:3b")
_OLLAMA_TIMEOUT        = float(os.getenv("OLLAMA_TIMEOUT",  str(_AI_BUDGET_S)))

# Auto-detect provider priority: Ollama (local/free) → Gemini → Groq → none
_AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "ollama" if _OLLAMA_BASE_URL else
    "gemini" if _GEMINI_KEY else
    "groq"   if _GROQ_KEY   else "none",
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


@router.get("/providers", summary="حالة مزودي الذكاء الاصطناعي")
async def list_ai_providers():
    """
    Return which AI providers are configured and their reachability status.
    Useful for operators to verify the fallback chain before going live.
    """
    statuses = []

    # Ollama — test by calling /api/tags (lightweight list-models endpoint)
    ollama_ok = False
    ollama_models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{_OLLAMA_BASE_URL}/api/tags")
            if r.status_code == 200:
                ollama_ok = True
                ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    statuses.append({
        "name":        "ollama",
        "type":        "local",
        "configured":  True,
        "reachable":   ollama_ok,
        "model":       _OLLAMA_CLINICAL_MODEL,
        "base_url":    _OLLAMA_BASE_URL,
        "available_models": ollama_models,
        "cost":        "free (local)",
    })

    # Gemini
    statuses.append({
        "name":       "gemini",
        "type":       "cloud",
        "configured": bool(_GEMINI_KEY),
        "reachable":  None,   # not probed (expensive to test)
        "model":      "gemini-2.0-flash",
        "cost":       "free tier (1500 req/day)",
    })

    # Groq
    statuses.append({
        "name":       "groq",
        "type":       "cloud",
        "configured": bool(_GROQ_KEY),
        "reachable":  None,
        "model":      "llama-3.1-8b-instant",
        "cost":       "free tier (30 req/min)",
    })

    active = next(
        (p["name"] for p in statuses if p.get("configured") and p.get("reachable") is not False),
        "none",
    )
    return {
        "providers":       statuses,
        "active_provider": active,
        "fallback_chain":  ["ollama", "gemini", "groq"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLINICAL INTERPRETATION LAYER — Patient-facing, public access
# Authentication: none — the result token is the proof of access.
# Rate limiting: nginx api_limit zone + in-process response cache.
# ══════════════════════════════════════════════════════════════════════════════

_SEVERITY_NORMAL   = "طبيعي"
_SEVERITY_WARNING  = "تنبيه"
_SEVERITY_CRITICAL = "حرج"

_DISCLAIMER = "هذا الشرح للتوعية فقط ولا يُغني عن استشارة الطبيب."

_FORBIDDEN_PHRASES = [
    "تشخيص:", "العلاج:", "الدواء:", "يُنصح بتناول", "جرعة",
    "diagnosis:", "treatment:", "medication:", "prescribe",
]

# ── In-process response cache (prevents AI cost explosion / token replay) ─────
_INTERPRET_CACHE: dict[str, tuple[dict, float]] = {}
_CACHE_TTL = 120  # seconds — same token served from cache


# ── Clinical Weighting Table ──────────────────────────────────────────────────
# The critical threshold is divided by this weight, so high-risk tests trigger
# حرج much sooner.  Format: lowercase substring → weight multiplier (default 1.0)
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
    # Thyroid / Liver
    "tsh": 1.5, "t3": 1.3, "t4": 1.3,
    "alt": 1.3, "ast": 1.3, "bilirubin": 1.4, "albumin": 1.5,
}
_BASE_CRITICAL_RATIO = 0.75  # fraction of range span beyond the limit → حرج

# ── Conflict-detection patterns ───────────────────────────────────────────────
# Each tuple: (pattern_id, keywords_a, keywords_b, Arabic message)
_CONFLICT_PATTERNS: list[tuple[str, list[str], list[str], str]] = [
    ("electrolyte_imbalance",
     ["sodium", "na+", "صوديوم"], ["potassium", "k+", "بوتاسيوم"],
     "اختلال في توازن الكهارل — يستوجب مراجعة طبية فورية"),
    ("glucose_hba1c_gap",
     ["glucose", "blood sugar", "سكر"], ["hba1c"],
     "تفاوت بين قراءتي السكر الآني والتراكمي"),
    ("liver_stress",
     ["alt"], ["ast"],
     "ارتفاع في إنزيمات الكبد"),
    ("renal_pattern",
     ["creatinine", "كرياتينين"], ["urea", "bun"],
     "مؤشرات وظائف كلوية تستوجب المتابعة"),
    ("anemia_pattern",
     ["hemoglobin", "hgb", "هيموغلوبين"], ["rbc", "red blood", "كريات حمراء"],
     "نمط يشير إلى احتمال فقر الدم"),
]


def _get_test_weight(test_name: str) -> float:
    name_lower = (test_name or "").lower()
    return max(
        (w for key, w in _TEST_WEIGHTS.items() if key in name_lower),
        default=1.0,
    )


def _classify_severity(val_raw, low_raw, high_raw, weight: float = 1.0) -> str:
    try:
        vf, lf, hf = float(val_raw), float(low_raw), float(high_raw)
        if lf <= vf <= hf:
            return _SEVERITY_NORMAL
        span = hf - lf
        deviation = (lf - vf) if vf < lf else (vf - hf)
        ratio = deviation / span if span > 0 else 1.0
        return _SEVERITY_CRITICAL if ratio >= _BASE_CRITICAL_RATIO / max(weight, 1.0) else _SEVERITY_WARNING
    except (TypeError, ValueError):
        return _SEVERITY_WARNING


def _compute_severities(results_data: list[dict]) -> list[dict]:
    enriched = []
    for r in results_data:
        val    = r.get("value") if r.get("value") is not None else r.get("value_text")
        low, high = r.get("normal_range_low"), r.get("normal_range_high")
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


def _detect_conflicts(enriched: list[dict]) -> list[str]:
    """Return Arabic conflict messages for co-abnormal test pairs."""
    # Build set of abnormal test name tokens for fast matching
    abnormal = {
        key
        for r in enriched if r["severity"] != _SEVERITY_NORMAL
        for key in _TEST_WEIGHTS if key in (r.get("test_name") or "").lower()
    }
    messages: list[str] = []
    for _pid, kw_a, kw_b, msg in _CONFLICT_PATTERNS:
        if any(k in abnormal for k in kw_a) and any(k in abnormal for k in kw_b):
            messages.append(msg)
    return messages


def _compute_confidence(
    enriched: list[dict],
    patient_context: Optional[dict],
    provider_used: str,
) -> dict:
    """
    Score 0.0–1.0 based on data completeness and result complexity.
    Returns {"score": float, "level": "high"|"medium"|"low"}.
    """
    score = 1.0
    total = len(enriched)
    if total:
        no_range = sum(
            1 for r in enriched
            if r.get("normal_range_low") is None or r.get("normal_range_high") is None
        )
        score -= min(0.30, no_range / total * 0.40)
    critical_count = sum(1 for r in enriched if r["severity"] == _SEVERITY_CRITICAL)
    score -= min(0.20, critical_count * 0.05)
    if not patient_context or not any(patient_context.values()):
        score -= 0.10
    if provider_used == "groq":
        score -= 0.05
    score = round(max(0.0, min(1.0, score)), 2)
    level = "high" if score >= 0.80 else "medium" if score >= 0.55 else "low"
    return {"score": score, "level": level}


def _action_guidance(overall_sev: str) -> dict:
    if overall_sev == _SEVERITY_CRITICAL:
        return {"ar": "⚠️ راجع الطبيب فوراً — لا تتأخر في التواصل مع مزودك الصحي.",
                "urgency": "immediate", "within_hours": 24}
    if overall_sev == _SEVERITY_WARNING:
        return {"ar": "📅 راجع طبيبك خلال أسبوع لمناقشة هذه النتائج.",
                "urgency": "soon", "within_hours": 168}
    return {"ar": "✅ جميع نتائجك ضمن الحدود الطبيعية. استمر في المتابعة الدورية.",
            "urgency": "routine", "within_hours": None}


def _emit_critical_alert(db: Session, order_id: int,
                          critical_tests: list[str], token_prefix: str) -> None:
    """Write a critical-result alert to audit_logs. Non-fatal."""
    try:
        db.add(AuditLog(
            user_id=None,
            user_role="system:ai",
            action="critical_result_alert",
            resource_type="lab_order",
            resource_id=order_id,
            details=json.dumps(
                {"critical_tests": critical_tests, "token_prefix": token_prefix,
                 "source": "ai_interpret"},
                ensure_ascii=False,
            ),
        ))
        db.commit()
    except Exception as exc:
        logger.error("[AI] critical_result_alert audit write failed: %s", exc)


def _build_interpret_prompt(
    results_data: list[dict],
    patient_context: Optional[dict] = None,
) -> str:
    enriched     = _compute_severities(results_data)
    has_critical = any(r["severity"] == _SEVERITY_CRITICAL for r in enriched)
    action       = _action_guidance(_overall_severity(enriched))

    ctx_lines = []
    if patient_context:
        if patient_context.get("age"):
            ctx_lines.append(f"عمر المريض: {patient_context['age']} سنة")
        if patient_context.get("gender"):
            ctx_lines.append("الجنس: " + ("ذكر" if str(patient_context["gender"]).upper() == "M" else "أنثى"))
    context_block = ("سياق المريض:\n" + "\n".join(ctx_lines) + "\n\n") if ctx_lines else ""

    result_lines = []
    for r in enriched:
        val  = r.get("value") if r.get("value") is not None else r.get("value_text", "-")
        unit = r.get("unit", "") or ""
        low, high = r.get("normal_range_low"), r.get("normal_range_high")
        range_str = (f"المدى الطبيعي: {low}–{high} {unit}".strip()
                     if (low is not None and high is not None) else unit)
        result_lines.append(f"[{r['severity']}] {r.get('test_name','')}: {val} {unit} — {range_str}")

    critical_rule = (
        "\n- ابدأ الرد بسطر: «⚠️ تنبيه: بعض النتائج تستوجب مراجعة طبية فورية.»"
        if has_critical else ""
    )
    return (
        "أنت مساعد توعوي طبي. مهمتك شرح نتائج التحاليل للمريض بأسلوب بسيط ومفهوم.\n\n"
        + context_block
        + "النتائج:\n" + "\n".join(result_lines) + "\n\n"
        "قواعد صارمة — لا استثناء:\n"
        "1. اكتب بالعربية حصراً.\n"
        "2. جملة واحدة مرقّمة لكل تحليل (1. … 2. … إلخ).\n"
        "3. في كل جملة: اسم التحليل + هل هو طبيعي أو خارج المدى + توضيح بسيط.\n"
        "4. محظور: أي دواء بالاسم، أي مرض بالاسم، أي تشخيص، أي توصية علاجية.\n"
        "5. محظور: اختلاق معلومات غير موجودة في البيانات.\n"
        "6. الرد لا يتجاوز 220 كلمة."
        + critical_rule
        + f"\n7. أنهِ الرد بهذه الجملة حرفياً: «{action['ar']}»"
        + f"\n8. آخر سطر حرفياً: «{_DISCLAIMER}»\n"
        "\nابدأ الآن:"
    )


async def _call_ollama_clinical(prompt: str) -> str:
    """
    Call local Ollama server for clinical interpretation.
    Uses /api/chat endpoint for better instruction-following than /api/generate.
    Raises httpx.HTTPError or RuntimeError on failure so the caller can fall back.
    """
    url = f"{_OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model":  _OLLAMA_CLINICAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":  False,
        "options": {"temperature": 0.3, "num_predict": 550},
    }
    async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    text = r.json().get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError("Ollama returned empty response")
    return text


async def _call_gemini_flash(prompt: str) -> str:
    url = _GEMINI_URL.format(key=_GEMINI_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
    }
    async with httpx.AsyncClient(timeout=_AI_BUDGET_S) as client:
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
    async with httpx.AsyncClient(timeout=_AI_BUDGET_S) as client:
        r = await client.post(
            _GROQ_URL, json=payload,
            headers={"Authorization": f"Bearer {_GROQ_KEY}"},
        )
        r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


async def _call_ai_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Try providers in priority order.  Returns (text, provider_name).

    Priority: Ollama (local/free, no limits) → Gemini (free tier) → Groq (free tier).
    Ollama is always attempted first when OLLAMA_BASE_URL is set (default).
    Cloud providers are used as fallback when Ollama is offline/unavailable.
    """
    providers: list[tuple[str, Callable]] = []
    # Ollama is always first — it's free, local, and has no rate limits
    providers.append(("ollama", _call_ollama_clinical))
    if _GEMINI_KEY:
        providers.append(("gemini", _call_gemini_flash))
    if _GROQ_KEY:
        providers.append(("groq", _call_groq_llama))

    last_exc: Exception = RuntimeError("no providers configured")
    for name, fn in providers:
        try:
            text = await fn(prompt)
            return text, name
        except Exception as exc:
            logger.warning("[AI] Provider %s failed: %s — trying fallback", name, exc)
            last_exc = exc
    logger.error("[AI] All providers failed: %s", last_exc)
    raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")


# ── Doctor-facing: critical alerts dashboard ──────────────────────────────────

@router.get("/critical-alerts", summary="نتائج حرجة — تنبيهات المختبر")
def list_critical_alerts(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return recent critical-result alerts for the current lab.
    Doctor+ only.  Sourced from audit_logs (action=critical_result_alert).
    """
    _require_doctor(current_user)
    lab_order_ids = db.query(LabOrder.id).filter(
        LabOrder.lab_id == current_user.lab_id
    ).subquery()
    rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "critical_result_alert",
            AuditLog.resource_id.in_(lab_order_ids),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for row in rows:
        try:
            details = json.loads(row.details or "{}")
        except Exception:
            details = {}
        items.append({
            "id":             row.id,
            "order_id":       row.resource_id,
            "critical_tests": details.get("critical_tests", []),
            "token_prefix":   details.get("token_prefix", ""),
            "created_at":     row.created_at.isoformat() if row.created_at else None,
        })
    return {"count": len(items), "alerts": items}


# ── Public interpret endpoint ─────────────────────────────────────────────────

@router.get(
    "/interpret/{token}",
    summary="تفسير نتائج التحليل للمريض (عام)",
    response_class=JSONResponse,
    tags=["AI Public"],
)
async def interpret_result_public(token: str) -> JSONResponse:
    """
    Plain-Arabic AI explanation for lab results identified by *token*.
    Public endpoint — no login required.
    Responses are cached 120 s per token to prevent cost explosion.
    """
    if not token or not re.match(r"^[A-Za-z0-9_-]{10,}$", token):
        raise HTTPException(status_code=400, detail="رمز النتيجة غير صالح")

    # ── In-process cache check ────────────────────────────────────────────────
    cache_key = sha256(token.encode()).hexdigest()[:16]
    cached = _INTERPRET_CACHE.get(cache_key)
    if cached and time.monotonic() < cached[1]:
        return JSONResponse({**cached[0], "cached": True})

    # ── Load results + patient context from DB ────────────────────────────────
    token_hash = sha256(token.encode()).hexdigest()
    db: Session = SessionLocal()
    patient_context: Optional[dict] = None
    order_id: int = 0
    results_data: list[dict] = []
    try:
        result = (
            db.query(LabResult).filter(LabResult.token_hash == token_hash).first()
            or db.query(LabResult).filter(LabResult.token == token).first()
        )
        if not result:
            raise HTTPException(status_code=404, detail="نتيجة التحليل غير موجودة")
        if result.expires_at and result.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="انتهت صلاحية رابط النتيجة")

        order_id = result.order_id
        results_data = [
            {
                "test_name":         r.test_name,
                "value":             r.value,
                "value_text":        getattr(r, "value_text", None),
                "unit":              r.unit,
                "normal_range_low":  r.normal_range_low,
                "normal_range_high": r.normal_range_high,
            }
            for r in db.query(LabResult).filter(LabResult.order_id == order_id).all()
        ]

        order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
        if order and order.patient_id:
            patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
            if patient:
                age = None
                if patient.birth_date:
                    today = datetime.now(timezone.utc).date()
                    age = today.year - patient.birth_date.year - (
                        (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
                    )
                patient_context = {"age": age, "gender": patient.gender}
    finally:
        db.close()

    if not results_data:
        raise HTTPException(status_code=404, detail="لا توجد نتائج للتفسير")

    # ── Severity, conflicts, action guidance ─────────────────────────────────
    enriched         = _compute_severities(results_data)
    overall_sev      = _overall_severity(enriched)
    critical_flags   = [r["test_name"] for r in enriched if r["severity"] == _SEVERITY_CRITICAL]
    results_severity = [{"test": r["test_name"], "severity": r["severity"]} for r in enriched]
    conflicts        = _detect_conflicts(enriched)
    action           = _action_guidance(overall_sev)

    # ── Audit: write critical alert (non-fatal) ───────────────────────────────
    if critical_flags:
        db2: Session = SessionLocal()
        try:
            _emit_critical_alert(db2, order_id, critical_flags, token[:8])
        finally:
            db2.close()

    # ── Call AI with automatic provider fallback ──────────────────────────────
    prompt = _build_interpret_prompt(results_data, patient_context=patient_context)
    text, provider_used = await _call_ai_with_fallback(prompt)

    # ── Post-generation safety gate ───────────────────────────────────────────
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in text:
            logger.warning("[AI] Stripped forbidden phrase: %r", phrase)
            text = text.replace(phrase, "")
    if _DISCLAIMER not in text:
        text = text.rstrip() + "\n" + _DISCLAIMER

    # ── Confidence score ──────────────────────────────────────────────────────
    confidence = _compute_confidence(enriched, patient_context, provider_used)

    logger.info(
        "[AI] interpreted token=%.8s provider=%s tests=%d severity=%s "
        "critical=%d confidence=%s conflicts=%d",
        token, provider_used, len(results_data), overall_sev,
        len(critical_flags), confidence["level"], len(conflicts),
    )

    payload = {
        "interpretation":   text,
        "provider":         provider_used,
        "severity":         overall_sev,
        "critical_flags":   critical_flags,
        "results_severity": results_severity,
        "conflicts":        conflicts,
        "confidence":       confidence,
        "action_guidance":  action,
    }
    _INTERPRET_CACHE[cache_key] = (payload, time.monotonic() + _CACHE_TTL)
    return JSONResponse(payload)


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI ASSISTANT CHAT — Frontend-facing conversational AI
# Authentication: JWT required (lab staff only).
# Safety: no clinical state changes — display-only by design.
# ══════════════════════════════════════════════════════════════════════════════

_ASSISTANT_SYSTEM_PROMPT = (
    "أنت مساعد ذكي لمنصة GULA للمختبرات الطبية. "
    "تساعد موظفي المختبر وأطباء المختبر على إدارة الطلبات والنتائج والمرضى. "
    "ردودك باللغة العربية ما لم يطلب المستخدم خلاف ذلك. "
    "أنت لا تُشخّص أمراضاً ولا تصف دواءً — هذا دور الطبيب المعالج. "
    "كن موجزاً ودقيقاً ومفيداً."
)

_CHAT_MAX_TOKENS = int(os.getenv("GEMINI_CHAT_MAX_TOKENS", "600"))
_CHAT_RATE_WINDOW: dict[str, tuple[int, float]] = {}  # user_id → (count, window_start)
_CHAT_RATE_LIMIT  = int(os.getenv("GEMINI_CHAT_RATE_LIMIT", "30"))   # req per 60s per user


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(default=None, max_length=500,
                                   description="Optional page context (e.g. 'orders page')")


async def _call_gemini_chat(system_prompt: str, user_message: str) -> str:
    """Call Gemini 2.0 Flash for the assistant chat endpoint."""
    if not _GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")
    url = _GEMINI_URL.format(key=_GEMINI_KEY)
    payload = {
        "contents": [
            {"role": "user", "parts": [
                {"text": f"{system_prompt}\n\n---\n{user_message}"}
            ]}
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": _CHAT_MAX_TOKENS,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_MEDICAL",           "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    }
    async with httpx.AsyncClient(timeout=_AI_BUDGET_S) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Gemini returned unexpected shape: {exc}") from exc


@router.post(
    "/chat",
    summary="مساعد GULA الذكي — محادثة",
    tags=["AI Assistant"],
)
async def ai_chat(
    body: ChatRequest,
    current_user=Depends(get_current_user),
):
    """
    Send a message to the GULA AI assistant (powered by Gemini 2.0 Flash).

    Responses are display-only and never mutate clinical data.
    Rate-limited to GEMINI_CHAT_RATE_LIMIT requests per 60 s per user.
    Falls back to a rule-based helper message if Gemini is unavailable.
    """
    # ── Per-user rate limit ───────────────────────────────────────────────────
    uid   = str(current_user.id)
    now   = time.monotonic()
    entry = _CHAT_RATE_WINDOW.get(uid, (0, now))
    count, window_start = entry
    if now - window_start > 60:
        count, window_start = 0, now
    count += 1
    _CHAT_RATE_WINDOW[uid] = (count, window_start)
    if count > _CHAT_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="تجاوزت حد الطلبات المسموح به. انتظر دقيقة وأعد المحاولة.",
        )

    # ── Build contextual system prompt ────────────────────────────────────────
    system = _ASSISTANT_SYSTEM_PROMPT
    if body.context:
        system += f"\nالصفحة الحالية: {body.context}"

    # ── Call Gemini with Ollama/Groq fallback ─────────────────────────────────
    provider_used = "gemini"
    try:
        reply = await _call_gemini_chat(system, body.message)
    except Exception as gemini_exc:
        logger.warning("[AI/chat] Gemini failed (%s), trying fallback", gemini_exc)
        # Fallback: try Ollama then Groq via the existing clinical pipeline
        try:
            combined = f"{system}\n\nسؤال المستخدم: {body.message}"
            reply, provider_used = await _call_ai_with_fallback(combined)
        except HTTPException:
            reply = (
                "عذراً، المساعد الذكي غير متاح حالياً. "
                "يرجى المحاولة لاحقاً أو التواصل مع الدعم الفني."
            )
            provider_used = "none"

    logger.info(
        "[AI/chat] user=%s provider=%s chars_in=%d chars_out=%d",
        current_user.id, provider_used, len(body.message), len(reply),
    )
    return {
        "reply":    reply,
        "provider": provider_used,
        "display_only": True,
    }
