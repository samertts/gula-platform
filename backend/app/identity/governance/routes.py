from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db

from .services import (
    AppealService,
    GovernanceService,
    PolicyApprovalService,
    RegistryService,
    SuspensionService,
)

router = APIRouter(prefix="/governance", tags=["NIAM Governance"])


# ── Authorities ────────────────────────────────────────────────────────────────


@router.post("/authorities")
def create_authority(
    authority_id: str,
    name_en: str,
    name_ar: str | None = None,
    authority_type: str = "identity_authority",
    jurisdiction: str = "national",
    parent_authority_id: str | None = None,
    contact_email: str | None = None,
    established_date: datetime | None = None,
    accredited_by: str | None = None,
    accreditation_expires: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.create_authority(
        authority_id=authority_id,
        name_en=name_en,
        name_ar=name_ar,
        authority_type=authority_type,
        jurisdiction=jurisdiction,
        parent_authority_id=parent_authority_id,
        contact_email=contact_email,
        established_date=established_date,
        accredited_by=accredited_by,
        accreditation_expires=accreditation_expires,
    )
    return {
        "uuid": entity.uuid,
        "id": entity.id,
        "authority_id": entity.authority_id,
        "status": entity.status,
    }


@router.get("/authorities")
def list_authorities(
    authority_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    authorities = service.list_authorities(authority_type=authority_type)
    return [
        {
            "uuid": a.uuid,
            "authority_id": a.authority_id,
            "name_en": a.name_en,
            "name_ar": a.name_ar,
            "authority_type": a.authority_type,
            "jurisdiction": a.jurisdiction,
            "status": a.status,
        }
        for a in authorities
    ]


@router.get("/authorities/{authority_id}")
def get_authority(
    authority_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.get_authority(authority_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.post("/authorities/{authority_id}/suspend")
def suspend_authority(
    authority_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.suspend_authority(authority_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "authority_id": entity.authority_id, "status": entity.status}


@router.post("/authorities/{authority_id}/activate")
def activate_authority(
    authority_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.activate_authority(authority_id)
    if not entity:
        return {"error": "not_found"}
    return {"uuid": entity.uuid, "authority_id": entity.authority_id, "status": entity.status}


# ── Councils ───────────────────────────────────────────────────────────────────


@router.post("/councils")
def create_council(
    council_id: str,
    name_en: str,
    name_ar: str | None = None,
    council_type: str = "governance",
    authority_id: str | None = None,
    chairperson_id: str | None = None,
    members: list[Any] | None = None,
    meeting_frequency: str | None = None,
    last_meeting: datetime | None = None,
    next_meeting: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.create_council(
        council_id=council_id,
        name_en=name_en,
        name_ar=name_ar,
        council_type=council_type,
        authority_id=authority_id,
        chairperson_id=chairperson_id,
        members=members,
        meeting_frequency=meeting_frequency,
        last_meeting=last_meeting,
        next_meeting=next_meeting,
    )
    return {
        "uuid": entity.uuid,
        "id": entity.id,
        "council_id": entity.council_id,
        "status": entity.status,
    }


@router.get("/councils")
def list_councils(
    authority_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    councils = service.list_councils(authority_id=authority_id)
    return [
        {
            "uuid": c.uuid,
            "council_id": c.council_id,
            "name_en": c.name_en,
            "name_ar": c.name_ar,
            "council_type": c.council_type,
            "status": c.status,
        }
        for c in councils
    ]


@router.get("/councils/{council_id}")
def get_council(
    council_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.get_council(council_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


# ── Review Boards ──────────────────────────────────────────────────────────────


@router.post("/review-boards")
def create_review_board(
    board_id: str,
    name_en: str,
    name_ar: str | None = None,
    board_type: str | None = None,
    authority_id: str | None = None,
    chairperson_id: str | None = None,
    members: list[Any] | None = None,
    quorum_size: int = 3,
    meeting_schedule: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = GovernanceService(db)
    entity = service.create_review_board(
        board_id=board_id,
        name_en=name_en,
        name_ar=name_ar,
        board_type=board_type,
        authority_id=authority_id,
        chairperson_id=chairperson_id,
        members=members,
        quorum_size=quorum_size,
        meeting_schedule=meeting_schedule,
    )
    return {
        "uuid": entity.uuid,
        "id": entity.id,
        "board_id": entity.board_id,
        "status": entity.status,
    }


# ── Policy Approvals ───────────────────────────────────────────────────────────


@router.post("/policy-approvals")
def submit_policy_approval(
    policy_id: str,
    submitted_by: str,
    db: AsyncSession = Depends(get_db),
):
    service = PolicyApprovalService(db)
    entity = service.submit_policy(
        policy_id=policy_id,
        submitted_by=submitted_by,
    )
    return {
        "uuid": entity.uuid,
        "workflow_id": entity.workflow_id,
        "policy_id": entity.policy_id,
        "status": entity.status,
    }


@router.get("/policy-approvals/pending/{reviewer_id}")
def get_pending_policy_approvals(
    reviewer_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = PolicyApprovalService(db)
    pending = service.get_pending_approvals(reviewer_id)
    return [
        {
            "uuid": p.uuid,
            "workflow_id": p.workflow_id,
            "policy_id": p.policy_id,
            "submitted_by": p.submitted_by,
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
            "status": p.status,
            "version": p.version,
        }
        for p in pending
    ]


@router.post("/policy-approvals/{workflow_id}/approve")
def approve_policy(
    workflow_id: str,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    service = PolicyApprovalService(db)
    entity = service.approve_policy(workflow_id, approved_by)
    if not entity:
        return {"error": "not_found"}
    return {
        "workflow_id": entity.workflow_id,
        "status": entity.status,
        "approved_by": entity.approved_by,
    }


@router.post("/policy-approvals/{workflow_id}/reject")
def reject_policy(
    workflow_id: str,
    rejected_by: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    service = PolicyApprovalService(db)
    entity = service.reject_policy(workflow_id, rejected_by, reason)
    if not entity:
        return {"error": "not_found"}
    return {
        "workflow_id": entity.workflow_id,
        "status": entity.status,
        "rejected_by": entity.rejected_by,
    }


# ── Appeals ────────────────────────────────────────────────────────────────────


@router.post("/appeals")
def submit_appeal(
    appeal_id: str,
    appellant_person_id: str,
    identity_id: str,
    appeal_type: str = "suspension",
    reason: str | None = None,
    supporting_documents: list[Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AppealService(db)
    entity = service.submit_appeal(
        appeal_id=appeal_id,
        appellant_person_id=appellant_person_id,
        identity_id=identity_id,
        appeal_type=appeal_type,
        reason=reason,
        supporting_documents=supporting_documents,
    )
    return {
        "uuid": entity.uuid,
        "appeal_id": entity.appeal_id,
        "status": entity.status,
    }


@router.get("/appeals")
def list_appeals(
    status: str | None = None,
    person_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AppealService(db)
    appeals = service.get_appeals(status=status, person_id=person_id)
    return [
        {
            "uuid": a.uuid,
            "appeal_id": a.appeal_id,
            "appellant_person_id": a.appellant_person_id,
            "appeal_type": a.appeal_type,
            "status": a.status,
            "decision": a.decision,
        }
        for a in appeals
    ]


@router.post("/appeals/{appeal_id}/assign")
def assign_appeal_to_council(
    appeal_id: str,
    council_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = AppealService(db)
    entity = service.assign_to_council(appeal_id, council_id)
    if not entity:
        return {"error": "not_found"}
    return {"appeal_id": entity.appeal_id, "council_id": entity.council_id, "status": entity.status}


@router.post("/appeals/{appeal_id}/decide")
def decide_appeal(
    appeal_id: str,
    decision: str,
    decided_by: str,
    notes: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = AppealService(db)
    entity = service.make_decision(appeal_id, decision, decided_by, notes)
    if not entity:
        return {"error": "not_found"}
    return {"appeal_id": entity.appeal_id, "decision": entity.decision, "status": entity.status}


# ── Suspensions ────────────────────────────────────────────────────────────────


@router.post("/suspensions")
def suspend_identity(
    person_id: str,
    identity_id: str,
    reason: str,
    severity: str = "medium",
    suspended_by: str | None = None,
    duration_hours: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = SuspensionService(db)
    entity = service.suspend_identity(
        person_id=person_id,
        identity_id=identity_id,
        reason=reason,
        severity=severity,
        suspended_by=suspended_by,
        duration_hours=duration_hours,
    )
    return {
        "uuid": entity.uuid,
        "suspension_id": entity.suspension_id,
        "status": entity.status,
        "expires_at": entity.expires_at.isoformat() if entity.expires_at else None,
    }


@router.post("/suspensions/{suspension_id}/lift")
def lift_suspension(
    suspension_id: str,
    lifted_by: str,
    reason: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = SuspensionService(db)
    entity = service.lift_suspension(suspension_id, lifted_by, reason)
    if not entity:
        return {"error": "not_found"}
    return {
        "suspension_id": entity.suspension_id,
        "status": entity.status,
        "lifted_by": entity.lifted_by,
    }


@router.get("/suspensions/active")
def list_active_suspensions(
    db: AsyncSession = Depends(get_db),
):
    service = SuspensionService(db)
    suspensions = service.get_active_suspensions()
    return [
        {
            "uuid": s.uuid,
            "suspension_id": s.suspension_id,
            "person_id": s.person_id,
            "severity": s.severity,
            "reason": s.reason,
            "suspended_at": s.suspended_at.isoformat() if s.suspended_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in suspensions
    ]


@router.get("/suspensions/history/{person_id}")
def get_suspension_history(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = SuspensionService(db)
    history = service.get_suspension_history(person_id)
    return [
        {
            "uuid": s.uuid,
            "suspension_id": s.suspension_id,
            "severity": s.severity,
            "reason": s.reason,
            "suspended_at": s.suspended_at.isoformat() if s.suspended_at else None,
            "lifted_at": s.lifted_at.isoformat() if s.lifted_at else None,
            "status": s.status,
        }
        for s in history
    ]


# ── Registry ───────────────────────────────────────────────────────────────────


@router.post("/registry")
def register_identity(
    person_id: str,
    identity_id: str,
    registry_type: str = "citizen",
    registered_by: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = RegistryService(db)
    entity = service.register_identity(
        person_id=person_id,
        identity_id=identity_id,
        registry_type=registry_type,
        registered_by=registered_by,
    )
    return {
        "uuid": entity.uuid,
        "registry_id": entity.registry_id,
        "registration_number": entity.registration_number,
        "status": entity.status,
    }


@router.get("/registry/{person_id}")
def get_registration(
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = RegistryService(db)
    entity = service.get_registration(person_id)
    if not entity:
        return {"error": "not_found"}
    return entity.to_dict()


@router.post("/registry/certify")
def certify_identity(
    certification_id: str,
    person_id: str,
    organization_id: str | None = None,
    certifying_authority_id: str | None = None,
    certification_type: str | None = None,
    certification_number: str | None = None,
    issue_date: datetime | None = None,
    expiry_date: datetime | None = None,
    verified_by: str | None = None,
    verification_method: str | None = None,
    digital_signature: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = RegistryService(db)
    entity = service.certify_identity(
        certification_id=certification_id,
        person_id=person_id,
        organization_id=organization_id,
        certifying_authority_id=certifying_authority_id,
        certification_type=certification_type,
        certification_number=certification_number,
        issue_date=issue_date,
        expiry_date=expiry_date,
        verified_by=verified_by,
        verification_method=verification_method,
        digital_signature=digital_signature,
    )
    return {
        "uuid": entity.uuid,
        "certification_id": entity.certification_id,
        "certification_number": entity.certification_number,
        "status": entity.status,
    }


@router.post("/registry/certification/{certification_id}/revoke")
def revoke_certification(
    certification_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    service = RegistryService(db)
    entity = service.revoke_certification(certification_id, reason)
    if not entity:
        return {"error": "not_found"}
    return {"certification_id": entity.certification_id, "status": entity.status}
