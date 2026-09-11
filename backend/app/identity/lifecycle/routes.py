from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
def start_enterprise_registration(
    organization_id: str,
    submitted_by: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.start_registration(organization_id, submitted_by)
    return {"reg_id": reg.reg_id, "uuid": reg.uuid}


@router.post("/enterprise/{reg_id}/validate-license")
def validate_enterprise_license(
    reg_id: str,
    license_document: str,
    validated_by: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.validate_license(reg_id, license_document, validated_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/inspect")
def submit_enterprise_inspection(
    reg_id: str,
    inspection_report: dict[str, Any],
    inspected_by: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.submit_inspection(reg_id, inspection_report, inspected_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/assess-risk")
def assess_enterprise_risk(
    reg_id: str,
    risk_assessment: dict[str, Any],
    risk_score: int,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.assess_risk(reg_id, risk_assessment, risk_score)
    return {"reg_id": reg.reg_id, "risk_score": reg.risk_score}


@router.post("/enterprise/{reg_id}/approve")
def approve_enterprise_registration(
    reg_id: str,
    approved_by: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.approve_registration(reg_id, approved_by)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.post("/enterprise/{reg_id}/reject")
def reject_enterprise_registration(
    reg_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    reg = svc.reject_registration(reg_id, reason)
    return {"reg_id": reg.reg_id, "status": reg.status}


@router.get("/enterprise/{org_id}")
def get_enterprise_status(
    org_id: str,
    db: Session = Depends(get_db),
):
    svc = EnterpriseRegistrationService(db)
    status = svc.get_registration_status(org_id)
    return {"status": status}

# ──────────────────────────────────────────────
#  Workforce
# ──────────────────────────────────────────────

@router.post("/workforce/request")
def request_employee(
    request_id: str,
    request_type: str,
    requesting_org_id: str,
    requested_by: str,
    person_id: str | None = None,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.request_employee(
        request_id=request_id,
        request_type=request_type,
        requesting_org_id=requesting_org_id,
        requested_by=requested_by,
        person_id=person_id,
    )
    return {"request_id": req.request_id}


@router.post("/workforce/{request_id}/validate-national-id")
def validate_workforce_national_id(
    request_id: str,
    national_id_hash: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.validate_national_id(request_id, national_id_hash)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/validate-license")
def validate_workforce_license(
    request_id: str,
    license_number: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.validate_license(request_id, license_number)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/check-conflicts")
def check_workforce_conflicts(
    request_id: str,
    conflict_report: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.check_conflicts(request_id, conflict_report)
    return {"request_id": req.request_id, "conflicts": req.conflict_report}


@router.post("/workforce/{request_id}/approve")
def approve_workforce_request(
    request_id: str,
    approved_by: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.approve_request(request_id, approved_by)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/activate")
def activate_workforce_account(
    request_id: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.activate_account(request_id)
    return {"request_id": req.request_id, "status": req.status}


@router.post("/workforce/{request_id}/terminate")
def terminate_workforce_employment(
    request_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.terminate_employment(request_id, reason)
    return {"request_id": req.request_id, "status": req.status}


@router.get("/workforce/{request_id}")
def get_workforce_request_status(
    request_id: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    req = svc.get_request_status(request_id)
    return {"request": req}


@router.post("/workforce/preserve-history/{person_id}")
def preserve_workforce_history(
    person_id: str,
    db: Session = Depends(get_db),
):
    svc = WorkforceService(db)
    requests = svc.preserve_history(person_id)
    return {"preserved": len(requests)}

# ──────────────────────────────────────────────
#  Government HR
# ──────────────────────────────────────────────

@router.post("/government/appointments")
def create_government_appointment(
    appointment_id: str,
    person_id: str,
    organization_id: str,
    hr_reference: str,
    appointment_type: str,
    position: str | None = None,
    grade: str | None = None,
    salary_scale: str | None = None,
    department: str | None = None,
    start_date: datetime | None = None,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.create_appointment(
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
def approve_government_appointment(
    appointment_id: str,
    approved_by: str,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.approve_appointment(appointment_id, approved_by)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/create-identity")
def create_government_identity(
    appointment_id: str,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.create_identity(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/issue-credential")
def issue_government_credential(
    appointment_id: str,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.issue_credential(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/activate")
def activate_government_account(
    appointment_id: str,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.activate_account(appointment_id)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/assign-permissions")
def assign_government_permissions(
    appointment_id: str,
    permissions: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.assign_permissions(appointment_id, permissions)
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/promote")
def promote_government_employee(
    appointment_id: str,
    new_position: str,
    new_grade: str,
    promoted_by: str | None = None,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.promote(
        appointment_id=appointment_id,
        new_position=new_position,
        new_grade=new_grade,
        promoted_by=promoted_by,
    )
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/transfer")
def transfer_government_employee(
    appointment_id: str,
    new_org_id: str | None = None,
    new_dept: str | None = None,
    transferred_by: str | None = None,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.transfer(
        appointment_id=appointment_id,
        new_org_id=new_org_id,
        new_dept=new_dept,
        transferred_by=transferred_by,
    )
    return {"appointment_id": appt.appointment_id, "status": appt.status}


@router.post("/government/appointments/{appointment_id}/retire")
def retire_government_employee(
    appointment_id: str,
    retirement_date: datetime,
    db: Session = Depends(get_db),
):
    svc = GovernmentHRService(db)
    appt = svc.retire(appointment_id, retirement_date)
    return {"appointment_id": appt.appointment_id, "status": appt.status}

# ──────────────────────────────────────────────
#  Citizen Lifecycle
# ──────────────────────────────────────────────

@router.post("/citizen/register")
def register_citizen(
    person_id: str,
    citizen_id: str | None = None,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.register_citizen(person_id, citizen_id=citizen_id)
    return {"citizen_id": citizen.citizen_id}


@router.post("/citizen/{citizen_id}/send-otp")
def send_citizen_otp(
    citizen_id: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.send_otp(citizen_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/verify-otp")
def verify_citizen_otp(
    citizen_id: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.verify_otp(citizen_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/verify-identity")
def verify_citizen_identity(
    citizen_id: str,
    verified_by: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.verify_identity(citizen_id, verified_by)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/issue-health-id")
def issue_health_id(
    citizen_id: str,
    health_id: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.issue_health_id(citizen_id, health_id)
    return {"citizen_id": citizen.citizen_id, "health_id": citizen.health_id}


@router.post("/citizen/{citizen_id}/link-guardian")
def link_citizen_guardian(
    citizen_id: str,
    guardian_person_id: str,
    relationship: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    guardian = svc.link_guardian(
        citizen_id=citizen_id,
        guardian_person_id=guardian_person_id,
        relationship=relationship,
    )
    return {"guardian_id": guardian.guardian_id}


@router.post("/citizen/{citizen_id}/link-family")
def link_citizen_family(
    citizen_id: str,
    relative_id: str,
    relationship: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    link = svc.link_family_member(
        citizen_id=citizen_id,
        relative_id=relative_id,
        relationship=relationship,
    )
    return {"link_id": link.link_id}


@router.post("/citizen/{citizen_id}/consent")
def record_citizen_consent(
    citizen_id: str,
    consent_type: str,
    granted_to: str | None = None,
    scope: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    consent = svc.record_consent(
        citizen_id=citizen_id,
        consent_type=consent_type,
        granted_to=granted_to,
        scope=scope,
    )
    return {"consent_id": consent.consent_id}


@router.post("/citizen/{citizen_id}/deactivate")
def deactivate_citizen(
    citizen_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.deactivate(citizen_id, reason)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.post("/citizen/{citizen_id}/record-death")
def record_citizen_death(
    citizen_id: str,
    death_date: datetime,
    death_certificate_id: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    citizen = svc.record_death(citizen_id, death_date, death_certificate_id)
    return {"citizen_id": citizen.citizen_id, "status": citizen.status}


@router.get("/citizen/{person_id}")
def get_citizen_status(
    person_id: str,
    db: Session = Depends(get_db),
):
    svc = CitizenService(db)
    status = svc.get_citizen_status(person_id)
    return {"status": status}

# ──────────────────────────────────────────────
#  Guardian Accounts
# ──────────────────────────────────────────────

@router.post("/guardians")
def create_guardianship(
    guardian_id: str,
    guardian_person_id: str,
    dependent_person_id: str,
    relationship: str,
    guardian_type: str,
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = svc.create_guardianship(
        guardian_id=guardian_id,
        guardian_person_id=guardian_person_id,
        dependent_person_id=dependent_person_id,
        relationship=relationship,
        guardian_type=guardian_type,
    )
    return {"guardian_id": guardian.guardian_id}


@router.get("/guardians/dependents/{guardian_person_id}")
def get_dependents(
    guardian_person_id: str,
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    dependents = svc.get_dependents(guardian_person_id)
    return {"dependents": [d.to_dict() for d in dependents]}


@router.get("/guardians/guardians/{dependent_person_id}")
def get_guardians(
    dependent_person_id: str,
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    guardians = svc.get_guardians(dependent_person_id)
    return {"guardians": [g.to_dict() for g in guardians]}


@router.post("/guardians/{guardian_id}/terminate")
def terminate_guardianship(
    guardian_id: str,
    reason: str,
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = svc.terminate_guardianship(guardian_id, reason)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}


@router.post("/guardians/{guardian_id}/delegate-access")
def delegate_guardian_access(
    guardian_id: str,
    access_permissions: dict[str, Any],
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = svc.delegate_access(guardian_id, access_permissions)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}


@router.post("/guardians/{guardian_id}/verify")
def verify_guardianship(
    guardian_id: str,
    verified_by: str,
    db: Session = Depends(get_db),
):
    svc = GuardianService(db)
    guardian = svc.verify_guardianship(guardian_id, verified_by)
    return {"guardian_id": guardian.guardian_id, "status": guardian.status}
