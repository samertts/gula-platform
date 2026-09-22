from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.lifecycle.models import (
    CitizenLifecycle,
    ConsentRecord,
    EnterpriseRegistration,
    EnterpriseRegistrationStep,
    FamilyLink,
    GovernmentAppointment,
    GuardianAccount,
    WorkforceRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService


class EnterpriseRegistrationService:
    """Fully converted to the async session-stored convention
    (`__init__(self, session)`, `await self.session.execute(...)`),
    matching every other NIAM service in this codebase. `start_registration`
    was the one representative Category-F repair
    (docs/security/NIAM_SYNC_ASYNC_MISMATCH_INVENTORY.md); the remaining 6
    methods (validate_license, submit_inspection, assess_risk,
    approve_registration, reject_registration, get_registration_status,
    plus the private _get_registration/_complete_step helpers) previously
    still took an explicit `db: Session` and used the legacy sync
    `db.query()` API while routes.py called them via
    `EnterpriseRegistrationService(db)` (a class already converted to a
    single-arg async constructor) and `await`ed their return values --
    a real arity mismatch (`db` bound into the first positional business
    parameter) plus a missed-`await` on the now-async `_add_step`/
    `_complete_step`, not just the usual dependency-typing mismatch. See
    docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F2_ENTERPRISE_STATUS.md."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def start_registration(
        self, org_id: str, submitted_by: str, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = EnterpriseRegistration(
            uuid=org_id,
            reg_id=org_id,
            organization_id=org_id,
            status="draft",
            submitted_by=submitted_by,
            submitted_at=datetime.now(UTC),
            current_step="license_validation",
            is_active=True,
        )
        self.session.add(reg)
        await self.session.flush()
        await self._add_step(reg.id, "license_validation", performed_by=submitted_by)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="ENTERPRISE_REGISTRATION_STARTED",
                category="LIFECYCLE",
                action="lifecycle.enterprise_registration.start",
                actor_id=actor_account_id,
                target_type="enterprise_registration",
                target_id=reg.id,
                decision="ALLOW",
                reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE",
                data_classification="INTERNAL",
            ),
        )
        return reg

    async def _add_step(
        self, reg_pk: str, step_name: str,
        performed_by: str | None = None, output: dict[str, Any] | None = None,
    ) -> EnterpriseRegistrationStep:
        step = EnterpriseRegistrationStep(
            # uuid must be globally unique (column constraint) and this
            # step's own reg_id+step_name composite (already unique via
            # step_id, the business key) can exceed the column's 36-char
            # limit, so a real uuid4 is used here rather than a composite
            # business string. See docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F2_ENTERPRISE_STATUS.md.
            uuid=str(uuid4()),
            step_id=f"{reg_pk}-{step_name}",
            reg_id=reg_pk,
            step_name=step_name,
            status="in_progress",
            started_at=datetime.now(UTC),
            performed_by=performed_by,
            output=output,
            is_active=True,
        )
        self.session.add(step)
        return step

    async def validate_license(
        self, reg_id: str, license_document: str, validated_by: str, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = await self._get_registration(reg_id)
        reg.license_document = license_document
        reg.license_validated_at = datetime.now(UTC)
        reg.license_validated_by = validated_by
        reg.status = "license_validated"
        reg.current_step = "inspection"
        reg.is_active = True
        await self._complete_step(reg.id, "license_validation", performed_by=validated_by)
        await self._add_step(reg.id, "inspection", performed_by=validated_by)
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="ENTERPRISE_REGISTRATION_LICENSE_VALIDATED", category="LIFECYCLE",
            action="lifecycle.enterprise_registration.validate_license", actor_id=actor_account_id,
            target_type="enterprise_registration", target_id=reg.id, decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE", data_classification="INTERNAL",
        ))
        return reg

    async def submit_inspection(
        self, reg_id: str, inspection_report: dict[str, Any], inspected_by: str, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = await self._get_registration(reg_id)
        reg.inspection_report = inspection_report
        reg.inspected_at = datetime.now(UTC)
        reg.inspected_by = inspected_by
        reg.status = "inspected"
        reg.current_step = "risk_assessment"
        reg.is_active = True
        await self._complete_step(reg.id, "inspection", performed_by=inspected_by)
        await self._add_step(reg.id, "risk_assessment", performed_by=inspected_by)
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="ENTERPRISE_REGISTRATION_INSPECTED", category="LIFECYCLE",
            action="lifecycle.enterprise_registration.inspect", actor_id=actor_account_id,
            target_type="enterprise_registration", target_id=reg.id, decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE", data_classification="INTERNAL",
        ))
        return reg

    async def assess_risk(
        self, reg_id: str, risk_assessment: dict[str, Any], risk_score: int, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = await self._get_registration(reg_id)
        reg.risk_assessment = risk_assessment
        reg.risk_score = risk_score
        reg.risk_assessed_at = datetime.now(UTC)
        reg.status = "risk_assessed"
        reg.current_step = "approval"
        reg.is_active = True
        await self._complete_step(reg.id, "risk_assessment", performed_by=risk_assessment.get("assessed_by"))
        await self._add_step(reg.id, "approval")
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="ENTERPRISE_REGISTRATION_RISK_ASSESSED", category="LIFECYCLE",
            action="lifecycle.enterprise_registration.assess_risk", actor_id=actor_account_id,
            target_type="enterprise_registration", target_id=reg.id, decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE", data_classification="INTERNAL",
        ))
        return reg

    async def approve_registration(
        self, reg_id: str, approved_by: str, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = await self._get_registration(reg_id)
        reg.approved_by = approved_by
        reg.approved_at = datetime.now(UTC)
        reg.certificate_id = f"CERT-{reg.reg_id}-{int(datetime.now(UTC).timestamp())}"
        reg.status = "approved"
        reg.current_step = "certificate_issued"
        reg.is_active = True
        await self._complete_step(reg.id, "approval", performed_by=approved_by)
        await self._add_step(reg.id, "certificate_issued", performed_by=approved_by, output={"certificate_id": reg.certificate_id})
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="ENTERPRISE_REGISTRATION_APPROVED", category="LIFECYCLE",
            action="lifecycle.enterprise_registration.approve", actor_id=actor_account_id,
            target_type="enterprise_registration", target_id=reg.id, decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE", data_classification="INTERNAL",
        ))
        return reg

    async def reject_registration(
        self, reg_id: str, reason: str, actor_account_id: str | None = None,
    ) -> EnterpriseRegistration:
        reg = await self._get_registration(reg_id)
        reg.rejection_reason = reason
        reg.status = "rejected"
        reg.is_active = False
        await self._complete_step(reg.id, reg.current_step or "rejected", output={"reason": reason})
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="ENTERPRISE_REGISTRATION_REJECTED", category="LIFECYCLE",
            action="lifecycle.enterprise_registration.reject", actor_id=actor_account_id,
            target_type="enterprise_registration", target_id=reg.id, decision="ALLOW",
            reason_code="PLATFORM_AUTHORITY_GOVERNANCE_MANAGE", data_classification="INTERNAL",
            metadata={"reason": reason},
        ))
        return reg

    async def get_registration_status(self, org_id: str) -> EnterpriseRegistration | None:
        stmt = select(EnterpriseRegistration).where(
            EnterpriseRegistration.organization_id == org_id,
            EnterpriseRegistration.is_active.is_(True),
        ).order_by(EnterpriseRegistration.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def _get_registration(self, reg_id: str) -> EnterpriseRegistration:
        stmt = select(EnterpriseRegistration).where(EnterpriseRegistration.reg_id == reg_id)
        result = await self.session.execute(stmt)
        reg = result.scalar_one_or_none()
        if not reg:
            raise ValueError(f"EnterpriseRegistration not found: reg_id={reg_id}")
        return reg

    async def _complete_step(
        self, reg_pk: str, step_name: str,
        performed_by: str | None = None, output: dict[str, Any] | None = None,
    ) -> None:
        stmt = select(EnterpriseRegistrationStep).where(
            EnterpriseRegistrationStep.reg_id == reg_pk,
            EnterpriseRegistrationStep.step_name == step_name,
        ).order_by(EnterpriseRegistrationStep.created_at.desc())
        result = await self.session.execute(stmt)
        step = result.scalars().first()
        if step:
            step.status = "completed"
            step.completed_at = datetime.now(UTC)
            step.performed_by = performed_by or step.performed_by
            if output:
                step.output = output


class WorkforceService:
    """Fully converted to the async session-stored convention
    (`__init__(self, session)`), matching every other NIAM service in this
    codebase. Previously had no `__init__` at all and every method took an
    explicit `db: Session`, while routes.py constructed it as
    `WorkforceService(db)` against a class with no constructor -- a real
    `TypeError` on every call. See
    docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F3_WORKFORCE_STATUS.md."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def request_employee(
        self, request_id: str, request_type: str,
        requesting_org_id: str, requested_by: str, person_id: str | None = None,
        actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = WorkforceRequest(
            uuid=request_id,
            request_id=request_id,
            request_type=request_type,
            requesting_org_id=requesting_org_id,
            requested_by=requested_by,
            person_id=person_id,
            status="draft",
            is_active=True,
        )
        self.session.add(req)
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_REQUEST_CREATED", category="LIFECYCLE",
            action="lifecycle.workforce.request_employee", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def validate_national_id(
        self, request_id: str, national_id_hash: str, actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.national_id_hash = national_id_hash
        req.status = "national_id_validated"
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_NATIONAL_ID_VALIDATED", category="LIFECYCLE",
            action="lifecycle.workforce.validate_national_id", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def validate_license(
        self, request_id: str, license_number: str, actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.license_number = license_number
        req.status = "license_validated"
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_LICENSE_VALIDATED", category="LIFECYCLE",
            action="lifecycle.workforce.validate_license", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def check_conflicts(
        self, request_id: str, conflict_report: dict[str, Any] | None = None, actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.conflict_report = conflict_report or {}
        req.status = "conflict_checked"
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_CONFLICTS_CHECKED", category="LIFECYCLE",
            action="lifecycle.workforce.check_conflicts", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def approve_request(
        self, request_id: str, approved_by: str, actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.approved_by = approved_by
        req.approved_at = datetime.now(UTC)
        req.status = "approved"
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_REQUEST_APPROVED", category="LIFECYCLE",
            action="lifecycle.workforce.approve_request", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def activate_account(self, request_id: str, actor_account_id: str | None = None) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.activated_at = datetime.now(UTC)
        req.status = "activated"
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_ACCOUNT_ACTIVATED", category="LIFECYCLE",
            action="lifecycle.workforce.activate_account", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
        ))
        return req

    async def terminate_employment(
        self, request_id: str, reason: str, actor_account_id: str | None = None,
    ) -> WorkforceRequest:
        req = await self._get_request(request_id)
        req.termination_reason = reason
        req.status = "terminated"
        req.is_active = False
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_EMPLOYMENT_TERMINATED", category="LIFECYCLE",
            action="lifecycle.workforce.terminate_employment", actor_id=actor_account_id,
            target_type="workforce_request", target_id=req.id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
            metadata={"reason": reason},
        ))
        return req

    async def get_request_status(self, request_id: str) -> WorkforceRequest | None:
        stmt = select(WorkforceRequest).where(WorkforceRequest.request_id == request_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def preserve_history(self, person_id: str, actor_account_id: str | None = None) -> list[WorkforceRequest]:
        stmt = select(WorkforceRequest).where(WorkforceRequest.person_id == person_id)
        result = await self.session.execute(stmt)
        requests = list(result.scalars().all())
        for req in requests:
            req.historical_preserved = True
        await self.session.flush()
        await self.audit.record(AuditEventInput(
            event_type="WORKFORCE_HISTORY_PRESERVED", category="LIFECYCLE",
            action="lifecycle.workforce.preserve_history", actor_id=actor_account_id,
            target_type="person", target_id=person_id, decision="ALLOW",
            reason_code="ADMIN_AUTHORITY_UNAVAILABLE", data_classification="INTERNAL",
            metadata={"preserved_count": len(requests)},
        ))
        return requests

    async def _get_request(self, request_id: str) -> WorkforceRequest:
        stmt = select(WorkforceRequest).where(WorkforceRequest.request_id == request_id)
        result = await self.session.execute(stmt)
        req = result.scalar_one_or_none()
        if not req:
            raise ValueError(f"WorkforceRequest not found: request_id={request_id}")
        return req


class GovernmentHRService:

    def create_appointment(
        self, db: Session, appointment_id: str, person_id: str,
        organization_id: str, hr_reference: str, appointment_type: str,
        position: str | None = None, grade: str | None = None,
        salary_scale: str | None = None, department: str | None = None,
        start_date: datetime | None = None,
    ) -> GovernmentAppointment:
        existing = db.query(GovernmentAppointment).filter(
            GovernmentAppointment.hr_reference == hr_reference,
        ).first()
        if existing:
            raise ValueError(f"GovernmentAppointment with hr_reference={hr_reference} already exists")

        appt = GovernmentAppointment(
            uuid=appointment_id,
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
            status="draft",
            is_active=True,
        )
        db.add(appt)
        db.flush()
        return appt

    def approve_appointment(self, db: Session, appointment_id: str, approved_by: str) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        appt.hr_approved_by = approved_by
        appt.hr_approved_at = datetime.now(UTC)
        appt.status = "hr_approved"
        db.flush()
        return appt

    def create_identity(self, db: Session, appointment_id: str) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        if appt.status not in ("hr_approved", "identity_created"):
            raise ValueError(f"Cannot create identity: status is {appt.status}, expected hr_approved")
        appt.identity_created = True
        appt.status = "identity_created"
        db.flush()
        return appt

    def issue_credential(self, db: Session, appointment_id: str) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        if not appt.identity_created:
            raise ValueError("Cannot issue credential before identity is created")
        appt.credential_issued = True
        appt.status = "credential_issued"
        db.flush()
        return appt

    def activate_account(self, db: Session, appointment_id: str) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        if not appt.credential_issued:
            raise ValueError("Cannot activate account before credential is issued")
        appt.account_activated = True
        appt.status = "activated"
        db.flush()
        return appt

    def assign_permissions(self, db: Session, appointment_id: str, permissions: dict[str, Any] | None = None) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        if not appt.account_activated:
            raise ValueError("Cannot assign permissions before account is activated")
        appt.permissions_assigned = True
        appt.status = "active"
        db.flush()
        return appt

    def promote(
        self, db: Session, appointment_id: str,
        new_position: str, new_grade: str, promoted_by: str | None = None,
    ) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        history = appt.promotion_history or []
        history.append({
            "from_position": appt.position,
            "from_grade": appt.grade,
            "to_position": new_position,
            "to_grade": new_grade,
            "promoted_by": promoted_by,
            "promoted_at": datetime.now(UTC).isoformat(),
        })
        appt.promotion_history = history
        appt.position = new_position
        appt.grade = new_grade
        appt.status = "promoted"
        db.flush()
        return appt

    def transfer(
        self, db: Session, appointment_id: str,
        new_org_id: str | None = None, new_dept: str | None = None,
        transferred_by: str | None = None,
    ) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        history = appt.transfer_history or []
        history.append({
            "from_org": appt.organization_id,
            "from_dept": appt.department,
            "to_org": new_org_id,
            "to_dept": new_dept,
            "transferred_by": transferred_by,
            "transferred_at": datetime.now(UTC).isoformat(),
        })
        appt.transfer_history = history
        if new_org_id:
            appt.organization_id = new_org_id
        if new_dept:
            appt.department = new_dept
        appt.status = "transferred"
        db.flush()
        return appt

    def retire(self, db: Session, appointment_id: str, retirement_date: datetime) -> GovernmentAppointment:
        appt = self._get_appointment(db, appointment_id)
        appt.end_date = retirement_date
        appt.status = "retired"
        appt.is_active = False
        db.flush()
        return appt

    def _get_appointment(self, db: Session, appointment_id: str) -> GovernmentAppointment:
        appt = db.query(GovernmentAppointment).filter(
            GovernmentAppointment.appointment_id == appointment_id,
        ).first()
        if not appt:
            raise ValueError(f"GovernmentAppointment not found: appointment_id={appointment_id}")
        return appt


class CitizenService:

    def register_citizen(self, db: Session, person_id: str, citizen_id: str | None = None) -> CitizenLifecycle:
        cid = citizen_id or person_id
        citizen = CitizenLifecycle(
            uuid=cid,
            citizen_id=cid,
            person_id=person_id,
            status="registered",
            registration_date=datetime.now(UTC),
            is_active=True,
        )
        db.add(citizen)
        db.flush()
        return citizen

    def send_otp(self, db: Session, citizen_id: str) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.otp_sent_at = datetime.now(UTC)
        citizen.status = "otp_sent"
        db.flush()
        return citizen

    def verify_otp(self, db: Session, citizen_id: str) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.otp_verified_at = datetime.now(UTC)
        citizen.status = "otp_verified"
        db.flush()
        return citizen

    def verify_identity(self, db: Session, citizen_id: str, verified_by: str) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.identity_verified_at = datetime.now(UTC)
        citizen.document_verification = citizen.document_verification or {}
        citizen.document_verification["verified_by"] = verified_by
        citizen.document_verification["verified_at"] = datetime.now(UTC).isoformat()
        citizen.status = "identity_verified"
        db.flush()
        return citizen

    def issue_health_id(self, db: Session, citizen_id: str, health_id: str) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.health_id = health_id
        citizen.status = "health_id_issued"
        db.flush()
        return citizen

    def link_guardian(
        self, db: Session, citizen_id: str,
        guardian_person_id: str, relationship: str,
    ) -> GuardianAccount:
        citizen = self._get_citizen(db, citizen_id)
        guardian = GuardianAccount(
            uuid=f"{citizen_id}-guardian-{guardian_person_id}",
            guardian_id=f"{citizen_id}-guardian-{guardian_person_id}",
            guardian_person_id=guardian_person_id,
            dependent_person_id=citizen.person_id,
            relationship=relationship,
            guardian_type=relationship,
            start_date=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        citizen.guardian_person_id = guardian_person_id
        citizen.status = "guardian_linked"
        db.add(guardian)
        db.flush()
        return guardian

    def link_family_member(
        self, db: Session, citizen_id: str,
        relative_id: str, relationship: str,
    ) -> FamilyLink:
        citizen = self._get_citizen(db, citizen_id)
        link = FamilyLink(
            uuid=f"{citizen_id}-fam-{relative_id}",
            link_id=f"{citizen_id}-fam-{relative_id}",
            person_id=citizen.person_id,
            relative_person_id=relative_id,
            relationship=relationship,
            emergency_contact=False,
            consent_sharing=False,
            is_active=True,
        )
        citizen.status = "family_linked"
        db.add(link)
        db.flush()
        return link

    def record_consent(
        self, db: Session, citizen_id: str,
        consent_type: str, granted_to: str | None = None,
        scope: dict[str, Any] | None = None,
    ) -> ConsentRecord:
        citizen = self._get_citizen(db, citizen_id)
        consent = ConsentRecord(
            uuid=f"{citizen_id}-consent-{consent_type}",
            consent_id=f"{citizen_id}-consent-{consent_type}",
            person_id=citizen.person_id,
            consent_type=consent_type,
            granted_to=granted_to,
            granted_at=datetime.now(UTC),
            scope=scope,
            status="active",
            is_active=True,
        )
        db.add(consent)
        db.flush()
        return consent

    def deactivate(self, db: Session, citizen_id: str, reason: str) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.deactivated_at = datetime.now(UTC)
        citizen.deactivation_reason = reason
        citizen.status = "deactivated"
        citizen.is_active = False
        db.flush()
        return citizen

    def record_death(
        self, db: Session, citizen_id: str,
        death_date: datetime, death_certificate_id: str,
    ) -> CitizenLifecycle:
        citizen = self._get_citizen(db, citizen_id)
        citizen.deceased_at = death_date
        citizen.death_certificate_id = death_certificate_id
        citizen.status = "deceased"
        citizen.is_active = False
        db.flush()
        return citizen

    def get_citizen_status(self, db: Session, person_id: str) -> CitizenLifecycle | None:
        return db.query(CitizenLifecycle).filter(
            CitizenLifecycle.person_id == person_id,
        ).order_by(CitizenLifecycle.created_at.desc()).first()

    def _get_citizen(self, db: Session, citizen_id: str) -> CitizenLifecycle:
        citizen = db.query(CitizenLifecycle).filter(
            CitizenLifecycle.citizen_id == citizen_id,
        ).first()
        if not citizen:
            raise ValueError(f"CitizenLifecycle not found: citizen_id={citizen_id}")
        return citizen


class GuardianService:
    """Category-F conversion: matches EnterpriseRegistrationService's
    proven representative repair (__init__(self, session), self.session,
    self.audit -- see NIAM_SYNC_ASYNC_MISMATCH_INVENTORY.md)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)

    async def create_guardianship(
        self, guardian_id: str,
        guardian_person_id: str, dependent_person_id: str,
        relationship: str, guardian_type: str,
        actor_account_id: str | None = None,
    ) -> GuardianAccount:
        guardian = GuardianAccount(
            uuid=guardian_id,
            guardian_id=guardian_id,
            guardian_person_id=guardian_person_id,
            dependent_person_id=dependent_person_id,
            relationship=relationship,
            guardian_type=guardian_type,
            start_date=datetime.now(UTC),
            status="active",
            is_active=True,
        )
        self.session.add(guardian)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="GUARDIANSHIP_CREATED",
                category="LIFECYCLE",
                action="lifecycle.guardianship.create",
                actor_id=actor_account_id,
                target_type="guardian_account",
                target_id=guardian.id,
                decision="ALLOW",
                reason_code="GUARDIANSHIP_CREATED",
                data_classification="INTERNAL",
            ),
        )
        return guardian

    async def terminate_guardianship(
        self, guardian_id: str, reason: str, actor_account_id: str | None = None,
    ) -> GuardianAccount:
        guardian = await self._get_guardian(guardian_id)
        guardian.end_date = datetime.now(UTC)
        guardian.status = "terminated"
        guardian.is_active = False
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="GUARDIANSHIP_TERMINATED",
                category="LIFECYCLE",
                action="lifecycle.guardianship.terminate",
                actor_id=actor_account_id,
                target_type="guardian_account",
                target_id=guardian.id,
                decision="ALLOW",
                reason_code="GUARDIANSHIP_TERMINATED",
                data_classification="INTERNAL",
                metadata={"reason": reason},
            ),
        )
        return guardian

    async def get_dependents(self, guardian_person_id: str) -> list[GuardianAccount]:
        stmt = select(GuardianAccount).where(
            GuardianAccount.guardian_person_id == guardian_person_id,
            GuardianAccount.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_guardians(self, dependent_person_id: str) -> list[GuardianAccount]:
        stmt = select(GuardianAccount).where(
            GuardianAccount.dependent_person_id == dependent_person_id,
            GuardianAccount.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delegate_access(
        self, guardian_id: str,
        access_permissions: dict[str, Any],
        actor_account_id: str | None = None,
    ) -> GuardianAccount:
        guardian = await self._get_guardian(guardian_id)
        guardian.delegated_access = access_permissions
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="GUARDIANSHIP_ACCESS_DELEGATED",
                category="LIFECYCLE",
                action="lifecycle.guardianship.delegate_access",
                actor_id=actor_account_id,
                target_type="guardian_account",
                target_id=guardian.id,
                decision="ALLOW",
                reason_code="GUARDIANSHIP_ACCESS_DELEGATED",
                data_classification="INTERNAL",
            ),
        )
        return guardian

    async def verify_guardianship(
        self, guardian_id: str, verified_by: str, actor_account_id: str | None = None,
    ) -> GuardianAccount:
        guardian = await self._get_guardian(guardian_id)
        guardian.verified_by = verified_by
        guardian.verified_at = datetime.now(UTC)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="GUARDIANSHIP_VERIFIED",
                category="LIFECYCLE",
                action="lifecycle.guardianship.verify",
                actor_id=actor_account_id,
                target_type="guardian_account",
                target_id=guardian.id,
                decision="ALLOW",
                reason_code="GUARDIANSHIP_VERIFIED",
                data_classification="INTERNAL",
            ),
        )
        return guardian

    async def get_guardian(self, guardian_id: str) -> GuardianAccount | None:
        """Public lookup, used by routes for pre-mutation ownership
        checks (e.g. confirming the caller is the guardian_person_id on
        an existing record before allowing terminate/delegate)."""
        stmt = select(GuardianAccount).where(
            GuardianAccount.guardian_id == guardian_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_guardian(self, guardian_id: str) -> GuardianAccount:
        guardian = await self.get_guardian(guardian_id)
        if not guardian:
            raise ValueError(f"GuardianAccount not found: guardian_id={guardian_id}")
        return guardian
