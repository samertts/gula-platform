from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.audit import AuditAction
from app.identity.models.authorization import CatalogStatus, Permission
from app.identity.models.citizen_relationship import CitizenRelationship
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.policy import IdentityPolicy
from app.identity.models.session import UserSession
from app.identity.models.verification_record import VerificationRecord
from app.identity.services.audit_service import AuditService
from app.identity.services.authorization_service_v2 import RolePermissionService


class AuthorizationDecisionValue(StrEnum):
    allow = "allow"
    deny = "deny"


class AuthorizationReason(StrEnum):
    allowed = "ALLOWED"
    unauthenticated = "UNAUTHENTICATED"
    actor_mismatch = "ACTOR_MISMATCH"
    account_inactive = "ACCOUNT_INACTIVE"
    session_invalid = "SESSION_INVALID"
    membership_unresolved = "MEMBERSHIP_UNRESOLVED"
    membership_inactive = "MEMBERSHIP_INACTIVE"
    membership_scope_mismatch = "MEMBERSHIP_SCOPE_MISMATCH"
    organization_authority_required = "ORGANIZATION_AUTHORITY_REQUIRED"
    role_unresolved = "ROLE_UNRESOLVED"
    permission_unknown = "PERMISSION_UNKNOWN"
    permission_missing = "PERMISSION_MISSING"
    resource_unresolved = "RESOURCE_UNRESOLVED"
    cross_tenant_denied = "CROSS_TENANT_DENIED"
    workspace_boundary_denied = "WORKSPACE_BOUNDARY_DENIED"
    scope_mismatch = "SCOPE_MISMATCH"
    relationship_required = "RELATIONSHIP_REQUIRED"
    relationship_denied = "RELATIONSHIP_DENIED"
    professional_verification_required = "PROFESSIONAL_VERIFICATION_REQUIRED"
    resource_state_denied = "RESOURCE_STATE_DENIED"
    step_up_required = "STEP_UP_REQUIRED"
    purpose_required = "PURPOSE_REQUIRED"
    purpose_invalid = "PURPOSE_INVALID"
    break_glass_workflow_required = "BREAK_GLASS_WORKFLOW_REQUIRED"
    policy_denied = "POLICY_DENIED"
    policy_evaluation_failed = "POLICY_EVALUATION_FAILED"
    audit_failure = "AUDIT_FAILURE"
    internal_failure = "INTERNAL_FAILURE"


@dataclass(frozen=True)
class AuthorizationActor:
    """Trusted server-side actor context derived by get_current_niam_actor."""

    account: Account
    session: UserSession


@dataclass(frozen=True)
class AuthorizationRequest:
    """Internal request; protected routes must construct it from trusted server data."""

    subject_account_id: str
    action: str
    resource_type: str
    resource_id: str | None = None
    permission_key: str | None = None
    organization_id: str | None = None
    facility_id: str | None = None
    department_id: str | None = None
    unit_id: str | None = None
    workspace_id: str | None = None
    membership_id: str | None = None
    relationship_type: str | None = None
    purpose: str | None = None
    purpose_validated: bool = False
    sensitivity: str = "medium"
    resource_status: str | None = None
    resource_context: Mapping[str, Any] = field(default_factory=dict)
    environment: Mapping[str, Any] = field(default_factory=dict)
    required_assurance: str | None = None
    break_glass: bool = False
    break_glass_authorized: bool = False

    @property
    def effective_permission(self) -> str:
        return self.permission_key or f"{self.resource_type}.{self.action}"


@dataclass(frozen=True)
class AuthorizationDecision:
    decision: AuthorizationDecisionValue
    reason_code: AuthorizationReason
    policy_id: str | None = None
    policy_version: str | None = None
    required_assurance: str | None = None
    audit_reference: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision is AuthorizationDecisionValue.allow

    @classmethod
    def allow(
        cls,
        *,
        policy_id: str | None = None,
        policy_version: str | None = None,
        audit_reference: str | None = None,
    ) -> AuthorizationDecision:
        return cls(
            decision=AuthorizationDecisionValue.allow,
            reason_code=AuthorizationReason.allowed,
            policy_id=policy_id,
            policy_version=policy_version,
            audit_reference=audit_reference,
        )

    @classmethod
    def deny(
        cls,
        reason: AuthorizationReason,
        *,
        policy_id: str | None = None,
        policy_version: str | None = None,
        required_assurance: str | None = None,
        audit_reference: str | None = None,
    ) -> AuthorizationDecision:
        return cls(
            decision=AuthorizationDecisionValue.deny,
            reason_code=reason,
            policy_id=policy_id,
            policy_version=policy_version,
            required_assurance=required_assurance,
            audit_reference=audit_reference,
        )

    def public(self) -> dict[str, object | None]:
        """Return a bounded response that does not expose policy internals."""
        return {
            "decision": self.decision.value,
            "reason_code": self.reason_code.value,
            "required_assurance": self.required_assurance,
        }


class AuthorizationDecisionService:
    """Central server-side RBAC + contextual + relationship authorization."""

    ALLOWED_PURPOSES = frozenset(
        {
            "TREATMENT",
            "DIAGNOSIS",
            "LABORATORY_PROCESSING",
            "PHARMACY_DISPENSING",
            "ADMINISTRATION",
            "BILLING",
            "AUDIT",
            "RESEARCH",
            "PUBLIC_HEALTH",
            "citizen_workspace",
        },
    )
    NON_ORGANIZATIONAL_READS = frozenset({"role_catalog", "permission_catalog"})
    SENSITIVE_ACTIONS = frozenset(
        {
            "export",
            "delete",
            "approve",
            "assign",
            "revoke",
            "transfer",
            "identity_change",
            "security_change",
        },
    )

    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)

    def authorize(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        """Evaluate in a fixed order and fail closed on every unresolved condition."""
        try:
            decision = self._evaluate(actor, request)
        except Exception:
            decision = AuthorizationDecision.deny(AuthorizationReason.internal_failure)

        if self._should_audit(request, decision):
            decision = self._audit_decision(actor, request, decision)
        return decision

    def _evaluate(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
    ) -> AuthorizationDecision:
        account = actor.account
        session = actor.session
        now = datetime.now(UTC)

        if not request.subject_account_id or account.id != request.subject_account_id:
            return AuthorizationDecision.deny(AuthorizationReason.actor_mismatch)
        if account.status != AccountStatus.active.value or not account.is_active or account.is_locked:
            return AuthorizationDecision.deny(AuthorizationReason.account_inactive)
        if session.account_id != account.id or not session.is_active or session.expires_at <= now:
            return AuthorizationDecision.deny(AuthorizationReason.session_invalid)

        if request.break_glass:
            if not request.break_glass_authorized:
                return AuthorizationDecision.deny(AuthorizationReason.break_glass_workflow_required)
            if not request.environment.get("break_glass_reason") or not request.environment.get("break_glass_expires_at"):
                return AuthorizationDecision.deny(AuthorizationReason.break_glass_workflow_required)
            if not session.mfa_used:
                return AuthorizationDecision.deny(
                    AuthorizationReason.step_up_required,
                    required_assurance="MFA",
                )

        if request.purpose is not None and (
            request.purpose not in self.ALLOWED_PURPOSES or not request.purpose_validated
        ):
            return AuthorizationDecision.deny(AuthorizationReason.purpose_invalid)
        required_purpose = request.resource_context.get("required_purpose")
        if required_purpose is not None and request.purpose != required_purpose:
            return AuthorizationDecision.deny(AuthorizationReason.purpose_required)

        if request.resource_status in {"ARCHIVED", "REVOKED", "DELETED"} and request.action not in {"read", "audit"}:
            return AuthorizationDecision.deny(AuthorizationReason.resource_state_denied)

        management_authority = self._has_management_authority(actor, request)
        if self._requires_management_authority(request) and not management_authority:
            return AuthorizationDecision.deny(AuthorizationReason.organization_authority_required)
        membership = self._resolve_membership(actor, request)
        if membership is None and not management_authority and request.resource_type not in self.NON_ORGANIZATIONAL_READS:
            return AuthorizationDecision.deny(AuthorizationReason.membership_unresolved)

        if membership is not None:
            scope_failure = self._check_scope(request, membership)
            if scope_failure is not None:
                return AuthorizationDecision.deny(scope_failure)

        resource_failure = self._check_resource_context(request)
        if resource_failure is not None:
            return AuthorizationDecision.deny(resource_failure)

        if request.relationship_type is not None:
            if not self._relationship_allows(actor, request):
                return AuthorizationDecision.deny(AuthorizationReason.relationship_denied)
        elif request.resource_context.get("relationship_required"):
            return AuthorizationDecision.deny(AuthorizationReason.relationship_required)

        if request.resource_context.get("professional_verification_required") and not self._professional_verification_exists(
            account.id,
            account.identity_id,
        ):
            return AuthorizationDecision.deny(AuthorizationReason.professional_verification_required)

        if self._requires_step_up(request) and not session.mfa_used:
            return AuthorizationDecision.deny(
                AuthorizationReason.step_up_required,
                required_assurance="MFA",
            )

        permission_key = request.effective_permission
        permissions = set()
        if membership is not None and request.organization_id:
            permissions = RolePermissionService(self.session).effective_permissions(
                account.id,
                request.organization_id,
                facility_id=request.facility_id,
                department_id=request.department_id,
                unit_id=request.unit_id,
                workspace_id=request.workspace_id,
            )
        if request.resource_type not in self.NON_ORGANIZATIONAL_READS and not management_authority:
            if not self._permission_exists(permission_key):
                return AuthorizationDecision.deny(AuthorizationReason.permission_unknown)
            if permission_key not in permissions:
                return AuthorizationDecision.deny(AuthorizationReason.permission_missing)

        policy = self._matching_policy(actor, request, membership)
        if policy is not None and policy.effect.lower() == "deny":
            return AuthorizationDecision.deny(
                AuthorizationReason.policy_denied,
                policy_id=policy.policy_id,
                policy_version=policy.version,
            )

        return AuthorizationDecision.allow(
            policy_id=policy.policy_id if policy is not None else None,
            policy_version=policy.version if policy is not None else None,
        )

    @staticmethod
    def _requires_management_authority(request: AuthorizationRequest) -> bool:
        return request.resource_type in {"role", "membership", "membership_application", "membership_invitation"} and request.action in {
            "assign",
            "revoke",
            "invite",
            "approve",
            "suspend",
            "reactivate",
        }

    def _has_management_authority(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
    ) -> bool:
        if not self._requires_management_authority(request) or not request.organization_id:
            return False
        return self._can_manage_organization(actor.account.id, request.organization_id)

    def _can_manage_organization(self, account_id: str, organization_id: str) -> bool:
        from app.identity.services.membership_service import MembershipService

        return MembershipService(self.session)._can_manage_organization(account_id, organization_id)

    def _resolve_membership(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
    ) -> Membership | None:
        if request.resource_type in self.NON_ORGANIZATIONAL_READS and request.organization_id is None:
            return None
        if not request.organization_id:
            return None
        conditions = [
            Membership.account_id == actor.account.id,
            Membership.organization_id == request.organization_id,
            Membership.status == MembershipStatus.active.value,
            Membership.is_active.is_(True),
        ]
        if request.membership_id:
            conditions.append(Membership.id == request.membership_id)
        result = self.session.execute(select(Membership).where(*conditions))
        memberships = [item for item in result.scalars().all() if not item.expires_at or item.expires_at > datetime.now(UTC)]
        matching = [item for item in memberships if self._check_scope(request, item) is None]
        if not matching:
            return None
        highest_score = max(self._scope_specificity(item) for item in matching)
        highest = [item for item in matching if self._scope_specificity(item) == highest_score]
        if len(highest) != 1:
            return None
        return highest[0]

    @staticmethod
    def _scope_specificity(membership: Membership) -> int:
        return sum(
            getattr(membership, key) is not None
            for key in ("facility_id", "department_id", "unit_id", "workspace_id")
        )

    @staticmethod
    def _check_scope(request: AuthorizationRequest, membership: Membership) -> AuthorizationReason | None:
        resource_scope = request.resource_context
        if membership.organization_id != request.organization_id:
            return AuthorizationReason.cross_tenant_denied

        scope_fields = ("facility_id", "department_id", "unit_id", "workspace_id")
        for key in scope_fields:
            requested = resource_scope.get(key, getattr(request, key))
            membership_value = getattr(membership, key, None)
            if requested is None or membership_value is None or membership_value == requested:
                continue
            if key == "workspace_id":
                return AuthorizationReason.workspace_boundary_denied
            return AuthorizationReason.scope_mismatch
        return None

    @staticmethod
    def _check_resource_context(request: AuthorizationRequest) -> AuthorizationReason | None:
        if request.resource_id is not None and request.resource_context.get("exists") is not True:
            return AuthorizationReason.resource_unresolved
        for key in ("organization_id", "facility_id", "department_id", "unit_id", "workspace_id"):
            request_value = getattr(request, key)
            resource_value = request.resource_context.get(key)
            if request_value is not None and resource_value is not None and request_value != resource_value:
                if key == "organization_id":
                    return AuthorizationReason.cross_tenant_denied
                if key == "workspace_id":
                    return AuthorizationReason.workspace_boundary_denied
                return AuthorizationReason.scope_mismatch
        return None

    def _permission_exists(self, permission_key: str) -> bool:
        permission = self.session.scalar(
            select(Permission.id).where(
                Permission.permission_key == permission_key,
                Permission.status == CatalogStatus.active.value,
            ),
        )
        return permission is not None

    def _relationship_allows(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
    ) -> bool:
        resource_context = request.resource_context
        patient_id = resource_context.get("patient_id")
        citizen_id = resource_context.get("citizen_id")
        if patient_id is None and citizen_id is None:
            return False
        statement = select(CitizenRelationship).where(
            CitizenRelationship.canonical_account_id == actor.account.id,
            CitizenRelationship.relationship_type == request.relationship_type,
            CitizenRelationship.status == "active",
        )
        result = self.session.execute(statement)
        for relationship in result.scalars().all():
            if not relationship.is_active_at():
                continue
            if request.purpose is not None and relationship.purpose != request.purpose:
                continue
            if not relationship.allows(
                request.resource_type,
                write=request.action not in {"read", "list", "view"},
            ):
                continue
            if patient_id is not None and relationship.patient_id == patient_id:
                return True
            if citizen_id is not None and relationship.citizen_id == citizen_id:
                return True
        return False

    def _professional_verification_exists(self, account_id: str, identity_id: str) -> bool:
        now = datetime.now(UTC)
        statement = select(VerificationRecord.id).where(
            VerificationRecord.account_id == account_id,
            VerificationRecord.identity_id == identity_id,
            VerificationRecord.record_type == "professional",
            VerificationRecord.status == "verified",
            VerificationRecord.is_active.is_(True),
            or_(VerificationRecord.valid_from.is_(None), VerificationRecord.valid_from <= now),
            or_(VerificationRecord.expires_at.is_(None), VerificationRecord.expires_at > now),
        )
        result = self.session.scalar(statement)
        return result is not None

    def _requires_step_up(self, request: AuthorizationRequest) -> bool:
        return request.required_assurance == "MFA" or (
            request.sensitivity in {"high", "critical"}
            and (
                request.action in self.SENSITIVE_ACTIONS
                or request.resource_type in {"clinical_record", "patient_export", "clinical_export"}
            )
        )

    def _matching_policy(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
        membership: Membership | None,
    ) -> IdentityPolicy | None:
        policies = self.session.execute(
            select(IdentityPolicy).where(
                IdentityPolicy.is_active.is_(True),
                IdentityPolicy.is_enabled.is_(True),
            ),
        )
        context: dict[str, Any] = {
            "account_id": actor.account.id,
            "organization_id": request.organization_id,
            "facility_id": request.facility_id,
            "department_id": request.department_id,
            "workspace_id": request.workspace_id,
            "membership_id": membership.id if membership else None,
            "relationship_type": request.relationship_type,
            "purpose": request.purpose,
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "action": request.action,
        }
        matches = [
            policy
            for policy in policies.scalars().all()
            if self._policy_matches(policy, request, context)
        ]
        if not matches:
            return None
        return sorted(
            matches,
            key=lambda item: (item.effect.lower() != "deny", -item.priority),
        )[0]

    @staticmethod
    def _policy_matches(
        policy: IdentityPolicy,
        request: AuthorizationRequest,
        context: Mapping[str, Any],
    ) -> bool:
        actions = policy.actions if isinstance(policy.actions, list) else []
        resources = policy.resources if isinstance(policy.resources, list) else []
        action_match = request.action in actions or "*" in actions or request.effective_permission in actions
        resource_match = request.resource_type in resources or "*" in resources
        if not action_match or not resource_match:
            return False
        for mapping in (policy.subjects, policy.conditions):
            if not isinstance(mapping, dict):
                continue
            for key, expected in mapping.items():
                actual = context.get(key)
                if isinstance(expected, list) and actual not in expected:
                    return False
                if not isinstance(expected, list) and actual != expected:
                    return False
        if policy.start_at and policy.start_at > datetime.now(UTC):
            return False
        return not policy.end_at or policy.end_at > datetime.now(UTC)

    def _should_audit(self, request: AuthorizationRequest, decision: AuthorizationDecision) -> bool:
        return decision.decision is AuthorizationDecisionValue.deny or request.sensitivity in {"high", "critical"} or request.action in self.SENSITIVE_ACTIONS

    def _audit_decision(
        self,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
        decision: AuthorizationDecision,
    ) -> AuthorizationDecision:
        if decision.allowed:
            action = AuditAction.authz_allow_sensitive.value
        elif decision.reason_code is AuthorizationReason.policy_evaluation_failed or decision.reason_code is AuthorizationReason.internal_failure:
            action = AuditAction.authz_policy_failure.value
        elif decision.reason_code is AuthorizationReason.cross_tenant_denied:
            action = AuditAction.authz_cross_tenant_attempt.value
        elif decision.reason_code in {
            AuthorizationReason.permission_missing,
            AuthorizationReason.actor_mismatch,
            AuthorizationReason.role_unresolved,
        }:
            action = AuditAction.authz_privilege_escalation_attempt.value
        else:
            action = AuditAction.authz_deny.value
        metadata = {
            "action": request.action,
            "resource_type": request.resource_type,
            "resource_id": request.resource_id,
            "decision": decision.decision.value,
            "reason_code": decision.reason_code.value,
            "required_assurance": decision.required_assurance,
            "authentication_assurance": "MFA" if actor.session.mfa_used else "SESSION",
        }
        try:
            entry = self.audit.record_event(
                action=action,
                actor_id=actor.account.id,
                target_type=request.resource_type,
                target_id=request.resource_id,
                organization_id=request.organization_id,
                metadata=metadata,
                outcome="success" if decision.allowed else "denied",
            )
        except Exception:
            if decision.allowed:
                return AuthorizationDecision.deny(AuthorizationReason.audit_failure)
            return decision
        return AuthorizationDecision(
            decision=decision.decision,
            reason_code=decision.reason_code,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            required_assurance=decision.required_assurance,
            audit_reference=entry.id,
        )
