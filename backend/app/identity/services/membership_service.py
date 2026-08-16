from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.administrative_structure import (
    NIAMAdminDepartment,
    NIAMAdminFacility,
    NIAMAdminUnit,
    OrganizationOwnership,
    OrganizationRepresentative,
    OwnershipStatus,
    RepresentativeStatus,
)
from app.identity.models.audit import AuditAction
from app.identity.models.membership import (
    InvitationStatus,
    Membership,
    MembershipApplication,
    MembershipApplicationStatus,
    MembershipInvitation,
    MembershipScopeType,
    MembershipSource,
    MembershipStatus,
)
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.models.workspace import Workspace, WorkspaceStatus
from app.identity.services.access_revocation import revoke_account_access
from app.identity.services.audit_service import AuditService

LEGAL_MEMBERSHIP_TRANSITIONS: dict[str, frozenset[str]] = {
    MembershipStatus.pending.value: frozenset({MembershipStatus.active.value, MembershipStatus.rejected.value, MembershipStatus.revoked.value}),
    MembershipStatus.invited.value: frozenset({MembershipStatus.active.value, MembershipStatus.rejected.value, MembershipStatus.revoked.value, MembershipStatus.expired.value}),
    MembershipStatus.active.value: frozenset({MembershipStatus.suspended.value, MembershipStatus.expired.value, MembershipStatus.revoked.value, MembershipStatus.deactivated.value}),
    MembershipStatus.suspended.value: frozenset({MembershipStatus.active.value, MembershipStatus.revoked.value, MembershipStatus.expired.value, MembershipStatus.deactivated.value}),
    MembershipStatus.expired.value: frozenset({MembershipStatus.active.value, MembershipStatus.revoked.value}),
    MembershipStatus.rejected.value: frozenset(),
    MembershipStatus.revoked.value: frozenset(),
    MembershipStatus.deactivated.value: frozenset(),
}

LEGAL_APPLICATION_TRANSITIONS: dict[str, frozenset[str]] = {
    MembershipApplicationStatus.draft.value: frozenset({MembershipApplicationStatus.submitted.value, MembershipApplicationStatus.cancelled.value}),
    MembershipApplicationStatus.submitted.value: frozenset({MembershipApplicationStatus.under_review.value, MembershipApplicationStatus.cancelled.value, MembershipApplicationStatus.expired.value}),
    MembershipApplicationStatus.under_review.value: frozenset({MembershipApplicationStatus.approved.value, MembershipApplicationStatus.rejected.value, MembershipApplicationStatus.expired.value}),
    MembershipApplicationStatus.approved.value: frozenset(),
    MembershipApplicationStatus.rejected.value: frozenset(),
    MembershipApplicationStatus.cancelled.value: frozenset(),
    MembershipApplicationStatus.expired.value: frozenset(),
}


class MembershipAccessDenied(PermissionError):
    """Raised when the server cannot prove an actor's membership authority."""


class MembershipStateError(ValueError):
    """Raised when a membership or application transition is not legal."""


class MembershipValidationError(ValueError):
    """Raised when a requested relationship context is invalid."""


class InvitationError(ValueError):
    """Raised for invalid, expired, revoked or replayed invitations."""


class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def relationship_key(
        account_id: str,
        organization_id: str,
        relationship_type: str,
        scope_type: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> str:
        parts = (
            account_id,
            organization_id,
            scope_type,
            relationship_type,
            facility_id or "-",
            department_id or "-",
            unit_id or "-",
            workspace_id or "-",
        )
        return ":".join(parts)

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def transition_membership(membership: Membership, target: MembershipStatus) -> Membership:
        current = str(membership.status)
        if target.value not in LEGAL_MEMBERSHIP_TRANSITIONS.get(current, frozenset()):
            raise MembershipStateError(f"Illegal membership transition: {current} -> {target.value}")
        membership.status = target.value
        membership.version = (membership.version or 1) + 1
        membership.is_active = target in {MembershipStatus.pending, MembershipStatus.invited, MembershipStatus.active, MembershipStatus.suspended}
        return membership

    @staticmethod
    def transition_application(application: MembershipApplication, target: MembershipApplicationStatus) -> MembershipApplication:
        current = str(application.status)
        if target.value not in LEGAL_APPLICATION_TRANSITIONS.get(current, frozenset()):
            raise MembershipStateError(f"Illegal application transition: {current} -> {target.value}")
        application.status = target.value
        application.version = (application.version or 1) + 1
        return application

    async def _audit(
        self,
        action: AuditAction,
        actor_id: str | None,
        target_type: str,
        target_id: str | None,
        organization_id: str | None,
        metadata: dict | None = None,
        outcome: str = "success",
    ) -> None:
        await AuditService(self.session).record(
            action,
            actor_id=actor_id,
            actor_type="account",
            target_type=target_type,
            target_id=target_id,
            organization_id=organization_id,
            decision="deny" if outcome == "denied" else "allow",
            reason_code=(metadata or {}).get("reason_code") or (metadata or {}).get("reason"),
            source="niam_membership",
            metadata=metadata,
            outcome=outcome,
        )

    async def _require_active_account(self, account_id: str) -> Account:
        result = await self.session.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if account is None or account.status != AccountStatus.active.value or not account.is_active:
            raise MembershipAccessDenied("Account is not active")
        return account

    async def _validate_context(
        self,
        organization_id: str,
        scope_type: str,
        facility_id: str | None,
        department_id: str | None,
        unit_id: str | None,
        workspace_id: str | None,
    ) -> None:
        organization = await self.session.scalar(select(NIAMOrganization).where(NIAMOrganization.id == organization_id))
        if organization is None or organization.status != "active" or not organization.is_active:
            raise MembershipValidationError("Organization is not active")

        expected = {
            MembershipScopeType.organization.value: (False, False, False, False),
            MembershipScopeType.facility.value: (True, False, False, False),
            MembershipScopeType.department.value: (True, True, False, False),
            MembershipScopeType.unit.value: (True, True, True, False),
            MembershipScopeType.workspace.value: (False, False, False, True),
        }.get(scope_type)
        if expected is None:
            raise MembershipValidationError("Unsupported membership scope")
        required = (facility_id is not None, department_id is not None, unit_id is not None, workspace_id is not None)
        if required != expected:
            raise MembershipValidationError("Scope identifiers do not match scope_type")

        if facility_id:
            facility = await self.session.scalar(select(NIAMAdminFacility).where(NIAMAdminFacility.id == facility_id))
            if facility is None or facility.organization_id != organization_id or not facility.is_active:
                raise MembershipValidationError("Facility is outside the organization context")
        if department_id:
            department = await self.session.scalar(select(NIAMAdminDepartment).where(NIAMAdminDepartment.id == department_id))
            if department is None or not department.is_active:
                raise MembershipValidationError("Department is not active")
            if facility_id and department.facility_id != facility_id:
                raise MembershipValidationError("Department is outside the facility context")
        if unit_id:
            unit = await self.session.scalar(select(NIAMAdminUnit).where(NIAMAdminUnit.id == unit_id))
            if unit is None or not unit.is_active:
                raise MembershipValidationError("Unit is not active")
            if department_id and unit.department_id != department_id:
                raise MembershipValidationError("Unit is outside the department context")
        if workspace_id:
            workspace = await self.session.scalar(select(Workspace).where(Workspace.id == workspace_id))
            if workspace is None or workspace.organization_id != organization_id:
                raise MembershipValidationError("Workspace is outside the organization context")
            if workspace.status != WorkspaceStatus.active.value:
                raise MembershipValidationError("Workspace is not active")
            if facility_id and workspace.facility_id and workspace.facility_id != facility_id:
                raise MembershipValidationError("Workspace is outside the facility context")

    async def _can_manage_organization(self, actor_id: str, organization_id: str) -> bool:
        try:
            await self._require_active_account(actor_id)
        except MembershipAccessDenied:
            return False
        now = self._now()
        ownership = await self.session.scalar(
            select(OrganizationOwnership.id).where(
                OrganizationOwnership.account_id == actor_id,
                OrganizationOwnership.organization_id == organization_id,
                OrganizationOwnership.status == OwnershipStatus.active.value,
                (OrganizationOwnership.valid_from.is_(None) | (OrganizationOwnership.valid_from <= now)),
                (OrganizationOwnership.expires_at.is_(None) | (OrganizationOwnership.expires_at > now)),
            ).limit(1),
        )
        if ownership:
            return True
        representative = await self.session.scalar(
            select(OrganizationRepresentative.id).where(
                OrganizationRepresentative.account_id == actor_id,
                OrganizationRepresentative.organization_id == organization_id,
                OrganizationRepresentative.status == RepresentativeStatus.active.value,
                (OrganizationRepresentative.valid_from.is_(None) | (OrganizationRepresentative.valid_from <= now)),
                (OrganizationRepresentative.expires_at.is_(None) | (OrganizationRepresentative.expires_at > now)),
            ).limit(1),
        )
        return representative is not None

    async def create_application(
        self,
        account_id: str,
        identity_id: str | None,
        organization_id: str,
        relationship_type: str,
        scope_type: str,
        actor_id: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> MembershipApplication:
        if actor_id != account_id:
            raise MembershipAccessDenied("An application can only be submitted for the authenticated account")
        await self._require_active_account(account_id)
        await self._validate_context(organization_id, scope_type, facility_id, department_id, unit_id, workspace_id)
        key = self.relationship_key(account_id, organization_id, relationship_type, scope_type, facility_id, department_id, unit_id, workspace_id)
        existing = await self.session.scalar(select(MembershipApplication).where(MembershipApplication.application_key == key))
        if existing:
            return existing
        application = MembershipApplication(
            uuid=secrets.token_hex(16),
            application_key=key,
            account_id=account_id,
            identity_id=identity_id,
            organization_id=organization_id,
            facility_id=facility_id,
            department_id=department_id,
            unit_id=unit_id,
            workspace_id=workspace_id,
            relationship_type=relationship_type,
            scope_type=scope_type,
            status=MembershipApplicationStatus.submitted.value,
            submitted_at=self._now(),
        )
        self.session.add(application)
        await self.session.flush()
        await self._audit(AuditAction.membership_application_submitted, account_id, "membership_application", application.id, organization_id, {"scope_type": scope_type})
        return application

    async def approve_application(self, application_id: str, actor_id: str) -> Membership:
        application = await self.session.scalar(select(MembershipApplication).where(MembershipApplication.id == application_id))
        if application is None:
            raise MembershipValidationError("Membership application not found")
        if not await self._can_manage_organization(actor_id, application.organization_id):
            raise MembershipAccessDenied("Actor cannot approve memberships in this organization")
        if application.status == MembershipApplicationStatus.submitted.value:
            self.transition_application(application, MembershipApplicationStatus.under_review)
        self.transition_application(application, MembershipApplicationStatus.approved)
        application.reviewed_by = actor_id
        application.reviewed_at = self._now()
        key = self.relationship_key(application.account_id, application.organization_id, application.relationship_type, application.scope_type, application.facility_id, application.department_id, application.unit_id, application.workspace_id)
        membership = await self.session.scalar(select(Membership).where(Membership.membership_key == key))
        if membership is None:
            membership = Membership(
                uuid=secrets.token_hex(16),
                membership_key=key,
                account_id=application.account_id,
                identity_id=application.identity_id,
                organization_id=application.organization_id,
                facility_id=application.facility_id,
                department_id=application.department_id,
                unit_id=application.unit_id,
                workspace_id=application.workspace_id,
                relationship_type=application.relationship_type,
                scope_type=application.scope_type,
                status=MembershipStatus.pending.value,
                source=MembershipSource.application.value,
                created_by=actor_id,
            )
            self.session.add(membership)
            await self.session.flush()
        if membership.status != MembershipStatus.active.value:
            self.transition_membership(membership, MembershipStatus.active)
        membership.activated_by = actor_id
        membership.activated_at = self._now()
        await self.session.flush()
        await self._audit(AuditAction.membership_application_approved, actor_id, "membership_application", application.id, application.organization_id, {"membership_id": membership.id})
        await self._audit(AuditAction.membership_created, actor_id, "membership", membership.id, membership.organization_id, {"source": membership.source})
        return membership

    async def create_invitation(
        self,
        actor_id: str,
        organization_id: str,
        relationship_type: str,
        scope_type: str,
        recipient_account_id: str | None = None,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
        ttl: timedelta = timedelta(hours=24),
    ) -> tuple[MembershipInvitation, str]:
        if not await self._can_manage_organization(actor_id, organization_id):
            raise MembershipAccessDenied("Actor cannot invite members in this organization")
        await self._validate_context(organization_id, scope_type, facility_id, department_id, unit_id, workspace_id)
        if recipient_account_id:
            await self._require_active_account(recipient_account_id)
        invitation_key = self.relationship_key(recipient_account_id or "unresolved", organization_id, relationship_type, scope_type, facility_id, department_id, unit_id, workspace_id)
        existing = await self.session.scalar(
            select(MembershipInvitation).where(
                MembershipInvitation.invitation_key == invitation_key,
                MembershipInvitation.status == InvitationStatus.pending.value,
                MembershipInvitation.expires_at > self._now(),
            ),
        )
        if existing:
            raise InvitationError("A pending invitation already exists")
        raw_token = secrets.token_urlsafe(32)
        invitation = MembershipInvitation(
            uuid=secrets.token_hex(16),
            invitation_key=invitation_key,
            token_hash=self.token_hash(raw_token),
            recipient_account_id=recipient_account_id,
            organization_id=organization_id,
            facility_id=facility_id,
            department_id=department_id,
            unit_id=unit_id,
            workspace_id=workspace_id,
            relationship_type=relationship_type,
            scope_type=scope_type,
            status=InvitationStatus.pending.value,
            created_by=actor_id,
            expires_at=self._now() + ttl,
        )
        self.session.add(invitation)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise InvitationError("Invitation could not be created idempotently") from exc
        await self._audit(AuditAction.invitation_created, actor_id, "membership_invitation", invitation.id, organization_id, {"expires_at": invitation.expires_at.isoformat()})
        return invitation, raw_token

    async def accept_invitation(self, invitation_id: str, actor_id: str, raw_token: str) -> Membership:
        invitation = await self.session.scalar(
            select(MembershipInvitation)
            .where(MembershipInvitation.id == invitation_id)
            .with_for_update()
        )
        if invitation is None or invitation.status != InvitationStatus.pending.value:
            raise InvitationError("Invitation is not available")
        if invitation.expires_at <= self._now():
            invitation.status = InvitationStatus.expired.value
            invitation.version += 1
            await self.session.flush()
            await self._audit(AuditAction.invitation_expired, actor_id, "membership_invitation", invitation.id, invitation.organization_id, outcome="denied")
            raise InvitationError("Invitation has expired")
        if not secrets.compare_digest(invitation.token_hash, self.token_hash(raw_token)):
            await self._audit(
                AuditAction.invitation_rejected,
                actor_id,
                "membership_invitation",
                invitation.id,
                invitation.organization_id,
                {"reason_code": "invalid_invitation_token"},
                outcome="denied",
            )
            raise InvitationError("Invitation token is invalid")
        if invitation.recipient_account_id and invitation.recipient_account_id != actor_id:
            await self._audit(
                AuditAction.invitation_rejected,
                actor_id,
                "membership_invitation",
                invitation.id,
                invitation.organization_id,
                {"reason_code": "invitation_recipient_mismatch"},
                outcome="denied",
            )
            raise InvitationError("Invitation recipient mismatch")
        account = await self._require_active_account(actor_id)
        key = self.relationship_key(actor_id, invitation.organization_id, invitation.relationship_type, invitation.scope_type, invitation.facility_id, invitation.department_id, invitation.unit_id, invitation.workspace_id)
        membership = await self.session.scalar(select(Membership).where(Membership.membership_key == key))
        if membership is None:
            membership = Membership(
                uuid=secrets.token_hex(16),
                membership_key=key,
                account_id=account.id,
                identity_id=account.identity_id,
                organization_id=invitation.organization_id,
                facility_id=invitation.facility_id,
                department_id=invitation.department_id,
                unit_id=invitation.unit_id,
                workspace_id=invitation.workspace_id,
                relationship_type=invitation.relationship_type,
                scope_type=invitation.scope_type,
                status=MembershipStatus.invited.value,
                source=MembershipSource.invitation.value,
                created_by=invitation.created_by,
            )
            self.session.add(membership)
            await self.session.flush()
        self.transition_membership(membership, MembershipStatus.active)
        membership.activated_by = actor_id
        membership.activated_at = self._now()
        invitation.status = InvitationStatus.accepted.value
        invitation.accepted_at = self._now()
        invitation.membership_id = membership.id
        invitation.version += 1
        await self.session.flush()
        await self._audit(AuditAction.invitation_accepted, actor_id, "membership_invitation", invitation.id, invitation.organization_id, {"membership_id": membership.id})
        await self._audit(AuditAction.membership_accepted, actor_id, "membership", membership.id, membership.organization_id, {"source": membership.source})
        return membership

    async def revoke_membership(self, membership_id: str, actor_id: str, reason: str | None = None) -> Membership:
        membership = await self.session.scalar(select(Membership).where(Membership.id == membership_id))
        if membership is None:
            raise MembershipValidationError("Membership not found")
        if not await self._can_manage_organization(actor_id, membership.organization_id):
            raise MembershipAccessDenied("Actor cannot revoke memberships in this organization")
        self.transition_membership(membership, MembershipStatus.revoked)
        membership.revoked_at = self._now()
        membership.revocation_reason = reason
        await self.session.flush()
        await self._audit(AuditAction.membership_revoked, actor_id, "membership", membership.id, membership.organization_id, {"reason": reason})
        await revoke_account_access(
            self.session,
            account_id=membership.account_id,
            actor_id=actor_id,
            organization_id=membership.organization_id,
            facility_id=membership.facility_id,
            workspace_id=membership.workspace_id,
            reason_code="membership_revoked",
        )
        return membership

    async def suspend_membership(self, membership_id: str, actor_id: str, reason: str | None = None) -> Membership:
        membership = await self.session.scalar(select(Membership).where(Membership.id == membership_id))
        if membership is None:
            raise MembershipValidationError("Membership not found")
        if not await self._can_manage_organization(actor_id, membership.organization_id):
            raise MembershipAccessDenied("Actor cannot suspend memberships in this organization")
        self.transition_membership(membership, MembershipStatus.suspended)
        membership.suspended_at = self._now()
        membership.revocation_reason = reason
        await self.session.flush()
        await self._audit(AuditAction.membership_suspended, actor_id, "membership", membership.id, membership.organization_id, {"reason": reason})
        await revoke_account_access(
            self.session,
            account_id=membership.account_id,
            actor_id=actor_id,
            organization_id=membership.organization_id,
            facility_id=membership.facility_id,
            workspace_id=membership.workspace_id,
            reason_code="membership_suspended",
        )
        return membership

    async def reactivate_membership(self, membership_id: str, actor_id: str) -> Membership:
        membership = await self.session.scalar(select(Membership).where(Membership.id == membership_id))
        if membership is None:
            raise MembershipValidationError("Membership not found")
        if not await self._can_manage_organization(actor_id, membership.organization_id):
            raise MembershipAccessDenied("Actor cannot reactivate memberships in this organization")
        self.transition_membership(membership, MembershipStatus.active)
        membership.suspended_at = None
        membership.revocation_reason = None
        membership.activated_by = actor_id
        membership.activated_at = self._now()
        await self.session.flush()
        await self._audit(AuditAction.membership_reactivated, actor_id, "membership", membership.id, membership.organization_id)
        return membership

    async def revoke_invitation(self, invitation_id: str, actor_id: str) -> MembershipInvitation:
        invitation = await self.session.scalar(select(MembershipInvitation).where(MembershipInvitation.id == invitation_id))
        if invitation is None:
            raise InvitationError("Invitation not found")
        if not await self._can_manage_organization(actor_id, invitation.organization_id):
            raise MembershipAccessDenied("Actor cannot revoke invitations in this organization")
        if invitation.status != InvitationStatus.pending.value:
            raise InvitationError("Invitation is not pending")
        invitation.status = InvitationStatus.revoked.value
        invitation.revoked_at = self._now()
        invitation.version += 1
        await self.session.flush()
        await self._audit(AuditAction.invitation_revoked, actor_id, "membership_invitation", invitation.id, invitation.organization_id)
        return invitation

    async def list_for_account(self, account_id: str) -> list[Membership]:
        await self._require_active_account(account_id)
        result = await self.session.execute(
            select(Membership).where(
                Membership.account_id == account_id,
                Membership.status.in_([MembershipStatus.pending.value, MembershipStatus.invited.value, MembershipStatus.active.value, MembershipStatus.suspended.value]),
            ).order_by(Membership.created_at.desc()),
        )
        memberships = list(result.scalars().all())
        now = self._now()
        expired_memberships: list[Membership] = []
        for membership in memberships:
            if membership.expires_at and membership.expires_at <= now and membership.status in {MembershipStatus.pending.value, MembershipStatus.invited.value, MembershipStatus.active.value, MembershipStatus.suspended.value}:
                self.transition_membership(membership, MembershipStatus.expired)
                membership.revoked_at = now
                expired_memberships.append(membership)
                await self._audit(
                    AuditAction.membership_expired,
                    account_id,
                    "membership",
                    membership.id,
                    membership.organization_id,
                    {"reason_code": "membership_expired"},
                    outcome="success",
                )
        if expired_memberships:
            await revoke_account_access(
                self.session,
                account_id=account_id,
                actor_id=account_id,
                organization_id=expired_memberships[0].organization_id,
                reason_code="membership_expired",
            )
        await self.session.flush()
        return memberships
