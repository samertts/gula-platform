from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.governance.models import (
    DigitalIdentityCouncil,
    IdentityAppeal,
    IdentityAuthority,
    IdentityCertificationRegistry,
    IdentityReviewBoard,
    IdentitySuspension,
    NationalIdentityRegistry,
    PolicyApprovalWorkflow,
)


def _now() -> datetime:
    return datetime.now(UTC)


class GovernanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Authorities ───────────────────────────────────────────────────────────

    def create_authority(
        self,
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
    ) -> IdentityAuthority:
        authority = IdentityAuthority(
            uuid=str(uuid.uuid4()),
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
            status="active",
            is_active=True,
        )
        self.session.add(authority)
        self.session.flush()
        return authority

    def get_authority(self, authority_id: str) -> IdentityAuthority | None:
        stmt = select(IdentityAuthority).where(
            IdentityAuthority.authority_id == authority_id,
            IdentityAuthority.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def list_authorities(
        self,
        authority_type: str | None = None,
    ) -> list[IdentityAuthority]:
        stmt = select(IdentityAuthority).where(
            IdentityAuthority.is_active.is_(True),
        )
        if authority_type:
            stmt = stmt.where(IdentityAuthority.authority_type == authority_type)
        stmt = stmt.order_by(IdentityAuthority.name_en)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def suspend_authority(self, authority_id: str) -> IdentityAuthority | None:
        stmt = select(IdentityAuthority).where(
            IdentityAuthority.authority_id == authority_id,
            IdentityAuthority.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        authority = result.scalar_one_or_none()
        if authority:
            authority.status = "suspended"
            authority.is_active = False
            authority.updated_at = _now()
            self.session.flush()
        return authority

    def activate_authority(self, authority_id: str) -> IdentityAuthority | None:
        stmt = select(IdentityAuthority).where(
            IdentityAuthority.authority_id == authority_id,
        )
        result = self.session.execute(stmt)
        authority = result.scalar_one_or_none()
        if authority:
            authority.status = "active"
            authority.is_active = True
            authority.updated_at = _now()
            self.session.flush()
        return authority

    # ── Councils ──────────────────────────────────────────────────────────────

    def create_council(
        self,
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
    ) -> DigitalIdentityCouncil:
        council = DigitalIdentityCouncil(
            uuid=str(uuid.uuid4()),
            council_id=council_id,
            name_en=name_en,
            name_ar=name_ar,
            council_type=council_type,
            authority_id=authority_id,
            chairperson_id=chairperson_id or "",
            members=members,
            meeting_frequency=meeting_frequency,
            last_meeting=last_meeting,
            next_meeting=next_meeting,
            status="active",
            is_active=True,
        )
        self.session.add(council)
        self.session.flush()
        return council

    def get_council(self, council_id: str) -> DigitalIdentityCouncil | None:
        stmt = select(DigitalIdentityCouncil).where(
            DigitalIdentityCouncil.council_id == council_id,
            DigitalIdentityCouncil.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def list_councils(
        self,
        authority_id: str | None = None,
    ) -> list[DigitalIdentityCouncil]:
        stmt = select(DigitalIdentityCouncil).where(
            DigitalIdentityCouncil.is_active.is_(True),
        )
        if authority_id:
            stmt = stmt.where(DigitalIdentityCouncil.authority_id == authority_id)
        stmt = stmt.order_by(DigitalIdentityCouncil.name_en)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Review Boards ─────────────────────────────────────────────────────────

    def create_review_board(
        self,
        board_id: str,
        name_en: str,
        name_ar: str | None = None,
        board_type: str | None = None,
        authority_id: str | None = None,
        chairperson_id: str | None = None,
        members: list[Any] | None = None,
        quorum_size: int = 3,
        meeting_schedule: dict[str, Any] | None = None,
    ) -> IdentityReviewBoard:
        board = IdentityReviewBoard(
            uuid=str(uuid.uuid4()),
            board_id=board_id,
            name_en=name_en,
            name_ar=name_ar,
            board_type=board_type or "",
            authority_id=authority_id,
            chairperson_id=chairperson_id or "",
            members=members,
            quorum_size=quorum_size,
            meeting_schedule=meeting_schedule,
            case_load=0,
            status="active",
            is_active=True,
        )
        self.session.add(board)
        self.session.flush()
        return board

    def get_review_board(self, board_id: str) -> IdentityReviewBoard | None:
        stmt = select(IdentityReviewBoard).where(
            IdentityReviewBoard.board_id == board_id,
            IdentityReviewBoard.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()


class PolicyApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def submit_policy(
        self,
        policy_id: str,
        submitted_by: str,
    ) -> PolicyApprovalWorkflow:
        workflow = PolicyApprovalWorkflow(
            uuid=str(uuid.uuid4()),
            workflow_id=str(uuid.uuid4()).replace("-", "")[:16],
            policy_id=policy_id,
            submitted_by=submitted_by,
            submitted_at=_now(),
            status="draft",
            version=1,
            is_active=True,
        )
        self.session.add(workflow)
        self.session.flush()
        return workflow

    def review_policy(
        self,
        workflow_id: str,
        reviewer: str,
        decision: str,
        comments: str | None = None,
    ) -> PolicyApprovalWorkflow | None:
        stmt = select(PolicyApprovalWorkflow).where(
            PolicyApprovalWorkflow.workflow_id == workflow_id,
            PolicyApprovalWorkflow.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            return None
        reviewers = workflow.reviewers or []
        if reviewer not in reviewers:
            reviewers.append(reviewer)
        workflow.reviewers = reviewers
        review_comments = workflow.review_comments or []
        review_comments.append(
            {
                "reviewer": reviewer,
                "decision": decision,
                "comments": comments,
                "at": _now().isoformat(),
            }
        )
        workflow.review_comments = review_comments
        workflow.status = "review"
        workflow.updated_at = _now()
        self.session.flush()
        return workflow

    def approve_policy(
        self,
        workflow_id: str,
        approved_by: str,
    ) -> PolicyApprovalWorkflow | None:
        stmt = select(PolicyApprovalWorkflow).where(
            PolicyApprovalWorkflow.workflow_id == workflow_id,
            PolicyApprovalWorkflow.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            return None
        workflow.status = "approved"
        workflow.approved_by = approved_by
        workflow.approved_at = _now()
        workflow.updated_at = _now()
        self.session.flush()
        return workflow

    def reject_policy(
        self,
        workflow_id: str,
        rejected_by: str,
        reason: str,
    ) -> PolicyApprovalWorkflow | None:
        stmt = select(PolicyApprovalWorkflow).where(
            PolicyApprovalWorkflow.workflow_id == workflow_id,
            PolicyApprovalWorkflow.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            return None
        workflow.status = "rejected"
        workflow.rejected_by = rejected_by
        workflow.rejected_at = _now()
        workflow.rejection_reason = reason
        workflow.updated_at = _now()
        self.session.flush()
        return workflow

    def deploy_policy(
        self,
        workflow_id: str,
    ) -> PolicyApprovalWorkflow | None:
        stmt = select(PolicyApprovalWorkflow).where(
            PolicyApprovalWorkflow.workflow_id == workflow_id,
            PolicyApprovalWorkflow.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            return None
        workflow.status = "deployed"
        workflow.updated_at = _now()
        self.session.flush()
        return workflow

    def get_pending_approvals(
        self,
        reviewer_id: str,
    ) -> list[PolicyApprovalWorkflow]:
        stmt = select(PolicyApprovalWorkflow).where(
            PolicyApprovalWorkflow.status.in_(["draft", "review"]),
            PolicyApprovalWorkflow.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        all_pending = list(result.scalars().all())
        pending = []
        for wf in all_pending:
            reviewers = wf.reviewers or []
            if reviewer_id in reviewers or not reviewers:
                pending.append(wf)
        return pending


class AppealService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def submit_appeal(
        self,
        appeal_id: str,
        appellant_person_id: str,
        identity_id: str,
        appeal_type: str = "suspension",
        reason: str | None = None,
        supporting_documents: list[Any] | None = None,
    ) -> IdentityAppeal:
        appeal = IdentityAppeal(
            uuid=str(uuid.uuid4()),
            appeal_id=appeal_id,
            appellant_person_id=appellant_person_id,
            identity_id=identity_id,
            appeal_type=appeal_type,
            reason=reason or "",
            supporting_documents=supporting_documents,
            status="submitted",
            is_active=True,
        )
        self.session.add(appeal)
        self.session.flush()
        return appeal

    def assign_to_council(
        self,
        appeal_id: str,
        council_id: str,
    ) -> IdentityAppeal | None:
        stmt = select(IdentityAppeal).where(
            IdentityAppeal.appeal_id == appeal_id,
            IdentityAppeal.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        appeal = result.scalar_one_or_none()
        if not appeal:
            return None
        appeal.council_id = council_id
        appeal.assigned_to = council_id
        appeal.status = "under_review"
        appeal.updated_at = _now()
        self.session.flush()
        return appeal

    def make_decision(
        self,
        appeal_id: str,
        decision: str,
        decided_by: str,
        notes: str | None = None,
    ) -> IdentityAppeal | None:
        stmt = select(IdentityAppeal).where(
            IdentityAppeal.appeal_id == appeal_id,
            IdentityAppeal.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        appeal = result.scalar_one_or_none()
        if not appeal:
            return None
        appeal.decision = decision
        appeal.decision_by = decided_by
        appeal.decision_at = _now()
        appeal.notes = notes
        appeal.status = "approved" if decision.lower() in ("approve", "approved") else "rejected"
        appeal.updated_at = _now()
        self.session.flush()
        return appeal

    def escalate_appeal(
        self,
        appeal_id: str,
        reason: str,
    ) -> IdentityAppeal | None:
        stmt = select(IdentityAppeal).where(
            IdentityAppeal.appeal_id == appeal_id,
            IdentityAppeal.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        appeal = result.scalar_one_or_none()
        if not appeal:
            return None
        appeal.status = "escalated"
        appeal.notes = (appeal.notes or "") + f"\n[ESCALATED] {reason}"
        appeal.updated_at = _now()
        self.session.flush()
        return appeal

    def get_appeals(
        self,
        status: str | None = None,
        person_id: str | None = None,
    ) -> list[IdentityAppeal]:
        stmt = select(IdentityAppeal).where(
            IdentityAppeal.is_active.is_(True),
        )
        if status:
            stmt = stmt.where(IdentityAppeal.status == status)
        if person_id:
            stmt = stmt.where(IdentityAppeal.appellant_person_id == person_id)
        stmt = stmt.order_by(IdentityAppeal.created_at.desc())
        result = self.session.execute(stmt)
        return list(result.scalars().all())


class SuspensionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def suspend_identity(
        self,
        person_id: str,
        identity_id: str,
        reason: str,
        severity: str = "medium",
        suspended_by: str | None = None,
        duration_hours: int | None = None,
    ) -> IdentitySuspension:
        now = _now()
        expires_at = None
        if duration_hours:
            expires_at = now + __import__("datetime").timedelta(hours=duration_hours)
        suspension = IdentitySuspension(
            uuid=str(uuid.uuid4()),
            suspension_id=str(uuid.uuid4()).replace("-", "")[:16],
            person_id=person_id,
            identity_id=identity_id,
            reason=reason,
            severity=severity,
            suspended_by=suspended_by or "",
            suspended_at=now,
            duration_hours=duration_hours,
            expires_at=expires_at,
            status="active",
            notification_sent=False,
            is_active=True,
        )
        self.session.add(suspension)
        self.session.flush()
        return suspension

    def lift_suspension(
        self,
        suspension_id: str,
        lifted_by: str,
        reason: str | None = None,
    ) -> IdentitySuspension | None:
        stmt = select(IdentitySuspension).where(
            IdentitySuspension.suspension_id == suspension_id,
            IdentitySuspension.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        suspension = result.scalar_one_or_none()
        if not suspension:
            return None
        suspension.status = "lifted"
        suspension.lifted_by = lifted_by
        suspension.lifted_at = _now()
        suspension.lift_reason = reason
        suspension.updated_at = _now()
        self.session.flush()
        return suspension

    def get_active_suspensions(self) -> list[IdentitySuspension]:
        stmt = select(IdentitySuspension).where(
            IdentitySuspension.status == "active",
            IdentitySuspension.is_active.is_(True),
        )
        stmt = stmt.order_by(IdentitySuspension.suspended_at.desc())
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_suspension_history(
        self,
        person_id: str,
    ) -> list[IdentitySuspension]:
        stmt = select(IdentitySuspension).where(
            IdentitySuspension.person_id == person_id,
            IdentitySuspension.is_active.is_(True),
        )
        stmt = stmt.order_by(IdentitySuspension.suspended_at.desc())
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def expire_suspensions(self) -> int:
        now = _now()
        stmt = (
            update(IdentitySuspension)
            .where(
                IdentitySuspension.status == "active",
                IdentitySuspension.expires_at.isnot(None),
                IdentitySuspension.expires_at <= now,
                IdentitySuspension.is_active.is_(True),
            )
            .values(
                status="expired",
                updated_at=now,
            )
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount


class RegistryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def register_identity(
        self,
        person_id: str,
        identity_id: str,
        registry_type: str = "citizen",
        registered_by: str | None = None,
    ) -> NationalIdentityRegistry:
        registration = NationalIdentityRegistry(
            uuid=str(uuid.uuid4()),
            registry_id=str(uuid.uuid4()).replace("-", "")[:16],
            person_id=person_id,
            identity_id=identity_id,
            registry_type=registry_type,
            registration_number=str(uuid.uuid4()).replace("-", "").upper()[:20],
            registered_at=_now(),
            registered_by=registered_by or "",
            status="active",
            is_active=True,
        )
        self.session.add(registration)
        self.session.flush()
        return registration

    def verify_registration(
        self,
        registry_id: str,
        verified_by: str,
    ) -> NationalIdentityRegistry | None:
        stmt = select(NationalIdentityRegistry).where(
            NationalIdentityRegistry.registry_id == registry_id,
            NationalIdentityRegistry.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        registration = result.scalar_one_or_none()
        if not registration:
            return None
        now = _now()
        registration.verified_at = now
        registration.verified_by = verified_by
        registration.last_verified = now
        registration.updated_at = now
        self.session.flush()
        return registration

    def certify_identity(
        self,
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
    ) -> IdentityCertificationRegistry:
        cert = IdentityCertificationRegistry(
            uuid=str(uuid.uuid4()),
            certification_id=certification_id,
            person_id=person_id,
            organization_id=organization_id,
            certifying_authority_id=certifying_authority_id or "",
            certification_type=certification_type or "",
            certification_number=certification_number
            or str(uuid.uuid4()).replace("-", "").upper()[:20],
            issue_date=issue_date or _now(),
            expiry_date=expiry_date,
            verified_by=verified_by,
            verification_method=verification_method,
            digital_signature=digital_signature,
            status="active",
            is_active=True,
        )
        self.session.add(cert)
        self.session.flush()
        return cert

    def get_registration(
        self,
        person_id: str,
    ) -> NationalIdentityRegistry | None:
        stmt = select(NationalIdentityRegistry).where(
            NationalIdentityRegistry.person_id == person_id,
            NationalIdentityRegistry.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_certification(
        self,
        person_id: str,
    ) -> IdentityCertificationRegistry | None:
        stmt = select(IdentityCertificationRegistry).where(
            IdentityCertificationRegistry.person_id == person_id,
            IdentityCertificationRegistry.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def revoke_certification(
        self,
        certification_id: str,
        reason: str,
    ) -> IdentityCertificationRegistry | None:
        stmt = select(IdentityCertificationRegistry).where(
            IdentityCertificationRegistry.certification_id == certification_id,
            IdentityCertificationRegistry.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        cert = result.scalar_one_or_none()
        if not cert:
            return None
        cert.status = "revoked"
        cert.revocation_reason = reason
        cert.updated_at = _now()
        self.session.flush()
        return cert
