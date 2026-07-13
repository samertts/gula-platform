"""
System Optimizer Routes — GULA Platform
=========================================
Read-only performance monitoring and AI-powered optimization recommendations.
Admin-only: requires role in {admin, lab_admin, province_admin, ministry_admin, master_admin}.

Routes:
  GET /api/optimizer/metrics   — current system snapshot (cached 30s)
  GET /api/optimizer/analyze   — full analysis + AI recommendations (cached 60s)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.ai.system_optimizer import analyze, get_snapshot
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/api/optimizer", tags=["System Optimizer"])

_ADMIN_ROLES = frozenset(
    {
        "admin",
        "lab_admin",
        "province_admin",
        "ministry_admin",
        "master_admin",
    }
)


def _require_admin(user) -> None:
    if user.role not in _ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Only administrators may access system optimizer endpoints.",
            headers={},
        )


@router.get("/metrics")
def get_metrics(current_user=Depends(get_current_user)):
    """
    Return current system metrics snapshot.
    Results are cached for up to 30 seconds — safe to poll.
    """
    _require_admin(current_user)
    snap = get_snapshot()
    return {
        "status": snap.overall_status,
        "collected_at": snap.collected_at,
        "cpu": {
            "load_1m": snap.cpu.load_1m,
            "load_5m": snap.cpu.load_5m,
            "load_15m": snap.cpu.load_15m,
            "num_cpus": snap.cpu.num_cpus,
            "load_per_cpu": snap.cpu.load_per_cpu,
            "status": snap.cpu.status,
        },
        "memory": {
            "total_mb": snap.memory.total_mb,
            "used_mb": snap.memory.used_mb,
            "available_mb": snap.memory.available_mb,
            "used_pct": snap.memory.used_pct,
            "status": snap.memory.status,
        },
        "database": {
            "pool_size": snap.db.pool_size,
            "checked_out": snap.db.checked_out,
            "overflow": snap.db.overflow,
            "utilization_pct": snap.db.utilization_pct,
            "status": snap.db.status,
        },
    }


@router.get("/analyze")
async def run_analysis(
    use_ai: bool = Query(
        default=True,
        description=(
            "Use local Ollama for an AI-generated narrative. "
            "Falls back to rule-based analysis if Ollama is unavailable. "
            "Rate-limited to 1 AI call per 60 seconds."
        ),
    ),
    current_user=Depends(get_current_user),
):
    """
    Full system analysis with rule-based + optional AI recommendations.

    - Results cached for 60 seconds — safe to poll from dashboards.
    - AI calls are rate-limited (1/min) and hard-timeout (15s) to protect the server.
    - When Ollama is unavailable, rule-based recommendations are always returned.
    """
    _require_admin(current_user)
    return await analyze(use_ai=use_ai)
