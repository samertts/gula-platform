from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.compliance.services import ComplianceService
from app.identity.niam_async_db import get_niam_db
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)

router = APIRouter(prefix="/compliance", tags=["NIAM Compliance"])


async def _require_compliance_permission(
    actor: NiamActor,
    db: AsyncSession,
    *,
    organization_id: str,
    permission_key: str,
) -> None:
    decision = await AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="read" if permission_key.endswith(".read") else "manage",
            resource_type="compliance",
            permission_key=permission_key,
            organization_id=organization_id,
            sensitivity="critical" if permission_key != "compliance.read" else "high",
            resource_context={"exists": True, "organization_id": organization_id},
        ),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compliance authorization denied")


@router.post("/frameworks")
async def register_framework(
    organization_id: str = Query(min_length=1, max_length=26),
    name: str = Query(min_length=1, max_length=300),
    framework_type: str = Query(min_length=1, max_length=50),
    version: str = Query(default="", max_length=20),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.manage")
    framework = await ComplianceService(db).register_framework(name=name, framework_type=framework_type, version=version or None)
    await db.commit()
    return {"framework": framework.to_dict()}


@router.get("/frameworks")
async def list_frameworks(
    organization_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.read")
    frameworks = await ComplianceService(db).list_frameworks()
    return {"frameworks": [framework.to_dict() for framework in frameworks]}


@router.get("/frameworks/{framework_id}")
async def get_framework(
    framework_id: str,
    organization_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.read")
    framework = await ComplianceService(db).get_framework(framework_id)
    if framework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance framework not found")
    return {"framework": framework.to_dict()}


@router.post("/checks")
async def run_check(
    organization_id: str = Query(min_length=1, max_length=26),
    framework_id: str = Query(min_length=1, max_length=26),
    requirement_id: str = Query(min_length=1, max_length=100),
    target_type: str = Query(min_length=1, max_length=50),
    target_id: str = Query(min_length=1, max_length=100),
    check_type: str = Query(default="automated", max_length=20),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.manage")
    if target_type not in {"organization", "facility", "workspace", "control", "system"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported compliance target type")
    try:
        check = await ComplianceService(db).run_check(
            framework_id=framework_id,
            requirement_id=requirement_id,
            target_type=target_type,
            target_id=target_id,
            organization_id=organization_id,
            checked_by=actor.account.id,
            check_type=check_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.commit()
    return {"check": check.to_dict()}


@router.get("/checks/{target_type}/{target_id}")
async def list_checks(
    target_type: str,
    target_id: str,
    organization_id: str = Query(min_length=1, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.read")
    checks = await ComplianceService(db).get_checks(target_type, target_id, organization_id=organization_id)
    return {"checks": [check.to_dict() for check in checks]}


@router.post("/reports")
async def generate_report(
    organization_id: str = Query(min_length=1, max_length=26),
    framework_id: str = Query(min_length=1, max_length=26),
    report_type: str = Query(default="self_assessment", max_length=20),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=organization_id, permission_key="compliance.report")
    report = await ComplianceService(db).generate_report(
        org_id=organization_id,
        framework_id=framework_id,
        generated_by=actor.account.id,
        report_type=report_type,
    )
    await db.commit()
    return {"report": report.to_dict()}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    report = await ComplianceService(db).get_report(report_id)
    if report is None or report.organization_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance report not found")
    await _require_compliance_permission(actor, db, organization_id=report.organization_id, permission_key="compliance.read")
    return {"report": report.to_dict()}


@router.get("/status/{org_id}")
async def get_org_compliance_status(
    org_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_niam_db),
):
    await _require_compliance_permission(actor, db, organization_id=org_id, permission_key="compliance.read")
    statuses = await ComplianceService(db).get_org_compliance_status(org_id)
    return {"compliance_status": statuses}
