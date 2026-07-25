from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.public_health.application.service import PublicHealthService
from app.public_health.domain.entities import (
    DiseaseCase,
    ImmunizationRecord,
    OutbreakAlert,
    PublicHealthReport,
    SurveillanceSignal,
)
from app.public_health.exceptions import (
    DiseaseCaseNotFoundError,
    OutbreakNotFoundError,
)

router = APIRouter(prefix="/public-health", tags=["National Public Health Surveillance"])


def _get_service(db: Session = Depends(get_db)) -> PublicHealthService:
    try:
        from app.kernel import Kernel

        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return PublicHealthService(db=db, event_bus=event_bus)


# ── Disease Cases ──


@router.post("/disease-cases", status_code=status.HTTP_201_CREATED)
async def report_case(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _case_to_dict(service.report_case(body))


@router.get("/disease-cases")
async def list_cases(
    disease_code: str | None = Query(None),
    region: str | None = Query(None),
    confirmed: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [
        _case_to_dict(c) for c in service.list_cases(disease_code, region, confirmed, skip, limit)
    ]


@router.get("/disease-cases/{case_id}")
async def get_case(
    case_id: str,
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _case_to_dict(service.get_case(case_id))
    except DiseaseCaseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


@router.get("/disease-cases/stats")
async def get_case_stats(
    region: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_case_stats(region, days)


# ── Outbreak Alerts ──


@router.post("/outbreak-alerts", status_code=status.HTTP_201_CREATED)
async def raise_alert(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _alert_to_dict(service.raise_alert(body))


@router.get("/outbreak-alerts")
async def list_alerts(
    status: str | None = Query(None),
    alert_level: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [
        _alert_to_dict(a) for a in service.list_alerts(status, alert_level, region, skip, limit)
    ]


@router.get("/outbreak-alerts/{alert_id}")
async def get_alert(
    alert_id: str,
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _alert_to_dict(service.get_alert(alert_id))
    except OutbreakNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


@router.put("/outbreak-alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _alert_to_dict(
            service.update_alert_status(alert_id, body.get("status", ""), body.get("notes", ""))
        )
    except OutbreakNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        ) from e


# ── Surveillance Signals ──


@router.post("/surveillance-signals", status_code=status.HTTP_201_CREATED)
async def record_signal(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _signal_to_dict(service.record_signal(body))


@router.get("/surveillance-signals")
async def list_signals(
    alert_level: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_signal_to_dict(s) for s in service.list_signals(alert_level, region, skip, limit)]


# ── AI Fabric Integration ──


@router.post("/analyze")
async def analyze_surveillance(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.analyze_surveillance(
        body.get("disease", ""),
        body.get("region", ""),
        body.get("case_count", 0),
        body.get("expected_daily", 0),
    )


@router.post("/detect-outbreak")
async def detect_outbreak_cluster(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.detect_outbreak_cluster(
        body.get("disease", ""),
        body.get("region", ""),
        body.get("cases", []),
    )


# ── Immunization ──


@router.post("/vaccinations", status_code=status.HTTP_201_CREATED)
async def record_vaccination(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _immunization_to_dict(service.record_vaccination(body))


@router.get("/vaccinations")
async def list_vaccinations(
    patient_id: str | None = Query(None),
    vaccine: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [
        _immunization_to_dict(v)
        for v in service.list_vaccinations(patient_id, vaccine, skip, limit)
    ]


@router.get("/vaccinations/coverage")
async def vaccination_coverage(
    vaccine: str | None = Query(None),
    region: str | None = Query(None),
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_vaccination_coverage(vaccine, region)


# ── Reports ──


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def publish_report(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _report_to_dict(service.publish_report(body))


@router.get("/reports")
async def list_reports(
    report_type: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_report_to_dict(r) for r in service.list_reports(report_type, region, skip, limit)]


# ── Dashboard ──


@router.get("/dashboard")
async def get_dashboard(
    region: str | None = Query(None),
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard(region)


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_public_health_surveillance", "version": "1.0.0"}


# ── Serializers ──


def _case_to_dict(c: DiseaseCase) -> dict[str, Any]:
    return {
        "id": c.id,
        "disease_code": c.disease_code,
        "disease_name": c.disease_name,
        "region": c.region,
        "is_confirmed": c.is_confirmed,
        "source": c.source,
        "reported_by": c.reported_by,
        "reported_at": c.reported_at,
    }


def _alert_to_dict(a: OutbreakAlert) -> dict[str, Any]:
    return {
        "id": a.id,
        "disease": a.disease,
        "region": a.region,
        "confirmed_cases": a.confirmed_cases,
        "alert_level": a.alert_level,
        "status": a.status,
        "recommendations": a.recommendations,
    }


def _signal_to_dict(s: SurveillanceSignal) -> dict[str, Any]:
    return {
        "id": s.id,
        "disease": s.disease,
        "region": s.region,
        "case_count": s.case_count,
        "z_score": s.z_score,
        "alert_level": s.alert_level,
        "recommendation": s.recommendation,
    }


def _immunization_to_dict(v: ImmunizationRecord) -> dict[str, Any]:
    return {
        "id": v.id,
        "patient_id": v.patient_id,
        "patient_name": v.patient_name,
        "vaccine": v.vaccine,
        "dose_number": v.dose_number,
        "administered_by": v.administered_by,
    }


def _report_to_dict(r: PublicHealthReport) -> dict[str, Any]:
    return {
        "id": r.id,
        "report_type": r.report_type,
        "region": r.region,
        "total_cases": r.total_cases,
        "total_deaths": r.total_deaths,
        "key_findings": r.key_findings,
        "published_by": r.published_by,
    }
