from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.lifecycle_platform.application.service import LifecycleService
from app.lifecycle_platform.domain.entities import (
    CompatibilityEntry,
    Component,
    DeprecationNotice,
    Release,
    UpgradePath,
)
from app.lifecycle_platform.exceptions import (
    ComponentNotFoundError,
    ReleaseNotFoundError,
    UpgradePathNotFoundError,
    VersionConflictError,
)

router = APIRouter(prefix="/lifecycle", tags=["National Platform Lifecycle & Governance"])


def _get_service(db: Session = Depends(get_db)) -> LifecycleService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return LifecycleService(db=db, event_bus=event_bus)


# ── Component Registry ──

@router.post("/components", status_code=status.HTTP_201_CREATED)
async def register_component(
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _component_to_dict(service.register_component(body))
    except VersionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/components")
async def list_components(
    component_type: str | None = Query(None),
    stage: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: LifecycleService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_component_to_dict(c) for c in service.list_components(component_type, stage, skip, limit)]


@router.get("/components/{component_id}")
async def get_component(
    component_id: str,
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _component_to_dict(service.get_component(component_id))
    except ComponentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/components/name/{name}")
async def find_component(
    name: str,
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _component_to_dict(service.find_component(name))
    except ComponentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/components/{component_id}/stage")
async def update_component_stage(
    component_id: str,
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _component_to_dict(service.update_component_stage(component_id, body.get("stage", "")))
    except ComponentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# ── Releases ──

@router.post("/releases", status_code=status.HTTP_201_CREATED)
async def create_release(
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    return _release_to_dict(service.create_release(body))


@router.get("/releases")
async def list_releases(
    component_id: str | None = Query(None),
    channel: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: LifecycleService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_release_to_dict(r) for r in service.list_releases(component_id, channel, status, skip, limit)]


@router.get("/releases/{release_id}")
async def get_release(
    release_id: str,
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _release_to_dict(service.get_release(release_id))
    except ReleaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/releases/{release_id}/approve")
async def approve_release(
    release_id: str,
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _release_to_dict(service.approve_release(release_id, body))
    except ReleaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# ── Compatibility Matrix ──

@router.post("/compatibility", status_code=status.HTTP_201_CREATED)
async def record_compatibility(
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    return _compat_to_dict(service.record_compatibility(body))


@router.get("/compatibility/check")
async def check_compatibility(
    component_a: str = Query(...),
    component_b: str = Query(...),
    version_a: str = Query(...),
    version_b: str = Query(...),
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    result = service.check_compatibility(component_a, component_b, version_a, version_b)
    if result is None:
        return {"compatible": "unknown", "level": "unknown", "message": "No compatibility data"}
    return _compat_to_dict(result)


@router.get("/compatibility/{component}/{version}")
async def list_compatibility(
    component: str,
    version: str,
    service: LifecycleService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.list_compatibility_for(component, version)


# ── Upgrade Paths ──

@router.post("/upgrade-paths", status_code=status.HTTP_201_CREATED)
async def create_upgrade_path(
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    return _upgrade_to_dict(service.create_upgrade_path(body))


@router.get("/upgrade-paths")
async def list_upgrade_paths(
    component: str | None = Query(None),
    service: LifecycleService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_upgrade_to_dict(u) for u in service.list_upgrade_paths(component)]


@router.get("/upgrade-paths/{component}/{from_version}/{to_version}")
async def find_upgrade_path(
    component: str,
    from_version: str,
    to_version: str,
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _upgrade_to_dict(service.find_upgrade_path(component, from_version, to_version))
    except UpgradePathNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# ── Deprecation ──

@router.post("/deprecations", status_code=status.HTTP_201_CREATED)
async def issue_deprecation(
    body: dict[str, Any],
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    return _deprecation_to_dict(service.issue_deprecation(body))


@router.get("/deprecations")
async def list_deprecations(
    component_id: str | None = Query(None),
    service: LifecycleService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_deprecation_to_dict(d) for d in service.list_deprecations(component_id)]


# ── Dashboard ──

@router.get("/dashboard")
async def get_dashboard(
    service: LifecycleService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_lifecycle_platform", "version": "1.0.0"}


# ── Serializers ──

def _component_to_dict(c: Component) -> dict[str, Any]:
    return {"id": c.id, "name": c.name, "component_type": c.component_type,
            "current_version": c.current_version, "stage": c.stage, "owner": c.owner,
            "description": c.description, "repository": c.repository}


def _release_to_dict(r: Release) -> dict[str, Any]:
    return {"id": r.id, "component_id": r.component_id, "version": r.version,
            "channel": r.channel, "status": r.status, "release_notes": r.release_notes,
            "certification_level": r.certification_level, "approved_by": r.approved_by,
            "deployed_by": r.deployed_by, "artifact_url": r.artifact_url}


def _compat_to_dict(e: CompatibilityEntry) -> dict[str, Any]:
    return {"id": e.id, "component_a": e.component_a, "component_b": e.component_b,
            "version_a": e.version_a, "version_b": e.version_b, "level": e.level,
            "notes": e.notes}


def _upgrade_to_dict(u: UpgradePath) -> dict[str, Any]:
    return {"id": u.id, "component": u.component, "from_version": u.from_version,
            "to_version": u.to_version, "severity": u.severity,
            "estimated_duration_minutes": u.estimated_duration_minutes}


def _deprecation_to_dict(d: DeprecationNotice) -> dict[str, Any]:
    return {"id": d.id, "component_id": d.component_id, "component_name": d.component_name,
            "deprecation_policy": d.deprecation_policy,
            "replacement_component": d.replacement_component,
            "migration_guide": d.migration_guide, "announced_by": d.announced_by}
