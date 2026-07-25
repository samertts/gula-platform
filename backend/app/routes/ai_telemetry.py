"""AI Interaction Telemetry & Feedback — Phase 3 + Phase 4.

Routes
------
  POST /api/ai/interactions                — log a single user↔AI interaction
  POST /api/ai/interactions/{id}/refs      — append retrieval refs (RAG audit trail)
  POST /api/ai/feedback                    — explicit feedback signal
  POST /api/ai/unresolved                  — flag a question the AI could not answer
  GET  /api/ai/dataset/summary             — aggregate counters (lab-scoped)
  GET  /api/ai/dataset/status              — flag status (always visible)

All write endpoints require an authenticated ``LabUser`` and enforce tenant
isolation by stamping ``lab_id`` from the JWT (never trusting the request body).

Anonymisation invariant
-----------------------
The schema deliberately has no columns for PII. Routes additionally:
  • Reject prompts > MAX_PROMPT_LEN
  • Truncate response to MAX_RESPONSE_LEN
  • Reject signals not in ``FEEDBACK_SIGNALS``
  • Use the caller-provided ``anonymous_session_id`` verbatim (it is the
    caller's responsibility to hash a session-stable identifier on the
    client; we never derive it from user_id / patient_id here).

Flag-gating
-----------
All writes require ``ENABLE_AI_DATASET=true`` (503 ``AI_DATASET_DISABLED``
otherwise). The feedback endpoint additionally requires
``ENABLE_AI_FEEDBACK=true``. ``GET /api/ai/dataset/status`` is always
reachable so operators can inspect the flag state.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.core.ai_dataset_flags import (
    require_dataset,
    require_feedback,
    status_snapshot,
)
from app.database import get_db
from app.models.ai_interaction import (
    AIFeedback,
    AIInteraction,
    AIRetrievalRef,
    AIUnresolvedQuestion,
)
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.ai.dataset")

router = APIRouter(prefix="/api/ai", tags=["AI Dataset (Phase 3+4)"])


# ── Validation constants ────────────────────────────────────────────────────
MAX_PROMPT_LEN = 8_000
MAX_RESPONSE_LEN = 16_000
MAX_NOTES_LEN = 2_000
MAX_REFS_PER_REQUEST = 50
MAX_SESSION_ID_LEN = 128

# Allowed values — keep narrow on purpose. Adding new ones is an explicit
# product decision (analytics / RAG-training pipelines key off these).
FEEDBACK_SIGNALS = {
    "helpful",
    "not_helpful",
    "unclear",
    "need_doctor",
    "incorrect_interpretation",
}

INTENT_VALUES = {
    "interpret_result",
    "explain_biomarker",
    "navigate",
    "educational",
    "decision_support",
    "unknown",
}

STATUS_VALUES = {"ok", "error", "guardrail_blocked", "escalated"}

# Directive §8 risk classes. Order is significant for severity comparisons.
RISK_LEVELS = ("informational", "low_risk", "moderate_risk", "high_risk")
RISK_LEVEL_SET = set(RISK_LEVELS)

# Bounded safety-flag vocabulary. We deliberately reject unknown flags here
# rather than at the DB layer so the analytics surface stays clean. Adding a
# new flag is a one-line product decision.
SAFETY_FLAG_VALUES = {
    "pii_detected",
    "prompt_injection_suspected",
    "off_topic",
    "policy_violation",
    "low_confidence",
    "stale_knowledge",
    "non_medical_query",
    "ambiguous_query",
}
MAX_SAFETY_FLAGS = 16


# ── Pydantic schemas ────────────────────────────────────────────────────────


class RetrievalRefIn(BaseModel):
    source: str | None = Field(None, max_length=64)
    doc_id: str | None = Field(None, max_length=128)
    doc_title: str | None = Field(None, max_length=256)
    chunk_text: str | None = Field(None, max_length=4_000)
    similarity: float | None = Field(None, ge=0.0, le=1.0)
    rank: int | None = Field(None, ge=0, le=10_000)


class InteractionIn(BaseModel):
    anonymous_session_id: str = Field(..., min_length=1, max_length=MAX_SESSION_ID_LEN)
    language: str | None = Field(None, max_length=8)
    region: str | None = Field(None, max_length=64)
    intent: str | None = Field(None, max_length=64)
    prompt: str | None = Field(None, max_length=MAX_PROMPT_LEN)
    prompt_redacted: bool = False
    response: str | None = Field(None, max_length=MAX_RESPONSE_LEN)
    response_model: str | None = Field(None, max_length=64)
    retrieval_strategy: str | None = Field(None, max_length=64)
    retrieval_refs: list[RetrievalRefIn] | None = None
    biomarkers: list[str] | None = None
    latency_ms: int | None = Field(None, ge=0, le=600_000)
    status: str = Field("ok", max_length=20)
    error_code: str | None = Field(None, max_length=64)

    # Directive §8 — AI safety layer
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    risk_level: str | None = Field(None, max_length=32)
    escalation_recommended: bool = False

    # Directive §14 — hallucination control
    retrieval_used: bool | None = None
    source_quality: float | None = Field(None, ge=0.0, le=1.0)
    unsupported_claims: int | None = Field(None, ge=0, le=1_000)
    fallback_generation: bool = False
    safety_flags: list[str] | None = None


class InteractionOut(BaseModel):
    id: str
    lab_id: int
    created_at: datetime


class FeedbackIn(BaseModel):
    interaction_id: str
    anonymous_session_id: str = Field(..., min_length=1, max_length=MAX_SESSION_ID_LEN)
    signal: str
    notes: str | None = Field(None, max_length=MAX_NOTES_LEN)


class UnresolvedIn(BaseModel):
    interaction_id: str | None = None
    anonymous_session_id: str | None = Field(None, max_length=MAX_SESSION_ID_LEN)
    question: str = Field(..., min_length=1, max_length=MAX_PROMPT_LEN)
    language: str | None = Field(None, max_length=8)
    category: str | None = Field(None, max_length=64)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _parse_uuid(s: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(s)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_UUID", "field": field},
        ) from None


def _now() -> datetime:
    return datetime.now(UTC)


# ── POST /api/ai/interactions ───────────────────────────────────────────────


@router.post(
    "/interactions",
    response_model=InteractionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_dataset())],
    summary="Log a single AI interaction (Phase 3)",
)
def log_interaction(
    payload: InteractionIn,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.status not in STATUS_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATUS", "allowed": sorted(STATUS_VALUES)},
        )
    # Intent is free-form for forward compatibility but we warn on unknowns.
    if payload.intent and payload.intent not in INTENT_VALUES:
        logger.info(
            "ai.dataset.intent.unknown intent=%s lab_id=%s",
            payload.intent,
            current_user.lab_id,
        )

    if payload.risk_level is not None and payload.risk_level not in RISK_LEVEL_SET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_RISK_LEVEL", "allowed": list(RISK_LEVELS)},
        )

    # Directive §8 mandatory rule: high-risk outputs require physician
    # escalation guidance. Reject the log if the caller claims high_risk
    # without setting escalation_recommended — this catches a class of
    # safety-layer regressions at the telemetry boundary.
    if payload.risk_level == "high_risk" and not payload.escalation_recommended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "HIGH_RISK_REQUIRES_ESCALATION"},
        )

    safety_flags = payload.safety_flags or None
    if safety_flags is not None:
        if len(safety_flags) > MAX_SAFETY_FLAGS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "TOO_MANY_SAFETY_FLAGS", "max": MAX_SAFETY_FLAGS},
            )
        unknown = [f for f in safety_flags if f not in SAFETY_FLAG_VALUES]
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SAFETY_FLAG",
                    "unknown": unknown,
                    "allowed": sorted(SAFETY_FLAG_VALUES),
                },
            )

    refs = payload.retrieval_refs or []
    if len(refs) > MAX_REFS_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TOO_MANY_REFS", "max": MAX_REFS_PER_REQUEST},
        )

    # Hallucination-control consistency: if retrieval_used is True but no
    # refs were attached AND no retrieval_strategy supplied, that's a
    # contradictory log — surface it rather than silently persisting.
    if payload.retrieval_used is True and not refs and not payload.retrieval_strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "RETRIEVAL_USED_WITHOUT_EVIDENCE"},
        )

    now = _now()
    interaction = AIInteraction(
        id=uuid.uuid4(),
        lab_id=current_user.lab_id,
        anonymous_session_id=payload.anonymous_session_id,
        language=payload.language,
        region=payload.region,
        intent=payload.intent,
        prompt=payload.prompt,
        prompt_redacted=payload.prompt_redacted,
        response=payload.response,
        response_model=payload.response_model,
        retrieval_strategy=payload.retrieval_strategy,
        retrieval_count=len(refs) if refs else None,
        biomarkers=payload.biomarkers,
        latency_ms=payload.latency_ms,
        status=payload.status,
        error_code=payload.error_code,
        # Safety layer (§8)
        confidence_score=payload.confidence_score,
        risk_level=payload.risk_level,
        escalation_recommended=payload.escalation_recommended,
        # Hallucination control (§14)
        retrieval_used=payload.retrieval_used,
        source_quality=payload.source_quality,
        unsupported_claims=payload.unsupported_claims,
        fallback_generation=payload.fallback_generation,
        safety_flags=safety_flags,
        created_at=now,
    )
    db.add(interaction)
    db.flush()  # surface FK / constraint issues before we attach refs

    for r in refs:
        db.add(
            AIRetrievalRef(
                id=uuid.uuid4(),
                interaction_id=interaction.id,
                source=r.source,
                doc_id=r.doc_id,
                doc_title=r.doc_title,
                chunk_text=r.chunk_text,
                similarity=r.similarity,
                rank=r.rank,
                created_at=now,
            ),
        )

    db.commit()
    return InteractionOut(
        id=str(interaction.id),
        lab_id=interaction.lab_id,
        created_at=interaction.created_at,
    )


# ── POST /api/ai/interactions/{id}/refs ─────────────────────────────────────


@router.post(
    "/interactions/{interaction_id}/refs",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_dataset())],
    summary="Append retrieval refs to an existing interaction",
)
def append_retrieval_refs(
    interaction_id: str,
    refs: list[RetrievalRefIn],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iid = _parse_uuid(interaction_id, "interaction_id")
    if len(refs) > MAX_REFS_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TOO_MANY_REFS", "max": MAX_REFS_PER_REQUEST},
        )

    # Tenant isolation: caller must own the interaction.
    interaction = (
        db.query(AIInteraction)
        .filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)
        .first()
    )
    if interaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INTERACTION_NOT_FOUND"},
        )

    now = _now()
    for r in refs:
        db.add(
            AIRetrievalRef(
                id=uuid.uuid4(),
                interaction_id=iid,
                source=r.source,
                doc_id=r.doc_id,
                doc_title=r.doc_title,
                chunk_text=r.chunk_text,
                similarity=r.similarity,
                rank=r.rank,
                created_at=now,
            ),
        )
    db.commit()
    return {"appended": len(refs)}


# ── POST /api/ai/feedback ───────────────────────────────────────────────────


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_feedback())],
    summary="Submit explicit feedback on an AI interaction (Phase 4)",
)
def submit_feedback(
    payload: FeedbackIn,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.signal not in FEEDBACK_SIGNALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_SIGNAL", "allowed": sorted(FEEDBACK_SIGNALS)},
        )

    iid = _parse_uuid(payload.interaction_id, "interaction_id")

    interaction = (
        db.query(AIInteraction)
        .filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)
        .first()
    )
    if interaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INTERACTION_NOT_FOUND"},
        )

    fb = AIFeedback(
        id=uuid.uuid4(),
        interaction_id=iid,
        lab_id=current_user.lab_id,
        anonymous_session_id=payload.anonymous_session_id,
        signal=payload.signal,
        notes=payload.notes,
        created_at=_now(),
    )
    db.add(fb)
    db.commit()
    return {"id": str(fb.id), "signal": fb.signal}


# ── POST /api/ai/unresolved ─────────────────────────────────────────────────


@router.post(
    "/unresolved",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_dataset())],
    summary="Flag a question the AI could not resolve",
)
def log_unresolved(
    payload: UnresolvedIn,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iid_uuid: uuid.UUID | None = None
    if payload.interaction_id:
        iid_uuid = _parse_uuid(payload.interaction_id, "interaction_id")
        # If linked, ensure caller owns it (tenant isolation).
        exists = (
            db.query(AIInteraction.id)
            .filter(AIInteraction.id == iid_uuid, AIInteraction.lab_id == current_user.lab_id)
            .first()
        )
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INTERACTION_NOT_FOUND"},
            )

    q = AIUnresolvedQuestion(
        id=uuid.uuid4(),
        interaction_id=iid_uuid,
        lab_id=current_user.lab_id,
        anonymous_session_id=payload.anonymous_session_id,
        question=payload.question,
        language=payload.language,
        category=payload.category,
        status="open",
        created_at=_now(),
    )
    db.add(q)
    db.commit()
    return {"id": str(q.id), "status": q.status}


# ── GET /api/ai/dataset/summary ─────────────────────────────────────────────


@router.get(
    "/dataset/summary",
    dependencies=[Depends(require_dataset())],
    summary="Aggregate counters for the calling lab (Phase 3+6 readout)",
)
def dataset_summary(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab_id = current_user.lab_id

    total_interactions = (
        db.query(func.count(AIInteraction.id)).filter(AIInteraction.lab_id == lab_id).scalar() or 0
    )
    total_feedback = (
        db.query(func.count(AIFeedback.id)).filter(AIFeedback.lab_id == lab_id).scalar() or 0
    )
    open_unresolved = (
        db.query(func.count(AIUnresolvedQuestion.id))
        .filter(AIUnresolvedQuestion.lab_id == lab_id, AIUnresolvedQuestion.status == "open")
        .scalar()
        or 0
    )
    feedback_breakdown = dict(
        db.query(AIFeedback.signal, func.count(AIFeedback.id))
        .filter(AIFeedback.lab_id == lab_id)
        .group_by(AIFeedback.signal)
        .all(),
    )

    # Directive §8 + §14 — surface safety + hallucination posture.
    # All filters tenant-scoped on lab_id.
    risk_breakdown = dict(
        db.query(AIInteraction.risk_level, func.count(AIInteraction.id))
        .filter(AIInteraction.lab_id == lab_id, AIInteraction.risk_level.isnot(None))
        .group_by(AIInteraction.risk_level)
        .all(),
    )
    escalation_count = (
        db.query(func.count(AIInteraction.id))
        .filter(AIInteraction.lab_id == lab_id, AIInteraction.escalation_recommended.is_(True))
        .scalar()
        or 0
    )
    fallback_count = (
        db.query(func.count(AIInteraction.id))
        .filter(AIInteraction.lab_id == lab_id, AIInteraction.fallback_generation.is_(True))
        .scalar()
        or 0
    )
    avg_confidence = (
        db.query(func.avg(AIInteraction.confidence_score))
        .filter(AIInteraction.lab_id == lab_id, AIInteraction.confidence_score.isnot(None))
        .scalar()
    )
    avg_source_quality = (
        db.query(func.avg(AIInteraction.source_quality))
        .filter(AIInteraction.lab_id == lab_id, AIInteraction.source_quality.isnot(None))
        .scalar()
    )
    return {
        "lab_id": lab_id,
        "interactions_total": total_interactions,
        "feedback_total": total_feedback,
        "unresolved_open": open_unresolved,
        "feedback_breakdown": feedback_breakdown,
        # §8 + §14 safety posture
        "risk_breakdown": risk_breakdown,
        "escalation_recommended_total": escalation_count,
        "fallback_generation_total": fallback_count,
        "avg_confidence_score": float(avg_confidence) if avg_confidence is not None else None,
        "avg_source_quality": float(avg_source_quality) if avg_source_quality is not None else None,
    }


# ── GET /api/ai/dataset/status (always available) ───────────────────────────


@router.get(
    "/dataset/status",
    summary="Inspect AI-dataset feature-flag state",
)
def dataset_status():
    snap = status_snapshot()
    return {
        "ai_dataset_enabled": snap["ai_dataset_enabled"],
        "ai_feedback_enabled": snap["ai_feedback_enabled"],
        # Surface for orchestrator dashboards.
        "phase": "production_launch_2026_05_11",
    }
