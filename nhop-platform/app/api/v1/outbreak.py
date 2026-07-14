"""Outbreak detection and public-health surveillance endpoints.

Restricted to MINISTRY and ADMIN roles. All three routes are read-only and
are safe to expose to dashboards and the hourly background task.

    GET /v1/outbreak/alerts                 - current outbreak alerts
    GET /v1/outbreak/heatmap/{disease_code} - province-level case counts
    GET /v1/outbreak/resistance             - antibiotic resistance report
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.app._compat import UTC

from ...core.database import get_db
from ...core.rbac import Role, require_roles
from ...schemas.outbreak import (
    AlertsResponse,
    HeatmapResponse,
    ResistanceResponse,
)
from ...schemas.outbreak import (
    OutbreakAlert as OutbreakAlertSchema,
)
from ...services.audit import log_action
from ...services.outbreak_detection import (
    check_outbreak,
    get_disease_heatmap,
    get_resistance_report,
)

router = APIRouter(prefix="/outbreak", tags=["outbreak"])

_ministry_or_admin = require_roles(Role.MINISTRY, Role.ADMIN)


def _actor_id(request: Request) -> str | None:
    return request.headers.get("X-Actor-Id")


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/alerts", response_model=AlertsResponse)
def list_alerts(
    request: Request,
    db: Session = Depends(get_db),
    role: str = Depends(_ministry_or_admin),
) -> AlertsResponse:
    alerts = check_outbreak(db)
    log_action(
        db,
        action="outbreak.alerts",
        target_type="outbreak_scan",
        target_id="-",
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"role": role, "alert_count": len(alerts)},
    )
    db.commit()
    return AlertsResponse(
        generated_at=datetime.now(UTC),
        alerts=[
            OutbreakAlertSchema(
                disease_code=a.disease_code,
                disease_name=a.disease_name,
                province=a.province,
                current_count=a.current_count,
                baseline_avg=a.baseline_avg,
                ratio=a.ratio,
                severity=a.severity,
                detected_at=a.detected_at,
            )
            for a in alerts
        ],
    )


@router.get("/heatmap/{disease_code}", response_model=HeatmapResponse)
def heatmap(
    disease_code: str,
    request: Request,
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
    role: str = Depends(_ministry_or_admin),
) -> HeatmapResponse:
    data = get_disease_heatmap(db, disease_code, days=days)
    log_action(
        db,
        action="outbreak.heatmap",
        target_type="disease",
        target_id=disease_code,
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"role": role, "days": days, "total": data["total"]},
    )
    db.commit()
    return HeatmapResponse(**data)


@router.get("/resistance", response_model=ResistanceResponse)
def resistance(
    request: Request,
    province: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    role: str = Depends(_ministry_or_admin),
) -> ResistanceResponse:
    data = get_resistance_report(db, province=province)
    log_action(
        db,
        action="outbreak.resistance",
        target_type="resistance_report",
        target_id=province or "-",
        actor_id=_actor_id(request),
        ip_address=_client_ip(request),
        metadata={"role": role, "total_pairs": data["total_pairs"]},
    )
    db.commit()
    return ResistanceResponse(**data)
