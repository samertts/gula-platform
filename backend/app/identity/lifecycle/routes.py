from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.lifecycle.services import (
    CitizenService,
    EnterpriseRegistrationService,
    GovernmentHRService,
    GuardianService,
    WorkforceService,
)

router = APIRouter(prefix="/lifecycle", tags=["NIAM Lifecycle"])

# ──────────────────────────────────────────────
#  Enterprise Registration
# ──────────────────────────────────────────────

@router.post("/enterprise/register")
async def start_enterprise_registration(
    organization_id: str,
    submitted_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.start_registration(organization_id, submitted_by)
    return {"reg_id": reg.reg_id, "uuid": reg.uuid}


@router.post("/enterprise/{reg_id}/validate-license")
async def validate_enterprise_license(
    reg_id: str,
    license_document: str,
    validated_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.validate_license(reg_id, license_document, validated_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/inspect")
async def submit_enterprise_inspection(
    reg_id: str,
    inspection_report: dict[str, Any],
    inspected_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.submit_inspection(reg_id, inspection_report, inspected_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/assess-risk")
async def assess_enterprise_risk(
    reg_id: str,
    risk_assessment: dict[str, Any],
    risk_score: int,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.assess_risk(reg_id, risk_assessment, risk_score)
    return {"reg_id": reg.reg_id, "risk_score": reg.risk_score}


@router.post("/enterprise/{reg_id}/approve")
async def approve_enterprise_registration(
    reg_id: str,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.approve_registration(reg_id, approved_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/reject")
async def reject_enterprise_registration(
    reg_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = await svc.reject_registration(reg_id, reason)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.get("/enterprise/{org_id}")
async def get_enterprise_status(
    org_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    status = await svc.get_registration_status(org_id)
    return {"status": status}

# ──────────────────────────────────────────────
#  Workforce
# ──────────────────────────────────────────────

@router.post("/workforce/request")
async def request_employee(
    request_id: str,
    request_type: str,
    requesting_org_id: str,
    requested_by: str,
    person_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.request_employee(
        request_id=request_id,
        request_type=request_type,
        requesting_org_id=requesting_org_id,
        requested_by=requested_by,
        person_id=person_id,
    )
    return {"request_id": req.request_id}


@router.post("/workforce/{request_id}/validate-national-id")
async def validate_workforce_national_id(
    request_id: str,
    national_id_hash: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.validate_national_id(request_id, national_id_hash)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/validate-license")
async def validate_workforce_license(
    request_id: str,
    license_number: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.validate_license(request_id, license_number)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/check-conflicts")
async def check_workforce_conflicts(
    request_id: str,
    conflict_report: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.check_conflicts(request_id, conflict_report)
    return {"request_id": req.request_id, "conflicts": req.conflict_report}


@router.post("/workforce/{request_id}/approve")
async def approve_workforce_request(
    request_id: str,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.approve_request(request_id, approved_by)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/activate")
async def activate_workforce_account(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.activate_account(request_id)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/terminate")
async def terminate_workforce_employment(
    request_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.terminate_employment(request_id, reason)
    return {"request_id": req.request_id, "status": req.status}


@router.get("/workforce/{request_id}")
async def get_workforce_request_status(
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    req = await svc.get_request_status(request_id)
    return {"request": req}


@router.post("/workforce/preserve-history/{person_id}")
async def preserve_workforce_history(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = WorkforceService(db)
    requests = await svc.preserve_history(person_id)
    return {"preserved": len(requests)}

# ──────────────────────────────────────────────
#  Government HR
# ──────────────────────────────────────────────

@router.post("/government/appointments")
async def create_government_appointment(
    appointment_id: str,
    person_id: str,
    organization_id: str,
    hr_reference: str,
    appointment_type: str,
    position: Optional[str] = None,
    grade: Optional[str] = None,
    salary_scale: Optional[str] = None,
    department: Optional[str] = None,
    start_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.create_appointment(
        appointment_id=appointment_id,
        person_id=person_id,
        organization_id=organization_id,
        hr_reference=hr_reference,
        appointment_type=appointment_type,
        position=position,
        grade=grade,
        salary_scale=salary_scale,
        department=department,
        start_date=start_date,
    )
    return {"appointment_id": appt.appointment_id}


@router.post("/government/appointments/{appointment_id}/approve")
async def approve_government_appointment(
    appointment_id: str,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.approve_appointment(appointment_id, approved_by)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/create-identity")
async def create_government_identity(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.create_identity(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/issue-credential")
async def issue_government_credential(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.issue_credential(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/activate")
async def activate_government_account(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.activate_account(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/assign-permissions")
async def assign_government_permissions(
    appointment_id: str,
    permissions: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.assign_permissions(appointment_id, permissions)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/promote")
async def promote_government_employee(
    appointment_id: str,
    new_position: str,
    new_grade: str,
    promoted_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.promote(
        appointment_id=appointment_id,
        new_position=new_position,
        new_grade=new_grade,
        promoted_by=promoted_by,
    )
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/transfer")
async def transfer_government_employee(
    appointment_id: str,
    new_org_id: Optional[str] = None,
    new_dept: Optional[str] = None,
    transferred_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.transfer(
        appointment_id=appointment_id,
        new_org_id=new_org_id,
        new_dept=new_dept,
        transferred_by=transferred_by,
    )
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/retire")
async def retire_government_employee(
    appointment_id: str,
    retirement_date: datetime,
    db: AsyncSession = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = await svc.retire(appointment_id, retirement_date)
    return {"appointment_id": appt.appointment_id, "status": appt.status}

# ──────────────────────────────────────────────
#  Citizen Lifecycle
# ──────────────────────────────────────────────

@router.post("/citizen/register")
async def register_citizen(
    person_id: str,
    citizen_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.register_citizen(person_id, citizen_id=citizen_id)
    return {"citizen_id": citizen.citizen_id}


@router.post("/citizen/{citizen_id}/send-otp")
async def send_citizen_otp(
    citizen_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.send_otp(citizen_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/verify-otp")
async def verify_citizen_otp(
    citizen_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.verify_otp(citizen_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/verify-identity")
async def verify_citizen_identity(
    citizen_id: str,
    verified_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.verify_identity(citizen_id, verified_by)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/issue-health-id")
async def issue_health_id(
    citizen_id: str,
    health_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.issue_health_id(citizen_id, health_id)
    return {"citizen_id": citizen.citizen_id, "health_id": citizen.health_id}


@router.post("/citizen/{citizen_id}/link-guardian")
async def link_citizen_guardian(
    citizen_id: str,
    guardian_person_id: str,
    relationship: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    guardian = await svc.link_guardian(
        citizen_id=citizen_id,
        guardian_person_id=guardian_person_id,
        relationship=relationship,
    )
    return {"guardian_id": guardian.guardian_id}


@router.post("/citizen/{citizen_id}/link-family")
async def link_citizen_family(
    citizen_id: str,
    relative_id: str,
    relationship: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    link = await svc.link_family_member(
        citizen_id=citizen_id,
        relative_id=relative_id,
        relationship=relationship,
    )
    return {"link_id": link.link_id}


@router.post("/citizen/{citizen_id}/consent")
async def record_citizen_consent(
    citizen_id: str,
    consent_type: str,
    granted_to: Optional[str] = None,
    scope: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    consent = await svc.record_consent(
        citizen_id=citizen_id,
        consent_type=consent_type,
        granted_to=granted_to,
        scope=scope,
    )
    return {"consent_id": consent.consent_id}


@router.post("/citizen/{citizen_id}/deactivate")
async def deactivate_citizen(
    citizen_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.deactivate(citizen_id, reason)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/record-death")
async def record_citizen_death(
    citizen_id: str,
    death_date: datetime,
    death_certificate_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = await svc.record_death(citizen_id, death_date, death_certificate_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.get("/citizen/{person_id}")
async def get_citizen_status(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = CitizenService(db)
    status = await svc.get_citizen_status(person_id)
    return {"status": status}

# ──────────────────────────────────────────────
#  Guardian Accounts
# ──────────────────────────────────────────────

@router.post("/guardians")
async def create_guardianship(
    guardian_id: str,
    guardian_person_id: str,
    dependent_person_id: str,
    relationship: str,
    guardian_type: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = await svc.create_guardianship(
        guardian_id=guardian_id,
        guardian_person_id=guardian_person_id,
        dependent_person_id=dependent_person_id,
        relationship=relationship,
        guardian_type=guardian_type,
    )
    return {"guardian_id": guardian.guardian_id}


@router.get("/guardians/dependents/{guardian_person_id}")
async def get_dependents(
    guardian_person_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    dependents = await svc.get_dependents(guardian_person_id)
    return {"dependents": [d.to_dict() for d in dependents]}


@router.get("/guardians/guardians/{dependent_person_id}")
async def get_guardians(
    dependent_person_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    guardians = await svc.get_guardians(dependent_person_id)
    return {"guardians": [g.to_dict() for g in guardians]}


@router.post("/guardians/{guardian_id}/terminate")
async def terminate_guardianship(
    guardian_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = await svc.terminate_guardianship(guardian_id, reason)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}


@router.post("/guardians/{guardian_id}/delegate-access")
async def delegate_guardian_access(
    guardian_id: str,
    access_permissions: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = await svc.delegate_access(guardian_id, access_permissions)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}


@router.post("/guardians/{guardian_id}/verify")
async def verify_guardianship(
    guardian_id: str,
    verified_by: str,
    db: AsyncSession = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = await svc.verify_guardianship(guardian_id, verified_by)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}
