from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.compliance.services import ComplianceService
from app.identity.security import get_current_identity

router = APIRouter(
    prefix="/compliance",
    tags=["NIAM Compliance"],
    dependencies=[Depends(get_current_identity)],
)


@router.post("/frameworks")
async def register_framework(
    name: str,
    framework_type: str,
    version: str = "",
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    framework = await service.register_framework(
        name=name,
        framework_type=framework_type,
        version=version or None,
    )
    return {"framework": framework.to_dict()}


@router.get("/frameworks")
async def list_frameworks(
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    frameworks = await service.list_frameworks()
    return {"frameworks": [f.to_dict() for f in frameworks]}


@router.get("/frameworks/{framework_id}")
async def get_framework(
    framework_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    framework = await service.get_framework(framework_id)
    if not framework:
        return {"error": "not_found"}
    return {"framework": framework.to_dict()}


@router.post("/checks")
async def run_check(
    framework_id: str,
    requirement_id: str,
    target_type: str,
    target_id: str,
    checked_by: str,
    check_type: str = "automated",
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    try:
        check = await service.run_check(
            framework_id=framework_id,
            requirement_id=requirement_id,
            target_type=target_type,
            target_id=target_id,
            checked_by=checked_by,
            check_type=check_type,
        )
        return {"check": check.to_dict()}
    except ValueError as e:
        return {"error": str(e)}


@router.get("/checks/{target_type}/{target_id}")
async def list_checks(
    target_type: str,
    target_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    checks = await service.get_checks(target_type, target_id)
    return {"checks": [c.to_dict() for c in checks]}


@router.post("/reports")
async def generate_report(
    org_id: str = "",
    framework_id: str = "",
    generated_by: str = "",
    report_type: str = "self_assessment",
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    report = await service.generate_report(
        org_id=org_id or None,
        framework_id=framework_id,
        generated_by=generated_by,
        report_type=report_type,
    )
    return {"report": report.to_dict()}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    report = await service.get_report(report_id)
    if not report:
        return {"error": "not_found"}
    return {"report": report.to_dict()}


@router.get("/status/{org_id}")
async def get_org_compliance_status(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    statuses = await service.get_org_compliance_status(org_id)
    return {"compliance_status": statuses}
