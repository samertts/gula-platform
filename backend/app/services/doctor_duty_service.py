"""Server-side Doctor Duty authorization service.

Design reminder: client-provided facility/ward/department values are hints only;
server-persisted duty assignments are authoritative. Every clinical mutation must
call ``require_clinical_access`` at execution time. Expired or revoked contexts deny.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app._compat import UTC
from app.models.doctor_duty import (
    ACTIVE_DUTY_STATES,
    ClinicalAccessContext,
    DoctorDuty,
    DutyAuditEvent,
    DutyBreakGlass,
    DutyContext,
    DutyHandover,
    ShiftContext,
)
from app.models.user import User
from app.services.doctor_duty_lifecycle import duty_lifecycle


class DutyAuthorizationError(Exception):
    """Raised for a fail-closed clinical authorization decision."""

    def __init__(self, code: str, message: str = "Clinical access denied") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ClinicalRequest:
    user_id: int
    purpose: str
    organization_id: int
    facility_id: int
    department_id: str | None = None
    ward_id: str | None = None
    patient_id: int | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    emergency: bool = False
    request_id: str | None = None
    correlation_id: str | None = None


class DoctorDutyService:
    """Transactional duty lifecycle and clinical scope enforcement."""

    def __init__(self, db: Session, *, now: datetime | None = None) -> None:
        self.db = db
        self._now = (now or datetime.now(UTC)).astimezone(UTC)

    @property
    def now(self) -> datetime:
        return self._now

    def _audit(self, *, event_type: str, decision: str, actor_id: int | None,
               context: DutyContext | None = None, duty: DoctorDuty | None = None,
               request: ClinicalRequest | None = None, metadata: dict | None = None) -> None:
        self.db.add(DutyAuditEvent(
            event_type=event_type,
            decision=decision,
            actor_id=actor_id,
            duty_context_id=context.id if context else None,
            organization_id=(context.organization_id if context else duty.organization_id if duty else request.organization_id if request else None),
            facility_id=(context.facility_id if context else duty.facility_id if duty else request.facility_id if request else None),
            location={"department_id": context.department_id if context else duty.department_id if duty else request.department_id if request else None,
                      "ward_id": context.ward_id if context else duty.ward_id if duty else request.ward_id if request else None},
            resource_type=request.resource_type if request else None,
            resource_id=request.resource_id if request else None,
            patient_id=request.patient_id if request else None,
            purpose=request.purpose if request else context.purpose if context else duty.purpose if duty else None,
            request_id=request.request_id if request else None,
            correlation_id=request.correlation_id if request else None,
            occurred_at=self.now,
            metadata_json=metadata,
        ))

    def _user_is_eligible(self, user: User | None) -> bool:
        return bool(user and user.is_active and user.is_verified)

    def _active_context(self, user_id: int, *, lock: bool = False) -> DutyContext | None:
        query = self.db.query(DutyContext).filter(
            DutyContext.user_id == user_id,
            DutyContext.status.in_(ACTIVE_DUTY_STATES),
            DutyContext.started_at <= self.now,
            DutyContext.expires_at > self.now,
        )
        if lock:
            query = query.with_for_update()
        contexts = query.order_by(DutyContext.started_at.desc()).all()
        if len(contexts) > 1:
            raise DutyAuthorizationError("CONCURRENT_ACTIVE_DUTIES")
        context = contexts[0] if contexts else None
        if context is not None:
            duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == context.duty_id).first()
            if duty is None or duty.status not in ACTIVE_DUTY_STATES:
                return None
        return context

    def _require_duty_admin(self, actor_id: int) -> User:
        actor = self.db.query(User).filter(User.id == actor_id).one_or_none()
        admin_roles = {"admin", "system_admin", "super_admin", "director", "medical_director", "duty_manager"}
        if not self._user_is_eligible(actor) or getattr(actor, "role", None) not in admin_roles:
            raise DutyAuthorizationError("DUTY_ADMIN_REQUIRED")
        return actor

    def schedule_duty(self, *, actor_id: int, user_id: int, organization_id: int, facility_id: int,
                      role_id: str, purpose: str, starts_at: datetime, expected_end_at: datetime,
                      tenant_id: int | None = None, department_id: str | None = None,
                      ward_id: str | None = None, room_id: str | None = None,
                      assigned_patient_ids: list[int] | None = None) -> DoctorDuty:
        self._require_duty_admin(actor_id)
        if actor_id == user_id:
            raise DutyAuthorizationError("SELF_DUTY_ASSIGNMENT_DENIED")
        target = self.db.query(User).filter(User.id == user_id).one_or_none()
        if not self._user_is_eligible(target):
            raise DutyAuthorizationError("PROFESSIONAL_NOT_ELIGIBLE")
        starts_at = starts_at.astimezone(UTC)
        expected_end_at = expected_end_at.astimezone(UTC)
        if expected_end_at <= starts_at or expected_end_at <= self.now:
            raise DutyAuthorizationError("DUTY_TIME_INVALID")
        duty = DoctorDuty(user_id=user_id, tenant_id=tenant_id, organization_id=organization_id,
                          facility_id=facility_id, department_id=department_id, ward_id=ward_id,
                          room_id=room_id, role_id=role_id, purpose=purpose, starts_at=starts_at,
                          expected_end_at=expected_end_at, status="SCHEDULED", assigned_by=actor_id,
                          assigned_patient_ids=assigned_patient_ids or [], version=1)
        self.db.add(duty)
        self._audit(event_type="DUTY_SCHEDULED", decision="ALLOW", actor_id=actor_id, duty=duty)
        self.db.flush()
        return duty

    def cancel_duty(self, duty_id: int, *, actor_id: int, reason: str) -> None:
        self._require_duty_admin(actor_id)
        duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == duty_id).with_for_update().one_or_none()
        if duty is None:
            raise DutyAuthorizationError("DUTY_NOT_FOUND")
        if duty.status not in {"SCHEDULED", "CHECKED_IN"}:
            raise DutyAuthorizationError("DUTY_STATE_INVALID")
        duty.status = "CANCELLED"
        duty.revoked_by = actor_id
        duty.revocation_reason = reason.strip() or "cancelled_by_admin"
        duty.version += 1
        self._audit(event_type="DUTY_REVOKED", decision="ALLOW", actor_id=actor_id, duty=duty, metadata={"reason": duty.revocation_reason})
        self.db.flush()

    def extend_duty(self, duty_id: int, *, actor_id: int, new_expected_end_at: datetime) -> DoctorDuty:
        self._require_duty_admin(actor_id)
        duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == duty_id).with_for_update().one_or_none()
        if duty is None:
            raise DutyAuthorizationError("DUTY_NOT_FOUND")
        new_end = new_expected_end_at.astimezone(UTC)
        if duty.status not in ACTIVE_DUTY_STATES or new_end <= self.now or new_end <= duty.expected_end_at:
            raise DutyAuthorizationError("DUTY_EXTENSION_INVALID")
        if new_end - self.now > timedelta(hours=24):
            raise DutyAuthorizationError("DUTY_EXTENSION_TOO_LONG")
        duty.expected_end_at = new_end
        duty.version += 1
        for context in self.db.query(DutyContext).filter(DutyContext.duty_id == duty.id, DutyContext.status.in_(ACTIVE_DUTY_STATES)).with_for_update().all():
            context.expires_at = new_end
            clinical = self.db.query(ClinicalAccessContext).filter(ClinicalAccessContext.duty_context_id == context.id).with_for_update().one_or_none()
            if clinical:
                clinical.expires_at = new_end
                clinical.version += 1
            context.authz_version += 1
        self._audit(event_type="DUTY_SCHEDULED", decision="ALLOW", actor_id=actor_id, duty=duty, metadata={"action": "extend", "new_expected_end_at": new_end.isoformat()})
        self.db.flush()
        return duty

    def start_duty(self, duty_id: int, *, actor_id: int) -> DutyContext:
        """Start a pre-assigned duty using server time and a row lock."""
        duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == duty_id).with_for_update().one_or_none()
        user = self.db.query(User).filter(User.id == actor_id).one_or_none()
        if duty is None:
            raise DutyAuthorizationError("DUTY_NOT_FOUND")
        if duty.user_id != actor_id:
            self._audit(event_type="DUTY_STARTED", decision="DENY", actor_id=actor_id, duty=duty, metadata={"reason": "not_assigned"})
            raise DutyAuthorizationError("DUTY_NOT_ASSIGNED")
        if not self._user_is_eligible(user):
            raise DutyAuthorizationError("PROFESSIONAL_NOT_ELIGIBLE")
        if duty.status not in ("SCHEDULED", "CHECKED_IN"):
            raise DutyAuthorizationError("DUTY_STATE_INVALID")
        if self.now < duty.starts_at:
            raise DutyAuthorizationError("DUTY_NOT_STARTED")
        if self.now >= duty.expected_end_at:
            duty.status = "ENDED"
            duty.actual_ended_at = self.now
            self._audit(event_type="DUTY_STARTED", decision="DENY", actor_id=actor_id, duty=duty, metadata={"reason": "expired_before_start"})
            raise DutyAuthorizationError("DUTY_EXPIRED")
        if self._active_context(actor_id, lock=True) is not None:
            raise DutyAuthorizationError("CONCURRENT_ACTIVE_DUTY")

        context_id = f"dctx_{uuid4().hex}"
        context = DutyContext(
            id=context_id, duty_id=duty.id, user_id=actor_id, tenant_id=duty.tenant_id,
            organization_id=duty.organization_id, facility_id=duty.facility_id,
            department_id=duty.department_id, ward_id=duty.ward_id, role_id=duty.role_id,
            purpose=duty.purpose, status="ACTIVE", started_at=self.now,
            expires_at=min(duty.expected_end_at, self.now + timedelta(hours=24)),
            assigned_patient_ids=duty.assigned_patient_ids or [],
            permissions={"clinical": True, "break_glass": False}, authz_version=1,
        )
        self.db.add(context)
        self.db.add(ShiftContext(
            id=f"shift_{uuid4().hex}", duty_context_id=context_id,
            shift_start=duty.starts_at, shift_expected_end=duty.expected_end_at,
            timezone="UTC", server_started_at=self.now, status="ACTIVE",
        ))
        self.db.add(ClinicalAccessContext(
            id=f"cctx_{uuid4().hex}", duty_context_id=context_id, user_id=actor_id,
            organization_id=duty.organization_id, facility_id=duty.facility_id,
            department_id=duty.department_id, ward_id=duty.ward_id,
            scope_type="ASSIGNED_LOCATION", allowed_resources=["patient.read", "clinical.read"],
            patient_scope={"patient_ids": duty.assigned_patient_ids or [], "assigned_only": bool(duty.assigned_patient_ids)},
            purpose=duty.purpose, active=True, expires_at=context.expires_at, version=1,
        ))
        duty.status = "ACTIVE"
        duty.actual_started_at = self.now
        duty.version += 1
        self._audit(event_type="DUTY_STARTED", decision="ALLOW", actor_id=actor_id, context=context, duty=duty)
        self.db.flush()
        return context

    def end_duty(self, duty_context_id: str, *, actor_id: int, reason: str = "normal_end") -> None:
        context = self.db.query(DutyContext).filter(DutyContext.id == duty_context_id).with_for_update().one_or_none()
        if context is None or context.user_id != actor_id:
            raise DutyAuthorizationError("DUTY_CONTEXT_DENIED")
        duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == context.duty_id).with_for_update().one()
        context.status = "ENDED"
        context.ended_at = self.now
        context.authz_version += 1
        duty.status = "ENDED"
        duty.actual_ended_at = self.now
        duty.version += 1
        clinical = self.db.query(ClinicalAccessContext).filter(ClinicalAccessContext.duty_context_id == context.id).with_for_update().one_or_none()
        if clinical:
            clinical.active = False
            clinical.revoked_at = self.now
            clinical.version += 1
        shift = self.db.query(ShiftContext).filter(ShiftContext.duty_context_id == context.id).with_for_update().one_or_none()
        if shift:
            shift.status = "ENDED"
            shift.server_ended_at = self.now
        self._audit(event_type="DUTY_ENDED", decision="ALLOW", actor_id=actor_id, context=context, duty=duty, metadata={"reason": reason})
        self.db.flush()
        duty_lifecycle.revoke(context.id)

    def expire_due_contexts(self, *, limit: int = 100) -> int:
        """Revoke expired contexts without waiting for logout or a UI request."""
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")
        contexts = self.db.query(DutyContext).filter(
            DutyContext.status.in_(ACTIVE_DUTY_STATES), DutyContext.expires_at <= self.now,
        ).with_for_update(skip_locked=True).limit(limit).all()
        count = 0
        for context in contexts:
            duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == context.duty_id).with_for_update().one_or_none()
            context.status = "ENDED"
            context.ended_at = self.now
            context.authz_version += 1
            if duty and duty.status in ACTIVE_DUTY_STATES:
                duty.status = "ENDED"
                duty.actual_ended_at = self.now
                duty.version += 1
            clinical = self.db.query(ClinicalAccessContext).filter(ClinicalAccessContext.duty_context_id == context.id).with_for_update().one_or_none()
            if clinical:
                clinical.active = False
                clinical.revoked_at = self.now
                clinical.version += 1
            self._audit(event_type="DUTY_ENDED", decision="ALLOW", actor_id=None, context=context, duty=duty, metadata={"reason": "server_expiry"})
            duty_lifecycle.revoke(context.id)
            count += 1
        self.db.flush()
        return count

    def revoke_duty(self, duty_id: int, *, actor_id: int, reason: str) -> None:
        duty = self.db.query(DoctorDuty).filter(DoctorDuty.id == duty_id).with_for_update().one_or_none()
        if duty is None:
            raise DutyAuthorizationError("DUTY_NOT_FOUND")
        duty.status = "REVOKED"
        duty.revoked_by = actor_id
        duty.revocation_reason = reason
        duty.version += 1
        contexts = self.db.query(DutyContext).filter(DutyContext.duty_id == duty_id, DutyContext.status.in_(ACTIVE_DUTY_STATES)).with_for_update().all()
        for context in contexts:
            context.status = "REVOKED"
            context.ended_at = self.now
            context.authz_version += 1
            clinical = self.db.query(ClinicalAccessContext).filter(ClinicalAccessContext.duty_context_id == context.id).with_for_update().one_or_none()
            if clinical:
                clinical.active = False
                clinical.revoked_at = self.now
                clinical.version += 1
            self._audit(event_type="DUTY_REVOKED", decision="ALLOW", actor_id=actor_id, context=context, duty=duty, metadata={"reason": reason})
            duty_lifecycle.revoke(context.id)
        self.db.flush()

    def authorize(self, request: ClinicalRequest) -> ClinicalAccessContext:
        """Authorize a read or mutation at execution time; never from UI state."""
        context = self._active_context(request.user_id, lock=True)
        clinical = None if context is None else self.db.query(ClinicalAccessContext).filter(
            ClinicalAccessContext.duty_context_id == context.id,
            ClinicalAccessContext.active.is_(True),
            ClinicalAccessContext.expires_at > self.now,
        ).with_for_update().one_or_none()
        allowed = bool(context and clinical)
        if allowed:
            allowed = context.organization_id == request.organization_id and context.facility_id == request.facility_id
        if allowed and context.department_id is not None:
            allowed = context.department_id == request.department_id
        if allowed and context.ward_id is not None:
            allowed = context.ward_id == request.ward_id
        if allowed and request.patient_id is not None:
            patient_ids = set((clinical.patient_scope or {}).get("patient_ids", []))
            assigned_only = bool((clinical.patient_scope or {}).get("assigned_only"))
            allowed = not assigned_only or request.patient_id in patient_ids
            if not allowed and request.emergency:
                break_glass = self.db.query(DutyBreakGlass).filter(
                    DutyBreakGlass.duty_context_id == context.id,
                    DutyBreakGlass.actor_id == request.user_id,
                    DutyBreakGlass.patient_id == request.patient_id,
                    DutyBreakGlass.status == "ACTIVE",
                    DutyBreakGlass.expires_at > self.now,
                ).first()
                allowed = break_glass is not None
        if allowed and request.resource_type:
            allowed = request.resource_type in set(clinical.allowed_resources or []) or request.resource_type in {"patient.read", "clinical.read"}
        if not allowed:
            self._audit(event_type="PATIENT_ACCESS" if request.patient_id else "CLINICAL_ACCESS", decision="DENY", actor_id=request.user_id, context=context, request=request, metadata={"reason": "default_deny"})
            self.db.flush()
            raise DutyAuthorizationError("CLINICAL_ACCESS_DENIED")
        self._audit(event_type="PATIENT_ACCESS" if request.patient_id else "CLINICAL_ACCESS", decision="ALLOW", actor_id=request.user_id, context=context, request=request)
        self.db.flush()
        return clinical

    def open_break_glass(self, request: ClinicalRequest, *, reason: str, duration_minutes: int = 30) -> DutyBreakGlass:
        if not request.emergency:
            raise DutyAuthorizationError("EMERGENCY_SCOPE_REQUIRED")
        if request.patient_id is None:
            raise DutyAuthorizationError("BREAK_GLASS_PATIENT_REQUIRED")
        if not reason.strip():
            raise DutyAuthorizationError("BREAK_GLASS_REASON_REQUIRED")
        context = self._active_context(request.user_id, lock=True)
        if context is None or context.organization_id != request.organization_id or context.facility_id != request.facility_id:
            self._audit(event_type="BREAK_GLASS", decision="DENY", actor_id=request.user_id, context=context, request=request, metadata={"reason": "scope_or_duty_denied"})
            self.db.flush()
            raise DutyAuthorizationError("CLINICAL_ACCESS_DENIED")
        if duration_minutes < 1 or duration_minutes > 60:
            raise DutyAuthorizationError("BREAK_GLASS_DURATION_INVALID")
        session = DutyBreakGlass(
            id=f"bg_{uuid4().hex}", duty_context_id=context.id, actor_id=request.user_id,
            patient_id=request.patient_id, reason=reason.strip(), scope={"facility_id": request.facility_id, "ward_id": request.ward_id},
            started_at=self.now, expires_at=self.now + timedelta(minutes=duration_minutes), status="ACTIVE",
        )
        self.db.add(session)
        self._audit(event_type="BREAK_GLASS", decision="ALLOW", actor_id=request.user_id, context=context, request=request, metadata={"expires_at": session.expires_at.isoformat()})
        self.db.flush()
        return session

    def start_handover(self, outgoing_duty_id: int, incoming_duty_id: int, *, actor_id: int, patient_ids: list[int], task_ids: list[str], notes: str | None = None) -> DutyHandover:
        outgoing = self.db.query(DoctorDuty).filter(DoctorDuty.id == outgoing_duty_id).with_for_update().one_or_none()
        incoming = self.db.query(DoctorDuty).filter(DoctorDuty.id == incoming_duty_id).with_for_update().one_or_none()
        if not outgoing or not incoming or outgoing.user_id != actor_id or outgoing.status != "ACTIVE":
            raise DutyAuthorizationError("HANDOVER_NOT_ALLOWED")
        if (outgoing.organization_id, outgoing.facility_id, outgoing.department_id, outgoing.ward_id) != (incoming.organization_id, incoming.facility_id, incoming.department_id, incoming.ward_id):
            raise DutyAuthorizationError("HANDOVER_SCOPE_MISMATCH")
        outgoing.status = "HANDOVER_PENDING"
        handover = DutyHandover(outgoing_duty_id=outgoing.id, incoming_duty_id=incoming.id, outgoing_user_id=outgoing.user_id, incoming_user_id=incoming.user_id, patient_ids=patient_ids, task_ids=task_ids, notes=notes)
        self.db.add(handover)
        self._audit(event_type="HANDOVER", decision="ALLOW", actor_id=actor_id, duty=outgoing, metadata={"incoming_duty_id": incoming.id, "patient_count": len(patient_ids)})
        self.db.flush()
        return handover

    def confirm_handover(self, handover_id: int, *, actor_id: int) -> None:
        handover = self.db.query(DutyHandover).filter(DutyHandover.id == handover_id).with_for_update().one_or_none()
        if handover is None or handover.incoming_user_id != actor_id or handover.status != "PENDING":
            raise DutyAuthorizationError("HANDOVER_CONFIRM_DENIED")
        incoming = self.db.query(DoctorDuty).filter(DoctorDuty.id == handover.incoming_duty_id).with_for_update().one()
        outgoing = self.db.query(DoctorDuty).filter(DoctorDuty.id == handover.outgoing_duty_id).with_for_update().one()
        handover.status = "COMPLETED"
        handover.confirmed_at = self.now
        handover.completed_at = self.now
        incoming.assigned_patient_ids = handover.patient_ids
        outgoing.status = "HANDOVER_COMPLETED"
        self.end_duty_for_handover(outgoing, actor_id=handover.outgoing_user_id)
        self._audit(event_type="HANDOVER", decision="ALLOW", actor_id=actor_id, duty=incoming, metadata={"handover_id": handover.id})
        self.db.flush()

    def end_duty_for_handover(self, duty: DoctorDuty, *, actor_id: int) -> None:
        context = self.db.query(DutyContext).filter(DutyContext.duty_id == duty.id, DutyContext.status.in_(ACTIVE_DUTY_STATES)).with_for_update().one_or_none()
        if context:
            self.end_duty(context.id, actor_id=actor_id, reason="handover_completed")
