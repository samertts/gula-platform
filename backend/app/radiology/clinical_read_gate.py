"""Synchronous, deny-by-default gate for clinical radiology reads.

The existing radiology router is synchronous, while NIAM's context service is
asynchronous.  This gate deliberately queries the same persisted evidence in a
synchronous transaction and delegates policy semantics to
``ClinicalPolicyEvaluator``.  It never treats a legacy ``lab_id`` as a
facility identifier.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.identity.models.account import Account
from app.identity.models.assignment import Assignment
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import LegacyAccountLink
from app.identity.models.policy import IdentityPolicy
from app.identity.services.clinical_policy_evaluator import ClinicalPolicyEvaluator
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant
from app.services.audit_service import log_action


class ClinicalRadiologyReadDenied(Exception):
    """A non-enumerating denial for a clinical read request."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ClinicalRadiologyReadContext:
    legacy_lab_id: int
    facility_resource_id: int
    organization_resource_id: int
    tenant_id: int
    person_id: str
    assignment_id: str
    mapping_version: int


class ClinicalRadiologyReadGate:
    """Resolve a proven clinical scope before allowing a radiology read."""

    permission = "clinical.radiology.order.read"
    resource_type = "clinical_radiology_read"

    def authorize(self, *, db: Session, lab_user) -> ClinicalRadiologyReadContext:
        try:
            return self._resolve(db=db, lab_user=lab_user)
        except ClinicalRadiologyReadDenied as denial:
            self._audit(db=db, lab_user=lab_user, decision="denied", reason=denial.reason)
            raise

    def _resolve(self, *, db: Session, lab_user) -> ClinicalRadiologyReadContext:
        links = (
            db.query(LegacyAccountLink)
            .filter(
                LegacyAccountLink.source_kind == "lab_user",
                LegacyAccountLink.legacy_account_id == lab_user.id,
                LegacyAccountLink.status == "migrated",
            )
            .all()
        )
        if len(links) != 1 or not links[0].canonical_account_id:
            raise ClinicalRadiologyReadDenied("legacy_identity_unresolved")

        account = db.get(Account, links[0].canonical_account_id)
        if not account or account.status != "active" or not account.is_active or account.is_locked:
            raise ClinicalRadiologyReadDenied("canonical_account_unavailable")

        identity = db.get(IdentityRecord, account.identity_id)
        if not identity or identity.status != "active" or not identity.is_active:
            raise ClinicalRadiologyReadDenied("canonical_identity_unavailable")

        bindings = (
            db.query(ClinicalLabFacilityBinding)
            .filter(
                ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,
                ClinicalLabFacilityBinding.status == "active",
            )
            .all()
        )
        if len(bindings) != 1:
            raise ClinicalRadiologyReadDenied("facility_scope_unavailable")
        binding = bindings[0]

        facility = db.get(Facility, binding.facility_resource_id)
        if not facility or not facility.is_active:
            raise ClinicalRadiologyReadDenied("facility_unavailable")
        organization = db.get(Organization, facility.organization_id)
        if not organization or not organization.is_active or not organization.tenant_id:
            raise ClinicalRadiologyReadDenied("organization_unavailable")
        tenant = db.get(Tenant, organization.tenant_id)
        if not tenant or not tenant.is_active:
            raise ClinicalRadiologyReadDenied("tenant_unavailable")

        assignments = (
            db.query(Assignment)
            .filter(
                Assignment.person_id == identity.person_id,
                Assignment.status == "active",
                Assignment.is_active.is_(True),
                Assignment.clinical_organization_resource_id == organization.id,
                Assignment.clinical_facility_resource_id == facility.id,
            )
            .all()
        )
        if len(assignments) != 1:
            raise ClinicalRadiologyReadDenied("active_assignment_unavailable")

        policies = (
            db.query(IdentityPolicy)
            .filter(
                IdentityPolicy.is_active.is_(True),
                IdentityPolicy.is_enabled.is_(True),
            )
            .all()
        )
        if not ClinicalPolicyEvaluator.allows(
            policies=policies,
            assignments=assignments,
            person_id=identity.person_id,
            permission=self.permission,
            organization_id=str(organization.id),
            facility_resource_id=facility.id,
        ):
            raise ClinicalRadiologyReadDenied("permission_denied")

        context = ClinicalRadiologyReadContext(
            legacy_lab_id=lab_user.lab_id,
            facility_resource_id=facility.id,
            organization_resource_id=organization.id,
            tenant_id=tenant.id,
            person_id=identity.person_id,
            assignment_id=assignments[0].id,
            mapping_version=binding.mapping_version,
        )
        self._audit(db=db, lab_user=lab_user, decision="allowed", reason="policy_granted", context=context)
        return context

    def _audit(
        self,
        *,
        db: Session,
        lab_user,
        decision: str,
        reason: str,
        context: ClinicalRadiologyReadContext | None = None,
    ) -> None:
        details = {
            "decision": decision,
            "reason": reason,
            "permission": self.permission,
            "lab_id": getattr(lab_user, "lab_id", None),
        }
        if context:
            details.update(
                {
                    "tenant_id": context.tenant_id,
                    "organization_resource_id": context.organization_resource_id,
                    "facility_resource_id": context.facility_resource_id,
                    "assignment_id": context.assignment_id,
                    "mapping_version": context.mapping_version,
                }
            )
        log_action(
            db,
            action=f"{self.permission}.{decision}",
            resource_type=self.resource_type,
            resource_id=None,
            user_id=getattr(lab_user, "id", None),
            user_role=getattr(lab_user, "role", None),
            details=json.dumps(details, sort_keys=True),
        )
