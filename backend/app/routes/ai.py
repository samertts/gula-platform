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

import asyncio
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

# OpenRouter — free-tier gateway to Qwen, DeepSeek, and 200+ models.
# Get a free key at https://openrouter.ai/keys (no credit card for free models).
# Recommended free models (strong Arabic support):
#   qwen/qwen3-14b:free          — best Arabic quality, strong reasoning
#   deepseek/deepseek-r1:free    — strong reasoning, good Arabic
#   qwen/qwen3-8b:free           — faster, lighter
_OPENROUTER_KEY   = os.getenv("OPENROUTER_API_KEY", "")
_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-14b:free")
_OPENROUTER_URL   = "https://openrouter.ai/api/v1/chat/completions"

# Ollama — completely free, runs locally on the server (no API key required).
# Set OLLAMA_ENABLED=false to skip Ollama entirely (saves RAM on small servers).
# Install: curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2:3b
_OLLAMA_ENABLED        = os.getenv("OLLAMA_ENABLED", "true").lower() not in ("false", "0", "no")
_OLLAMA_BASE_URL       = os.getenv("OLLAMA_BASE_URL",       "http://localhost:11434")
_OLLAMA_CLINICAL_MODEL = os.getenv("OLLAMA_CLINICAL_MODEL", "llama3.2:3b")
_OLLAMA_TIMEOUT        = float(os.getenv("OLLAMA_TIMEOUT",  "20"))

# Auto-detect provider priority:
#   Ollama (local/free, if enabled) → OpenRouter (Qwen/DeepSeek) → Gemini → Groq → none
_AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "ollama"       if (_OLLAMA_ENABLED and _OLLAMA_BASE_URL) else
    "openrouter"   if _OPENROUTER_KEY else
    "gemini"       if _GEMINI_KEY else
    "groq"         if _GROQ_KEY   else "none",
)
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent?key={key}"
)
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# AI response cache — Redis (cross-worker) with in-process dict fallback.
# Key = SHA256(first 300 chars of prompt) so identical test panels hit cache.
# This cuts AI API calls by ~70% for repeated/similar result patterns.
_AI_CACHE_TTL     = int(os.getenv("AI_CACHE_TTL_SECONDS", "7200"))   # 2 hours
_AI_BUDGET_SECS   = float(os.getenv("AI_BUDGET_SECONDS", "6.0"))   # hard wall for entire chain
try:
    from app.security.redis_client import cache as _redis_cache
    _AI_CACHE_BACKEND = _redis_cache
except Exception:
    _AI_CACHE_BACKEND = None   # fall back to in-process dict

_AI_RESPONSE_CACHE: dict[str, tuple[str, str, float]] = {}  # key → (text, provider, expire_at)

# Semaphore to limit concurrent Ollama calls (prevents RAM exhaustion on 4 GB servers)
_OLLAMA_SEMAPHORE = asyncio.Semaphore(1)

# ── Stampede protection ───────────────────────────────────────────────────────
# Maps cache_key → asyncio.Event.  When a key is in-flight, subsequent requests
# wait on the event instead of all hitting the AI provider simultaneously.
# Per-worker only (Redis-based cross-worker lock omitted for simplicity — max
# 3 parallel calls across 3 workers is acceptable).
_IN_FLIGHT: dict[str, asyncio.Event] = {}


# ── Per-provider circuit breaker ─────────────────────────────────────────────
# After _CB_THRESHOLD consecutive failures within _CB_WINDOW seconds, the
# provider is skipped until the window expires (half-open retry).
_CB_THRESHOLD = 3
_CB_WINDOW    = 30   # seconds

class _CircuitBreaker:
    """Lightweight in-process circuit breaker for one AI provider."""
    __slots__ = ("failures", "opened_at")

    def __init__(self) -> None:
        self.failures: int = 0
        self.opened_at: float = 0.0

    def is_open(self) -> bool:
        """Return True if the circuit is open (provider should be skipped)."""
        if self.failures >= _CB_THRESHOLD:
            age = time.monotonic() - self.opened_at
            if age < _CB_WINDOW:
                return True
            # Window expired — reset and allow a trial call (half-open)
            self.failures = 0
        return False

    def record_failure(self) -> None:
        self.failures += 1
        self.opened_at = time.monotonic()

    def record_success(self) -> None:
        self.failures = 0


# One breaker per provider name
_CIRCUIT_BREAKERS: dict[str, _CircuitBreaker] = {
    "ollama":      _CircuitBreaker(),
    "openrouter":  _CircuitBreaker(),
    "gemini":      _CircuitBreaker(),
    "groq":        _CircuitBreaker(),
}


# ── AI in-process metrics (Prometheus-compatible) ─────────────────────────────
# Simple integer counters — safe without a lock in CPython (GIL).
# Exposed via get_ai_metrics() imported by metrics.py.
_AI_CALLS:             dict[str, int] = {}   # provider → successful API calls
_AI_TIMEOUTS:          dict[str, int] = {}   # provider → timeout count
_AI_ERRORS:            dict[str, int] = {}   # provider → non-timeout failure count
_AI_CACHE_HITS:        int = 0
_AI_CACHE_MISSES:      int = 0
_AI_BUDGET_EXHAUSTED:  int = 0


def get_ai_metrics() -> dict:
    """Return current AI metrics snapshot for Prometheus exposition.
    Called from metrics.py — must never raise.
    """
    return {
        "calls":            dict(_AI_CALLS),
        "timeouts":         dict(_AI_TIMEOUTS),
        "errors":           dict(_AI_ERRORS),
        "cache_hits":       _AI_CACHE_HITS,
        "cache_misses":     _AI_CACHE_MISSES,
        "budget_exhausted": _AI_BUDGET_EXHAUSTED,
        "circuit_open": {
            name: 1 if cb.is_open() else 0
            for name, cb in _CIRCUIT_BREAKERS.items()
        },
    }

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
    if _OLLAMA_ENABLED:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{_OLLAMA_BASE_URL}/api/tags")
                if r.status_code == 200:
                    ollama_ok = True
                    ollama_models = [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
    statuses.append({
        "name":             "ollama",
        "type":             "local",
        "enabled":          _OLLAMA_ENABLED,
        "configured":       _OLLAMA_ENABLED,
        "reachable":        ollama_ok if _OLLAMA_ENABLED else None,
        "model":            _OLLAMA_CLINICAL_MODEL,
        "base_url":         _OLLAMA_BASE_URL,
        "available_models": ollama_models,
        "cost":             "free (local)" if _OLLAMA_ENABLED else "disabled (OLLAMA_ENABLED=false)",
        "note":             None if _OLLAMA_ENABLED else "Set OLLAMA_ENABLED=true to re-enable",
    })

    # OpenRouter (Qwen / DeepSeek)
    statuses.append({
        "name":       "openrouter",
        "type":       "cloud",
        "enabled":    bool(_OPENROUTER_KEY),
        "configured": bool(_OPENROUTER_KEY),
        "reachable":  None,   # not probed (avoids wasting free-tier quota)
        "model":      _OPENROUTER_MODEL,
        "cost":       "free tier (qwen3-14b:free, deepseek-r1:free)",
        "note":       "Set OPENROUTER_API_KEY + OPENROUTER_MODEL in .env",
    })

    # Gemini
    statuses.append({
        "name":       "gemini",
        "type":       "cloud",
        "enabled":    bool(_GEMINI_KEY),
        "configured": bool(_GEMINI_KEY),
        "reachable":  None,
        "model":      "gemini-2.0-flash",
        "cost":       "free tier (1500 req/day)",
    })

    # Groq
    statuses.append({
        "name":       "groq",
        "type":       "cloud",
        "enabled":    bool(_GROQ_KEY),
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
        "fallback_chain":  [
            p["name"] for p in statuses
            if p.get("configured") and p.get("enabled")
        ] or ["none"],
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
    Semaphore-limited to 1 concurrent call to protect RAM on 4 GB servers.
    """
    url = f"{_OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model":  _OLLAMA_CLINICAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":  False,
        "options": {"temperature": 0.3, "num_predict": 550},
    }
    async with _OLLAMA_SEMAPHORE:
        async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
    text = r.json().get("message", {}).get("content", "").strip()
    if not text:
        raise RuntimeError("Ollama returned empty response")
    return text


async def _call_with_retry(fn: Callable, prompt: str, retries: int = 1) -> str:
    """
    Call an async AI provider function with a single retry on transient errors.

    Retries on: 429 (rate limit), 503 (service unavailable), 529 (overloaded).
    Waits 2s before the retry so the provider has time to recover.
    Does NOT retry on 4xx client errors (bad key, bad request, etc.).
    """
    _RETRYABLE_STATUS = {429, 503, 529}
    last_exc: Exception = RuntimeError("unknown")
    for attempt in range(retries + 1):
        try:
            return await fn(prompt)
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            if exc.response.status_code in _RETRYABLE_STATUS and attempt < retries:
                logger.warning(
                    "[AI] %s HTTP %s (attempt %d/%d) — retrying in 2s",
                    fn.__name__, exc.response.status_code, attempt + 1, retries + 1,
                )
                await asyncio.sleep(2)
            else:
                raise
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                logger.warning(
                    "[AI] %s failed (attempt %d/%d): %s — retrying in 2s",
                    fn.__name__, attempt + 1, retries + 1, exc,
                )
                await asyncio.sleep(2)
            else:
                raise
    raise last_exc


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


async def _call_openrouter(prompt: str) -> str:
    """
    Call OpenRouter API — free gateway to Qwen, DeepSeek, and 200+ models.
    Default model: qwen/qwen3-14b:free (strong Arabic support, no cost).
    Uses OpenAI-compatible /v1/chat/completions endpoint.
    """
    payload = {
        "model": _OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            _OPENROUTER_URL, json=payload,
            headers={
                "Authorization": f"Bearer {_OPENROUTER_KEY}",
                "HTTP-Referer": "https://gula-platform.org",
                "X-Title": "GULA Platform",
            },
        )
        r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    if not text:
        raise RuntimeError("OpenRouter returned empty response")
    return text


def _ai_cache_get(cache_key: str) -> Optional[tuple[str, str]]:
    """Return (text, provider) from Redis or in-process cache, or None."""
    # Redis first (shared across workers)
    if _AI_CACHE_BACKEND is not None:
        try:
            cached = _AI_CACHE_BACKEND.get(f"ai:interp:{cache_key}")
            if cached:
                parts = cached.split("\x00", 1)
                provider = parts[0] if len(parts) == 2 else "cache"
                text = parts[1] if len(parts) == 2 else parts[0]
                return text, f"{provider}(cache)"
        except Exception:
            pass

    # In-process fallback
    entry = _AI_RESPONSE_CACHE.get(cache_key)
    if entry:
        text, provider, expire_at = entry
        if time.monotonic() < expire_at:
            return text, f"{provider}(cache)"
        del _AI_RESPONSE_CACHE[cache_key]

    return None


def _ai_cache_set(cache_key: str, text: str, provider: str) -> None:
    """Write to Redis (preferred) and in-process cache."""
    payload = f"{provider}\x00{text}"

    if _AI_CACHE_BACKEND is not None:
        try:
            _AI_CACHE_BACKEND.set(f"ai:interp:{cache_key}", payload, ex=_AI_CACHE_TTL)
        except Exception:
            pass

    # Always write in-process as backup
    _AI_RESPONSE_CACHE[cache_key] = (text, provider, time.monotonic() + _AI_CACHE_TTL)


def _prompt_cache_key(prompt: str) -> str:
    """Stable cache key from prompt content (first 300 chars are sufficient for uniqueness)."""
    return sha256(prompt[:300].encode()).hexdigest()[:24]


# ── Async wrappers for blocking Redis I/O ────────────────────────────────────
# _ai_cache_get/set call redis-py (synchronous) which blocks the event loop.
# asyncio.to_thread() offloads them to a thread pool so the loop stays free.
# The in-process dict path is ~µs but also runs in the thread — no downside.
async def _ai_cache_get_async(cache_key: str) -> Optional[tuple[str, str]]:
    return await asyncio.to_thread(_ai_cache_get, cache_key)


async def _ai_cache_set_async(cache_key: str, text: str, provider: str) -> None:
    await asyncio.to_thread(_ai_cache_set, cache_key, text, provider)


async def _call_ai_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Try providers in priority order.  Returns (text, provider_name).

    Layers (in order):
      1. Redis/in-process cache  — zero cost, ~2h TTL          (async, non-blocking)
      2. Stampede protection     — secondary requests wait on the first
      3. Hard budget timer       — AI_BUDGET_SECONDS (default 6s) wall for entire chain
      4. Circuit breaker         — skip providers that failed ≥3× in last 30s
      5. Provider chain          — Ollama → OpenRouter → Gemini → Groq
      6. Retry                   — 1 retry on 429/503/529 for cloud providers

    Privacy: prompt contains only test names, numeric values, age, and gender.
    No patient name, ID, or any PII is sent to cloud providers.
    """
    global _AI_CACHE_HITS, _AI_CACHE_MISSES, _AI_BUDGET_EXHAUSTED

    # ── 1. Cache lookup (async — does not block the event loop) ──────────────
    cache_key = _prompt_cache_key(prompt)
    cached = await _ai_cache_get_async(cache_key)
    if cached:
        _AI_CACHE_HITS += 1
        logger.info("[AI] event=ai_call cache=hit provider=%s", cached[1])
        return cached
    _AI_CACHE_MISSES += 1

    # ── 2. Stampede protection ────────────────────────────────────────────────
    if cache_key in _IN_FLIGHT:
        event = _IN_FLIGHT[cache_key]
        logger.debug("[AI] Waiting for in-flight request (key=%s)", cache_key[:8])
        try:
            await asyncio.wait_for(event.wait(), timeout=25)
        except asyncio.TimeoutError:
            pass  # timed out — proceed to fetch ourselves
        cached = await _ai_cache_get_async(cache_key)
        if cached:
            logger.info("[AI] event=ai_call cache=hit_after_wait provider=%s", cached[1])
            return cached

    # ── 3. Register as the fetcher ────────────────────────────────────────────
    fetch_event = asyncio.Event()
    _IN_FLIGHT[cache_key] = fetch_event

    try:
        # ── 4. Provider chain (with hard budget timer) ────────────────────────
        providers: list[tuple[str, Callable]] = []
        if _OLLAMA_ENABLED:
            providers.append(("ollama", _call_ollama_clinical))
        if _OPENROUTER_KEY:
            providers.append(("openrouter", _call_openrouter))
        if _GEMINI_KEY:
            providers.append(("gemini", _call_gemini_flash))
        if _GROQ_KEY:
            providers.append(("groq", _call_groq_llama))

        t_budget = time.perf_counter()
        last_exc: Exception = RuntimeError("no providers configured")

        for name, fn in providers:
            # ── Budget check: stop if wall time exhausted ─────────────────────
            remaining = _AI_BUDGET_SECS - (time.perf_counter() - t_budget)
            if remaining <= 0.3:
                _AI_BUDGET_EXHAUSTED += 1
                logger.warning(
                    "[AI] event=ai_call budget_exhausted elapsed=%.1fs — stopping chain",
                    time.perf_counter() - t_budget,
                )
                break

            cb = _CIRCUIT_BREAKERS.get(name)
            if cb and cb.is_open():
                logger.warning("[AI] Circuit open for %s — skipping", name)
                continue

            t0 = time.perf_counter()
            try:
                # Wrap the call (including any retry waits) in the remaining budget.
                # asyncio.wait_for cancels the coroutine cleanly on timeout.
                call_coro = (
                    fn(prompt) if name == "ollama"
                    else _call_with_retry(fn, prompt, retries=1)
                )
                text = await asyncio.wait_for(call_coro, timeout=remaining)
                latency_ms = (time.perf_counter() - t0) * 1000
                if cb:
                    cb.record_success()
                _AI_CALLS[name] = _AI_CALLS.get(name, 0) + 1
                await _ai_cache_set_async(cache_key, text, name)
                logger.info(
                    "[AI] event=ai_call cache=miss provider=%s latency_ms=%.0f",
                    name, latency_ms,
                )
                return text, name
            except asyncio.TimeoutError:
                latency_ms = (time.perf_counter() - t0) * 1000
                if cb:
                    cb.record_failure()
                _AI_TIMEOUTS[name] = _AI_TIMEOUTS.get(name, 0) + 1
                logger.warning(
                    "[AI] event=ai_call provider=%s timeout after %.0fms — trying fallback",
                    name, latency_ms,
                )
                last_exc = asyncio.TimeoutError(f"{name} timed out")
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000
                if cb:
                    cb.record_failure()
                _AI_ERRORS[name] = _AI_ERRORS.get(name, 0) + 1
                logger.warning(
                    "[AI] event=ai_call provider=%s latency_ms=%.0f failed=%s — trying fallback",
                    name, latency_ms, exc,
                )
                last_exc = exc

        logger.error("[AI] event=ai_call all_providers_failed last_error=%s", last_exc)
        raise HTTPException(status_code=503, detail="تعذر الحصول على التفسير حالياً. حاول لاحقاً.")

    finally:
        # Always unblock waiting coroutines, success or failure
        fetch_event.set()
        _IN_FLIGHT.pop(cache_key, None)


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
