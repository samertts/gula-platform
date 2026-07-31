from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.metrics_service import (
    build_deep_health,
    build_health_status,
    build_prometheus_response,
    get_json_metrics,
)

router = APIRouter(tags=["metrics"])

_WIDE_ROLES = {"master_admin", "ministry_admin", "province_admin"}


@router.get("/health")
def liveness_health():
    """Liveness probe — the process is up and serving requests."""
    return build_health_status()


@router.get("/health/ready")
def readiness_health():
    """Readiness probe — DB, Redis and degradation state."""
    return build_health_status()


@router.get("/health/status")
def detailed_health():
    """Detailed health status — always visible so operators can diagnose startup failures."""
    return build_health_status()


@router.get("/health/deep")
def deep_health():
    """Deep health — component latencies, queue backlog, process state."""
    return build_deep_health()


@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    is_wide = current_user.role in _WIDE_ROLES
    return get_json_metrics(
        db,
        lab_id=current_user.lab_id,
        is_wide=is_wide,
    )


@router.get("/metrics/prom", include_in_schema=False)
def prometheus_metrics(request: Request, db: Session = Depends(get_db)):
    return build_prometheus_response(request, db)
