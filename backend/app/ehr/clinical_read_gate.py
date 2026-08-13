"""Deny-by-default guard for a single facility-scoped EHR note read."""

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
from app.models.clinical_scope import ClinicalEhrFacilityBinding, ClinicalLabFacilityBinding
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant
from app.services.audit_service import log_action


class ClinicalEhrReadDenied(Exception):
    """A non-enumerating denial for a facility-scoped EHR note request."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ClinicalEhrReadContext:
    legacy_lab_id: int
    national_facility_id: str
    facility_resource_id: int
    organization_resource_id: int
    tenant_id: int
    person_id: str
    assignment_id: str
    lab_mapping_version: int
    ehr_mapping_version: int


class ClinicalEhrReadGate:
    """Prove canonical identity, both scope bridges, assignment, and exact policy."""

    permission = "clinical.ehr.record.read"
    resource_type = "clinical_ehr_record_read"

    def authorize(self, *, db: Session, lab_user, national_facility_id: str) -> ClinicalEhrReadContext:
        try:
            return self._resolve(db=db, lab_user=lab_user, national_facility_id=national_facility_id)
        except ClinicalEhrReadDenied as denial:
            self._audit(db=db, lab_user=lab_user, decision="denied", reason=denial.reason)
            raise

    def _resolve(self, *, db: Session, lab_user, national_facility_id: str) -> ClinicalEhrReadContext:
        if not isinstance(national_facility_id, str) or not national_facility_id.strip():
            raise ClinicalEhrReadDenied("ehr_facility_scope_unavailable")
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
            raise ClinicalEhrReadDenied("legacy_identity_unresolved")
        account = db.get(Account, links[0].canonical_account_id)
        if not account or account.status != "active" or not account.is_active or account.is_locked:
            raise ClinicalEhrReadDenied("canonical_account_unavailable")
        identity = db.get(IdentityRecord, account.identity_id)
        if not identity or identity.status != "active" or not identity.is_active:
            raise ClinicalEhrReadDenied("canonical_identity_unavailable")

        lab_bindings = (
            db.query(ClinicalLabFacilityBinding)
            .filter(
                ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,
                ClinicalLabFacilityBinding.status == "active",
            )
            .all()
        )
        if len(lab_bindings) != 1:
            raise ClinicalEhrReadDenied("lab_facility_scope_unavailable")
        lab_binding = lab_bindings[0]

        ehr_bindings = (
            db.query(ClinicalEhrFacilityBinding)
            .filter(
                ClinicalEhrFacilityBinding.national_facility_id == national_facility_id,
                ClinicalEhrFacilityBinding.status == "active",
            )
            .all()
        )
        if len(ehr_bindings) != 1:
            raise ClinicalEhrReadDenied("ehr_facility_scope_unavailable")
        ehr_binding = ehr_bindings[0]
        if ehr_binding.facility_resource_id != lab_binding.facility_resource_id:
            raise ClinicalEhrReadDenied("facility_scope_mismatch")

        facility = db.get(Facility, ehr_binding.facility_resource_id)
        if not facility or not facility.is_active:
            raise ClinicalEhrReadDenied("facility_unavailable")
        organization = db.get(Organization, facility.organization_id)
        if not organization or not organization.is_active or not organization.tenant_id:
            raise ClinicalEhrReadDenied("organization_unavailable")
        tenant = db.get(Tenant, organization.tenant_id)
        if not tenant or not tenant.is_active:
            raise ClinicalEhrReadDenied("tenant_unavailable")

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
            raise ClinicalEhrReadDenied("active_assignment_unavailable")
        policies = (
            db.query(IdentityPolicy)
            .filter(IdentityPolicy.is_active.is_(True), IdentityPolicy.is_enabled.is_(True))
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
            raise ClinicalEhrReadDenied("permission_denied")
        context = ClinicalEhrReadContext(
            legacy_lab_id=lab_user.lab_id,
            national_facility_id=national_facility_id,
            facility_resource_id=facility.id,
            organization_resource_id=organization.id,
            tenant_id=tenant.id,
            person_id=identity.person_id,
            assignment_id=assignments[0].id,
            lab_mapping_version=lab_binding.mapping_version,
            ehr_mapping_version=ehr_binding.mapping_version,
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
        context: ClinicalEhrReadContext | None = None,
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
                    "lab_mapping_version": context.lab_mapping_version,
                    "ehr_mapping_version": context.ehr_mapping_version,
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
