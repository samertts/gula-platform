from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.admin.services import EnterprisePortalService

router = APIRouter(prefix="/admin", tags=["NIAM Admin"])


@router.post("/portals")
async def create_portal(
    org_id: str,
    name: str,
    portal_type: str,
    created_by: str,
    features: str = "{}",
    db: AsyncSession = Depends(get_db),
):
    import json
    service = EnterprisePortalService(db)
    portal = await service.create_portal(
        org_id=org_id,
        name=name,
        portal_type=portal_type,
        features=json.loads(features) if features else None,
        created_by=created_by,
    )
    return {"portal": portal.to_dict()}


@router.get("/portals/organization/{org_id}")
async def list_org_portals(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    portals = await service.get_portals_for_org(org_id)
    return {"portals": [p.to_dict() for p in portals]}


@router.post("/portals/{portal_id}/branches")
async def add_branch(
    portal_id: str,
    org_id: str,
    name_en: str,
    name_ar: str,
    address: str = "",
    phone: str = "",
    email: str = "",
    manager_person_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    branch = await service.add_branch(
        portal_id=portal_id,
        org_id=org_id,
        name_en=name_en,
        name_ar=name_ar,
        address=address or None,
        phone=phone or None,
        email=email or None,
        manager_person_id=manager_person_id or None,
    )
    return {"branch": branch.to_dict()}


@router.post("/branches/{branch_id}/facilities")
async def add_facility(
    branch_id: str,
    org_id: str,
    name_en: str,
    name_ar: str,
    facility_type: str,
    license_number: str = "",
    accreditation: str = "",
    address: str = "",
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    facility = await service.add_facility(
        branch_id=branch_id,
        org_id=org_id,
        name_en=name_en,
        name_ar=name_ar,
        facility_type=facility_type,
        license_number=license_number or None,
        accreditation=accreditation or None,
        address=address or None,
    )
    return {"facility": facility.to_dict()}


@router.post("/facilities/{facility_id}/departments")
async def add_department(
    facility_id: str,
    name_en: str,
    name_ar: str,
    dept_type: str = "",
    head_person_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    dept = await service.add_department(
        facility_id=facility_id,
        name_en=name_en,
        name_ar=name_ar,
        dept_type=dept_type or None,
        head_person_id=head_person_id or None,
    )
    return {"department": dept.to_dict()}


@router.get("/subscriptions/{org_id}")
async def get_subscription(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    sub = await service.get_subscription(org_id)
    if not sub:
        return {"subscription": None}
    return {"subscription": sub.to_dict()}


@router.post("/subscriptions")
async def create_subscription(
    org_id: str,
    plan_type: str,
    user_limit: int = 0,
    storage_limit: int = 0,
    api_call_limit: int = 0,
    billing_cycle: str = "monthly",
    billing_amount: int = 0,
    currency: str = "IQD",
    auto_renew: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    sub = await service.manage_subscription(
        org_id=org_id,
        plan_type=plan_type,
        user_limit=user_limit or None,
        storage_limit=storage_limit or None,
        api_call_limit=api_call_limit or None,
        billing_cycle=billing_cycle,
        billing_amount=billing_amount or None,
        currency=currency,
        auto_renew=auto_renew,
    )
    return {"subscription": sub.to_dict()}


@router.put("/subscriptions/{sub_id}")
async def update_subscription(
    sub_id: str,
    plan_type: str = "",
    status: str = "",
    billing_cycle: str = "",
    billing_amount: int = 0,
    auto_renew: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    kwargs: dict = {}
    if plan_type:
        kwargs["plan_type"] = plan_type
    if status:
        kwargs["status"] = status
    if billing_cycle:
        kwargs["billing_cycle"] = billing_cycle
    if billing_amount:
        kwargs["billing_amount"] = billing_amount
    kwargs["auto_renew"] = auto_renew
    sub = await service.update_subscription(sub_id, **kwargs)
    if not sub:
        return {"error": "not_found"}
    return {"subscription": sub.to_dict()}


@router.post("/fhir-connections")
async def create_fhir_connection(
    org_id: str,
    name: str,
    fhir_version: str,
    base_url: str,
    auth_type: str,
    credentials_encrypted: str = "",
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    conn = await service.create_fhir_connection(
        org_id=org_id,
        name=name,
        fhir_version=fhir_version,
        base_url=base_url,
        auth_type=auth_type,
        credentials_encrypted=credentials_encrypted or None,
    )
    return {"fhir_connection": conn.to_dict()}


@router.get("/fhir-connections/organization/{org_id}")
async def list_fhir_connections(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    conns = await service.get_fhir_connections_for_org(org_id)
    return {"fhir_connections": [c.to_dict() for c in conns]}


@router.post("/fhir-connections/{conn_id}/test")
async def test_fhir_connection(
    conn_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    result = await service.test_fhir_connection(conn_id)
    return result


@router.get("/audit-log/{org_id}")
async def get_audit_log(
    org_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = EnterprisePortalService(db)
    entries = await service.get_audit_log(org_id, limit=limit)
    return {"audit_log": [e.to_dict() for e in entries]}
