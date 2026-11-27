"""National Clinical Integration Layer — synthetic, composition-only.

This module wires the existing canonical services into one bounded chain:

    Citizen Identity -> Health Identity -> Patient/MPI -> Clinical Encounter
    -> Laboratory Order -> Specimen -> Processing -> Result Validation
    -> Clinical Record (FHIR R4) -> Authorized Citizen Access

It is deliberately a *composition* layer:

* no new identity, patient, MPI, LIMS, FHIR, consent, audit, or event store;
* no route, migration, DDL, trigger, production config, or government connector;
* no real national identifier, card image, raw NFC payload, or real patient data;
* no substitute for the canonical Authorization Decision Engine.

Every unresolved condition fails closed. Synthetic identifiers must use the
bounded ``synthetic-`` prefix enforced by :mod:`app.lab_slice.models`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, NoReturn

from sqlalchemy import or_, select

from app._compat import UTC
from app.identity.models.authorization import (
    CatalogStatus,
    Role,
    RoleAssignment,
    RoleAssignmentStatus,
)
from app.identity.models.citizen_relationship import CitizenRelationship, CitizenRelationshipStatus
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecision,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.identity.services.consent_service_v2 import NiamConsentService
from app.identity.services.phi_permission_map import (
    PHI_RESOURCE_TYPES,
    resolve_phi_permission,
)
from app.integration.fhir_r4_exchange import FHIRContractError, validate_synthetic_bundle
from app.lab_slice.decision_engine import assess_result, authorize_release, reject_release
from app.lab_slice.event_pipeline import PipelineSummary, SyntheticLabEventPipeline
from app.lab_slice.fhir_projector import build_bundle
from app.lab_slice.models import (
    RELEASE_PENDING,
    RELEASE_QUARANTINED,
    RELEASE_RELEASED,
    ReleaseDecision,
    SyntheticLabCase,
    require_synthetic_id,
)
from app.lab_slice.terminology_bindings import bind_test
from app.lims.events import LIMSEvent, ResultValidated
from app.national.enums import EncounterStatus
from app.national.fhir.validation import FHIRValidationEngine
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.national.services.identity_access import (
    PATIENT_LINKAGE,
    IdentityAccessContext,
    IdentityAccessGrant,
    IdentityRole,
    assert_identity_access_v2,
)
from app.national.services.identity_governance import LinkageReviewer
from app.national.services.patient_identity_safety import (
    FacilityIdentityRecord,
    PatientSafetyAction,
    cross_facility_linkage_decision,
)
from app.services.mpi.identity_safety import NID_CONFLICT, classify_nid_match
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

SYNTHETIC_INTEGRATION_SOURCE = "national_clinical_integration_synthetic"

# Derived from the canonical role's allowed field set in identity_access.py;
# the composition layer requests only the references needed for this chain.
_CLINICAL_ACCESS_FIELDS = (
    "gula_citizen_identifier",
    "patient_record_reference",
    "facility_id",
)

STAGE_IDENTITY = "citizen_identity"
STAGE_HEALTH = "health_identity"
STAGE_PATIENT = "patient_mpi"
STAGE_ENCOUNTER = "clinical_encounter"
STAGE_ORDER = "laboratory_order"
STAGE_SPECIMEN = "specimen"
STAGE_PROCESSING = "laboratory_processing"
STAGE_VALIDATION = "result_validation"
STAGE_RECORD = "clinical_record"
STAGE_ACCESS = "authorized_citizen_access"


class ClinicalIntegrationError(RuntimeError):
    """Base bounded failure for the integration chain."""


class ClinicalIntegrationDenied(ClinicalIntegrationError):
    """An actor, scope, consent, or policy gate denied the operation."""


class ClinicalIntegrationConflict(ClinicalIntegrationError):
    """Identity, record, event, or referral data conflicts."""


class ClinicalIntegrationIncomplete(ClinicalIntegrationError):
    """A required chain artifact or reference is missing."""


@dataclass(frozen=True, slots=True)
class IntegrationStage:
    name: str
    status: str
    reference: str | None = None
    detail: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class IdentityLinkageOutcome:
    primary_identifier: str
    secondary_identifier: str
    action: str
    reasons: tuple[str, ...]
    reviewer: str
    evidence_reference: str
    nid_disposition: str


@dataclass(frozen=True, slots=True)
class ChainBinding:
    patient_reference: str
    encounter_reference: str
    order_id: str
    specimen_id: str
    result_id: str
    gula_citizen_identifier: str
    national_id_hash: str
    nid_disposition: str


@dataclass(frozen=True, slots=True)
class AuthorizedAccessOutcome:
    decision: AuthorizationDecision
    consent_id: str
    patient_reference: str
    result_id: str | None
    identity_grant: IdentityAccessGrant
    identity_audit_event: AuditEventInput
    audit_event: AuditEventInput
    projected_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IntegratedClinicalRecord:
    correlation_id: str
    organization_id: str
    facility_id: str
    stages: tuple[IntegrationStage, ...]
    linkage: IdentityLinkageOutcome
    binding: ChainBinding
    decision: ReleaseDecision
    bundle: dict[str, Any] | None
    event_summary: PipelineSummary | None
    access: AuthorizedAccessOutcome | None
    quarantined: bool


def _bounded(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ClinicalIntegrationIncomplete(f"{name} must be a bounded non-empty string")
    return value


class NationalClinicalIntegration:
    """Compose canonical services into one synthetic clinical chain.

    The instance records only stage outcomes; it does not own domain records.
    All domain records remain in the canonical services and the caller's
    synthetic fixtures.
    """

    def __init__(
        self,
        *,
        correlation_id: str,
        organization_id: str,
        facility_id: str,
        reviewer: str,
        review_reason: str,
        release_idempotency_key: str,
        event_idempotency_key: str,
        catalog: NationalLaboratoryCatalog | None = None,
        delta_engine: DeltaCheckEngine | None = None,
        event_pipeline: SyntheticLabEventPipeline | None = None,
    ) -> None:
        self.correlation_id = _bounded(correlation_id, "correlation_id")
        self.organization_id = _bounded(organization_id, "organization_id")
        self.facility_id = _bounded(facility_id, "facility_id")
        self.reviewer = require_synthetic_id(reviewer, "reviewer")
        self.review_reason = _bounded(review_reason, "review_reason")
        self.release_idempotency_key = _bounded(release_idempotency_key, "release_idempotency_key")
        self.event_idempotency_key = _bounded(event_idempotency_key, "event_idempotency_key")
        self.catalog = catalog or NationalLaboratoryCatalog()
        if not self.catalog.count().get("tests", 0):
            self.catalog.seed_common_tests()
        self.delta_engine = delta_engine or DeltaCheckEngine()
        self.event_pipeline = event_pipeline or SyntheticLabEventPipeline()
        self._published_event_keys: set[str] = set()
        self._stages: list[IntegrationStage] = []

    @property
    def stages(self) -> tuple[IntegrationStage, ...]:
        return tuple(self._stages)

    def _record(
        self,
        name: str,
        status: str,
        *,
        reference: str | None = None,
        detail: Sequence[str] = (),
    ) -> None:
        self._stages.append(
            IntegrationStage(name=name, status=status, reference=reference, detail=tuple(detail)),
        )

    # -- Stage 1 and 2: citizen identity -> health identity -----------------
    def link_health_identity(
        self,
        primary: FacilityIdentityRecord,
        secondary: FacilityIdentityRecord,
        *,
        decision: str = "APPROVED",
        reviewer: LinkageReviewer,
        reason: str,
        evidence_reference: str,
        decided_at: datetime | None = None,
    ) -> IdentityLinkageOutcome:
        """Link two facility identities only through the canonical guard.

        Facility records keep distinct GULA identifiers until an authorized
        reviewer explicitly links them; this never merges the records.
        """
        if reviewer.name != self.reviewer:
            raise ClinicalIntegrationDenied("linkage reviewer is not the configured reviewer")
        if primary.gula_citizen_identifier == secondary.gula_citizen_identifier:
            raise ClinicalIntegrationConflict("facility records must be distinct before linkage")
        safety = cross_facility_linkage_decision(
            primary,
            secondary,
            decision=decision,
            reviewer=reviewer,
            reason=reason,
            evidence_reference=evidence_reference,
            decided_at=decided_at or datetime.now(UTC),
        )
        if safety.action in {PatientSafetyAction.BLOCKED, PatientSafetyAction.PENDING_REVIEW}:
            raise ClinicalIntegrationConflict(
                f"identity linkage {safety.action.value}: {safety.reasons}"
            )
        if safety.action is not PatientSafetyAction.LINK_APPROVED:
            raise ClinicalIntegrationConflict(
                f"identity linkage not approved: {safety.action.value}"
            )
        if safety.merged:
            raise ClinicalIntegrationConflict("automatic merge is prohibited")
        outcome = IdentityLinkageOutcome(
            primary_identifier=safety.primary_identifier,
            secondary_identifier=safety.secondary_identifier,
            action=safety.action.value,
            reasons=safety.reasons,
            reviewer=reviewer.name,
            evidence_reference=evidence_reference,
            nid_disposition=str(safety.audit_metadata.get("nid_disposition", "unknown")),
        )
        self._record(STAGE_IDENTITY, "RESOLVED", reference=outcome.primary_identifier)
        self._record(
            STAGE_HEALTH,
            "LINK_APPROVED",
            reference=outcome.secondary_identifier,
            detail=outcome.reasons,
        )
        return outcome

    # -- Stages 3-6: patient/MPI, encounter, order and specimen binding -----
    def bind_chain(
        self,
        case: SyntheticLabCase,
        *,
        patient_reference: str,
        encounter_reference: str,
        gula_citizen_identifier: str,
        encounter: Any | None = None,
        national_id_hash: str,
        linkage: IdentityLinkageOutcome | None = None,
        profile_hash: str | None = None,
        candidate_hash: str | None = None,
        candidate_verified: bool = False,
        corroborated: bool = False,
    ) -> ChainBinding:
        """Bind the result to one patient/order/specimen with no conflict."""
        patient_reference = require_synthetic_id(patient_reference, "patient_reference")
        encounter_reference = require_synthetic_id(encounter_reference, "encounter_reference")
        if patient_reference != case.patient.patient_id:
            raise ClinicalIntegrationConflict("patient reference does not match the case patient")
        if encounter is not None:
            expected_encounter_reference = f"synthetic-encounter-{str(encounter.id)[:8].lower()}"
            if encounter_reference != expected_encounter_reference:
                raise ClinicalIntegrationConflict(
                    "encounter reference does not match the canonical encounter"
                )
            if str(encounter.patient_id) != patient_reference:
                raise ClinicalIntegrationConflict(
                    "encounter patient does not match the chain patient"
                )
            if str(encounter.organization_id) != self.organization_id:
                raise ClinicalIntegrationConflict("encounter organization is outside scope")
            if str(encounter.facility_id) != self.facility_id:
                raise ClinicalIntegrationConflict("encounter facility is outside scope")
            if getattr(encounter, "status", None) is not EncounterStatus.COMPLETED:
                raise ClinicalIntegrationConflict("encounter is not completed")
        if case.order.patient_id != case.patient.patient_id:
            raise ClinicalIntegrationConflict("order patient does not match the patient record")
        if case.specimen.patient_id != case.patient.patient_id:
            raise ClinicalIntegrationConflict("specimen patient does not match the patient record")
        if case.specimen.order_id != case.order.order_id:
            raise ClinicalIntegrationConflict("specimen order does not match the order")
        if case.result.patient_id != case.patient.patient_id:
            raise ClinicalIntegrationConflict("result patient does not match the patient record")
        if (
            case.result.order_id != case.order.order_id
            or case.result.specimen_id != case.specimen.specimen_id
        ):
            raise ClinicalIntegrationConflict("result references are inconsistent")

        profile = profile_hash if profile_hash is not None else national_id_hash
        candidate = candidate_hash if candidate_hash is not None else national_id_hash
        classification = classify_nid_match(
            profile_hash=profile,
            candidate_hash=candidate,
            candidate_verified=candidate_verified,
            corroborated=corroborated,
        )
        if classification.disposition == NID_CONFLICT:
            raise ClinicalIntegrationConflict("NID conflict blocks patient linkage")
        if linkage is not None:
            if linkage.reviewer != self.reviewer:
                raise ClinicalIntegrationDenied("linkage outcome reviewer is not configured")
            if gula_citizen_identifier not in {
                linkage.primary_identifier,
                linkage.secondary_identifier,
            }:
                raise ClinicalIntegrationConflict("binding is not bound to the linked identities")

        binding = ChainBinding(
            patient_reference=patient_reference,
            encounter_reference=encounter_reference,
            order_id=case.order.order_id,
            specimen_id=case.specimen.specimen_id,
            result_id=case.result.result_id,
            gula_citizen_identifier=gula_citizen_identifier,
            national_id_hash=national_id_hash,
            nid_disposition=str(classification.disposition),
        )
        self._record(STAGE_PATIENT, "BOUND", reference=patient_reference)
        self._record(STAGE_ENCOUNTER, "BOUND", reference=encounter_reference)
        self._record(STAGE_ORDER, "BOUND", reference=binding.order_id)
        self._record(STAGE_SPECIMEN, "BOUND", reference=binding.specimen_id)
        return binding

    # -- Stages 7 and 8: processing and result validation ------------------
    def validate_and_release(self, case: SyntheticLabCase) -> ReleaseDecision:
        """Assess a result and allow only an explicit human release."""
        binding = bind_test(self.catalog, case.result.test_code)
        decision = assess_result(
            order=case.order,
            specimen=case.specimen,
            result=case.result,
            qc=case.qc,
            binding=binding,
            delta_engine=self.delta_engine,
        )
        self._record(
            STAGE_PROCESSING,
            "COMPLETED" if decision.status == RELEASE_PENDING else "QUARANTINED",
            reference=case.result.result_id,
            detail=decision.reasons,
        )
        if decision.status == RELEASE_QUARANTINED:
            self._record(
                STAGE_VALIDATION,
                "QUARANTINED",
                reference=decision.decision_id,
                detail=decision.reasons,
            )
            return decision
        if decision.status != RELEASE_PENDING:
            raise ClinicalIntegrationIncomplete(f"unexpected release decision: {decision.status}")
        released = authorize_release(
            decision,
            reviewer=self.reviewer,
            reason=self.review_reason,
            idempotency_key=self.release_idempotency_key,
        )
        if released.status != RELEASE_RELEASED or released.reviewer != self.reviewer:
            raise ClinicalIntegrationDenied(
                "result was not released by an authorized human reviewer"
            )
        self._record(
            STAGE_VALIDATION,
            "RELEASED",
            reference=released.decision_id,
            detail=released.reasons,
        )
        return released

    def reject_result(self, decision: ReleaseDecision, *, reason: str) -> ReleaseDecision:
        """Explicitly reject a non-released decision; quarantines stay quarantined."""
        rejected = reject_release(decision, reason=_bounded(reason, "reason"))
        self._record(STAGE_VALIDATION, "REJECTED", reference=rejected.decision_id)
        return rejected

    # -- Stage 9: clinical record projection -------------------------------
    def project_clinical_record(
        self,
        case: SyntheticLabCase,
        decision: ReleaseDecision,
    ) -> dict[str, Any]:
        """Project a released result into a validated FHIR R4 bundle."""
        if decision.result_id != case.result.result_id:
            raise ClinicalIntegrationConflict("release decision belongs to a different result")
        if decision.status != RELEASE_RELEASED:
            raise ClinicalIntegrationDenied("only a released result can become a clinical record")
        binding = bind_test(self.catalog, case.result.test_code)
        try:
            bundle = build_bundle(
                patient=case.patient,
                order=case.order,
                specimen=case.specimen,
                result=case.result,
                decision=decision,
                binding=binding,
            )
            contract_errors = validate_synthetic_bundle(bundle)
            if contract_errors:
                raise FHIRContractError("; ".join(contract_errors))
            validator = FHIRValidationEngine()
            for entry in bundle["entry"]:
                result = validator.validate(entry["resource"])
                if not result.valid:
                    raise FHIRContractError(f"{entry['resource']['resourceType']}: {result.errors}")
        except FHIRContractError as exc:
            raise ClinicalIntegrationConflict(f"FHIR R4 projection failed: {exc}") from exc
        serialized = json.dumps(bundle, sort_keys=True)
        if "national_id" in serialized or case.patient.patient_id not in serialized:
            raise ClinicalIntegrationConflict("FHIR bundle binding or redaction check failed")
        self._record(STAGE_RECORD, "PROJECTED", reference=str(bundle["id"]))
        return bundle

    # -- Event path: deduplication through the existing LIMS pipeline ------
    def publish_result_event(
        self, case: SyntheticLabCase, decision: ReleaseDecision
    ) -> PipelineSummary:
        """Publish and process the canonical LIMS result event exactly once.

        The pipeline is owned by the integration instance so replay and
        restart-with-injected-pipeline are deduplicated by the same
        store-forward state rather than a fresh in-memory object per call.
        """
        if decision.result_id != case.result.result_id:
            raise ClinicalIntegrationConflict("release decision belongs to a different result")
        if decision.status != RELEASE_RELEASED:
            raise ClinicalIntegrationDenied("unreleased results cannot emit a validated event")
        expected = f"{case.result.result_id}-{ResultValidated.event_type}"
        idempotency_key = f"{self.event_idempotency_key}:{case.result.result_id}"
        if (
            idempotency_key in self._published_event_keys
            or expected in self.event_pipeline._processed
        ):
            self._record(STAGE_RECORD, "EVENT_DUPLICATE", reference=expected)
            return PipelineSummary(
                delivered=(),
                duplicates=(expected,),
                conflicts=(),
                queue_status=self.event_pipeline.store_forward.queue_size(),
            )
        event = LIMSEvent(
            event_type=ResultValidated.event_type,
            aggregate_id=case.result.result_id,
            aggregate_type="Result",
            payload={"version": 1, "idempotency_key": self.event_idempotency_key},
            timestamp=datetime.now(UTC).isoformat(),
        )
        self.event_pipeline.publish(event)
        summary = self.event_pipeline.process()
        if summary.delivered == (expected,):
            self._published_event_keys.add(idempotency_key)
            self._record(STAGE_RECORD, "EVENT_DELIVERED", reference=summary.delivered[0])
            return summary
        if summary.duplicates == (expected,):
            self._published_event_keys.add(idempotency_key)
            self._record(STAGE_RECORD, "EVENT_DUPLICATE", reference=summary.duplicates[0])
            return summary
        raise ClinicalIntegrationConflict(f"result event was not delivered: {summary}")

    # -- Stage 10: authorized citizen access -------------------------------
    async def _canonical_identity_evidence(
        self,
        session: Any,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
        now: datetime,
    ) -> tuple[IdentityRole, str, AuthorizationRequest]:
        """Derive identity role and patient relationship from canonical NIAM data."""
        try:
            role_result = await session.execute(
                select(Role.role_key)
                .join(RoleAssignment, RoleAssignment.role_id == Role.id)
                .where(
                    RoleAssignment.account_id == actor.account.id,
                    RoleAssignment.organization_id == request.organization_id,
                    or_(
                        RoleAssignment.facility_id.is_(None),
                        RoleAssignment.facility_id == request.facility_id,
                    ),
                    RoleAssignment.status == RoleAssignmentStatus.active.value,
                    or_(
                        RoleAssignment.expires_at.is_(None),
                        RoleAssignment.expires_at > now,
                    ),
                    Role.status == CatalogStatus.active.value,
                ),
            )
            role_keys = tuple(dict.fromkeys(role_result.scalars().all()))
        except Exception as exc:
            await self._deny_access(
                session,
                request,
                "CANONICAL_ROLE_LOOKUP_FAILURE",
                f"canonical role lookup failed: {type(exc).__name__}",
            )
        if len(role_keys) != 1:
            await self._deny_access(
                session,
                request,
                "IDENTITY_ROLE_NOT_UNIQUE",
                "identity role is not uniquely assigned",
            )
        try:
            role = IdentityRole(role_keys[0])
        except ValueError:
            await self._deny_access(
                session,
                request,
                "IDENTITY_ROLE_UNSUPPORTED",
                "assigned identity role is not approved for clinical access",
            )

        try:
            relationship_result = await session.execute(
                select(CitizenRelationship).where(
                    CitizenRelationship.canonical_account_id == actor.account.id,
                    CitizenRelationship.status == CitizenRelationshipStatus.active.value,
                    or_(
                        CitizenRelationship.expires_at.is_(None),
                        CitizenRelationship.expires_at > now,
                    ),
                ),
            )
            write = request.action not in {"read", "list", "view"}
            eligible = [
                relationship
                for relationship in relationship_result.scalars().all()
                if relationship.patient_id == request.resource_id
                and relationship.purpose == request.purpose
                and relationship.is_active_at(now)
                and relationship.allows(request.resource_type, write=write)
            ]
            relationship_type = (
                _bounded(eligible[0].relationship_type, "relationship_type") if eligible else ""
            )
        except Exception as exc:
            await self._deny_access(
                session,
                request,
                "CANONICAL_RELATIONSHIP_LOOKUP_FAILURE",
                f"canonical patient relationship lookup failed: {type(exc).__name__}",
            )
        if len(eligible) != 1:
            await self._deny_access(
                session,
                request,
                "PATIENT_RELATIONSHIP_NOT_VERIFIED",
                "patient relationship is not uniquely verified for this access",
            )
        return role, relationship_type, replace(request, relationship_type=relationship_type)

    async def _deny_access(
        self,
        session: Any,
        request: AuthorizationRequest,
        reason_code: str,
        message: str,
    ) -> NoReturn:
        """Write a canonical denial audit event before every fail-closed exit."""
        event = AuditEventInput(
            event_type="NATIONAL_CLINICAL_ACCESS_DENIED",
            category="AUTHORIZATION",
            action=f"{request.resource_type}.{request.action}",
            actor_id=request.subject_account_id,
            organization_id=request.organization_id,
            facility_id=request.facility_id,
            target_type=request.resource_type,
            target_id=request.resource_id,
            decision="DENY",
            reason_code=reason_code,
            request_id=self.correlation_id,
            correlation_id=self.correlation_id,
            source=SYNTHETIC_INTEGRATION_SOURCE,
            data_classification="SENSITIVE",
            metadata={"reason": message},
        )
        try:
            await CanonicalAuditService(session).record(event)
        except Exception as exc:
            raise ClinicalIntegrationDenied(
                f"canonical audit failure on denial: {type(exc).__name__}"
            ) from exc
        raise ClinicalIntegrationDenied(message)

    async def authorize_citizen_access(
        self,
        session: Any,
        *,
        actor: AuthorizationActor,
        request: AuthorizationRequest,
        consent_id: str,
        citizen_account_id: str,
        expected_gula_identifier: str,
        national_id_hash: str,
        binding: ChainBinding | None = None,
        now: datetime | None = None,
    ) -> AuthorizedAccessOutcome:
        """Run ADE, consent, identity guards, and canonical audit in order.

        Every trusted binding comes from the configured instance, canonical
        NIAM role/relationship records, the ADE decision object, the verified
        consent record, or the composed chain binding. Caller-supplied scope
        overrides, purpose overrides, prebuilt identity contexts, and loose
        role/relationship declarations are not accepted.
        """
        clean_consent_id = _bounded(consent_id, "consent_id")
        clean_citizen = _bounded(citizen_account_id, "citizen_account_id")
        clean_gula = _bounded(expected_gula_identifier, "expected_gula_identifier")
        clean_hash = _bounded(national_id_hash, "national_id_hash")
        if binding is not None:
            if binding.patient_reference != request.resource_id:
                await self._deny_access(
                    session,
                    request,
                    "PATIENT_BINDING_MISMATCH",
                    "authorized patient does not match the clinical chain binding",
                )
            if binding.gula_citizen_identifier != clean_gula:
                await self._deny_access(
                    session,
                    request,
                    "CITIZEN_BINDING_MISMATCH",
                    "authorized citizen does not match the clinical chain binding",
                )
        try:
            require_synthetic_id(request.resource_id or "", "resource_id")
        except ValueError as exc:
            await self._deny_access(session, request, "RESOURCE_REFERENCE_INVALID", str(exc))
        if request.organization_id != self.organization_id:
            await self._deny_access(
                session, request, "ORGANIZATION_SCOPE_MISMATCH", "organization scope mismatch"
            )
        if request.facility_id != self.facility_id:
            await self._deny_access(
                session, request, "FACILITY_SCOPE_MISMATCH", "facility scope mismatch"
            )
        if request.resource_context.get("organization_id") != request.organization_id:
            await self._deny_access(
                session,
                request,
                "RESOURCE_ORGANIZATION_MISMATCH",
                "resource organization context mismatch",
            )
        if request.resource_context.get("facility_id") != request.facility_id:
            await self._deny_access(
                session, request, "RESOURCE_FACILITY_MISMATCH", "resource facility context mismatch"
            )
        if not request.purpose:
            await self._deny_access(
                session, request, "PURPOSE_REQUIRED", "authorization purpose is required"
            )

        if (
            request.resource_type in PHI_RESOURCE_TYPES
            and resolve_phi_permission(request.resource_type, request.action) is None
        ):
            await self._deny_access(session, request, "UNMAPPED_PHI_ACTION", "unmapped PHI action")

        effective_now = now or datetime.now(UTC)
        role, patient_relationship, request = await self._canonical_identity_evidence(
            session,
            actor,
            request,
            effective_now,
        )
        decision = await AuthorizationDecisionService(session).authorize(
            actor,
            request,
            now=effective_now,
        )
        if not decision.allowed:
            await self._deny_access(
                session,
                request,
                decision.reason_code.value,
                f"canonical authorization denied: {decision.reason_code.value}",
            )

        consent = await NiamConsentService(session).check(
            actor_account_id=actor.account.id,
            consent_id=clean_consent_id,
            now=effective_now,
        )
        if consent is None:
            await self._deny_access(
                session, request, "CONSENT_INVALID", "consent is absent or invalid"
            )
        scope = consent.scope
        if not isinstance(scope, Mapping):
            await self._deny_access(
                session, request, "CONSENT_SCOPE_INVALID", "consent scope is invalid"
            )
        if consent.resource_domain != request.resource_type:
            await self._deny_access(
                session, request, "CONSENT_DOMAIN_MISMATCH", "consent resource domain mismatch"
            )
        if scope.get("resource_domain") != request.resource_type:
            await self._deny_access(
                session,
                request,
                "CONSENT_SCOPE_DOMAIN_MISMATCH",
                "consent scope resource domain mismatch",
            )
        if request.action not in scope.get("actions", ()):
            await self._deny_access(
                session, request, "CONSENT_ACTION_MISSING", "consent action was not granted"
            )
        if consent.purpose != request.purpose:
            await self._deny_access(
                session, request, "CONSENT_PURPOSE_MISMATCH", "consent purpose mismatch"
            )
        if consent.subject_account_id != clean_citizen:
            await self._deny_access(
                session, request, "CONSENT_SUBJECT_MISMATCH", "consent subject is not the citizen"
            )
        if consent.grantee_account_id != actor.account.id:
            await self._deny_access(
                session, request, "CONSENT_GRANTEE_MISMATCH", "consent grantee is not the actor"
            )
        if scope.get("patient_reference") != request.resource_id:
            await self._deny_access(
                session, request, "CONSENT_PATIENT_MISMATCH", "consent patient reference mismatch"
            )
        if scope.get("gula_citizen_identifier") != clean_gula:
            await self._deny_access(
                session, request, "CONSENT_CITIZEN_MISMATCH", "consent citizen identifier mismatch"
            )

        identity_context = IdentityAccessContext(
            decision=decision,
            role=role,
            actor_id=actor.account.id,
            organization_id=request.organization_id,
            facility_id=request.facility_id,
            purpose=request.purpose,
            action=PATIENT_LINKAGE,
            requested_fields=_CLINICAL_ACCESS_FIELDS,
            gula_citizen_identifier=clean_gula,
            national_id_hash=clean_hash,
            now=effective_now,
            consent_required=True,
            consent_present=True,
            relationship_required=True,
            patient_relationship=patient_relationship,
            break_glass=False,
            break_glass_authorized=False,
        )
        try:
            grant = assert_identity_access_v2(identity_context)
        except Exception as exc:
            await self._deny_access(
                session, request, "IDENTITY_ACCESS_DENIED", f"identity access guard denied: {exc}"
            )
        projected_fields = grant.allowed_fields

        event = AuditEventInput(
            event_type="NATIONAL_CLINICAL_ACCESS",
            category="AUTHORIZATION",
            action=f"{request.resource_type}.{request.action}",
            actor_id=actor.account.id,
            organization_id=request.organization_id,
            facility_id=request.facility_id,
            target_type=request.resource_type,
            target_id=request.resource_id,
            decision="ALLOW",
            reason_code=decision.reason_code.value,
            request_id=self.correlation_id,
            correlation_id=self.correlation_id,
            source=SYNTHETIC_INTEGRATION_SOURCE,
            data_classification="SENSITIVE",
            metadata={
                "consent_id": clean_consent_id,
                "consent_purpose": consent.purpose,
                "citizen_account_id": clean_citizen,
                "gula_citizen_identifier": clean_gula,
                "patient_reference": request.resource_id,
                "identity_role": role.value,
                "patient_relationship": patient_relationship,
                "chain_result_id": binding.result_id if binding is not None else None,
                "identity_operation": grant.action,
                "allowed_fields": list(projected_fields),
            },
        )
        try:
            audit = CanonicalAuditService(session)
            await audit.record(grant.audit_event)
            await audit.record(event)
        except Exception as exc:  # fail closed on audit failure (S-05)
            raise ClinicalIntegrationDenied(
                f"canonical audit failure: {type(exc).__name__}"
            ) from exc

        self._record(STAGE_ACCESS, "AUTHORIZED", reference=request.resource_id)
        return AuthorizedAccessOutcome(
            decision=decision,
            consent_id=clean_consent_id,
            patient_reference=request.resource_id or "",
            result_id=binding.result_id if binding is not None else None,
            identity_grant=grant,
            identity_audit_event=grant.audit_event,
            audit_event=event,
            projected_fields=tuple(projected_fields),
        )

    # -- Full composition --------------------------------------------------
    def build_record(
        self,
        *,
        linkage: IdentityLinkageOutcome,
        binding: ChainBinding,
        decision: ReleaseDecision,
        bundle: dict[str, Any] | None,
        event_summary: PipelineSummary | None,
        access: AuthorizedAccessOutcome | None,
    ) -> IntegratedClinicalRecord:
        """Assemble immutable evidence for the composed chain."""
        if decision.result_id != binding.result_id:
            raise ClinicalIntegrationConflict("release decision does not match the chain binding")
        if access is not None:
            if access.patient_reference != binding.patient_reference:
                raise ClinicalIntegrationConflict("access is bound to a different patient")
            if access.result_id != binding.result_id:
                raise ClinicalIntegrationConflict("access is bound to a different result")
        if bundle is not None:
            serialized = json.dumps(bundle, sort_keys=True)
            if binding.patient_reference not in serialized or binding.result_id not in serialized:
                raise ClinicalIntegrationConflict(
                    "clinical record does not match the chain binding"
                )
        if event_summary is not None:
            expected = f"{binding.result_id}-{ResultValidated.event_type}"
            if expected not in (*event_summary.delivered, *event_summary.duplicates):
                raise ClinicalIntegrationConflict("result event does not match the chain binding")
        return IntegratedClinicalRecord(
            correlation_id=self.correlation_id,
            organization_id=self.organization_id,
            facility_id=self.facility_id,
            stages=self.stages,
            linkage=linkage,
            binding=binding,
            decision=decision,
            bundle=bundle,
            event_summary=event_summary,
            access=access,
            quarantined=decision.status == RELEASE_QUARANTINED,
        )

    async def record_linkage_audit(
        self,
        session: Any,
        outcome: IdentityLinkageOutcome,
        binding: ChainBinding,
    ) -> AuditEventInput:
        """Persist the redacted linkage event through canonical audit only."""
        if outcome.reviewer != self.reviewer:
            raise ClinicalIntegrationDenied("linkage audit reviewer is not configured")
        event = self.audit_event_for_linkage(outcome, binding)
        try:
            await CanonicalAuditService(session).record(event)
        except Exception as exc:
            raise ClinicalIntegrationDenied(
                f"canonical linkage audit failure: {type(exc).__name__}"
            ) from exc
        return event

    def audit_event_for_linkage(
        self,
        outcome: IdentityLinkageOutcome,
        binding: ChainBinding,
    ) -> AuditEventInput:
        """Build a canonical, redacted audit event for patient linkage."""
        from app.national.services.identity_access import build_wave053_audit_event

        return build_wave053_audit_event(
            operation=PATIENT_LINKAGE,
            actor_id=self.reviewer,
            purpose="TREATMENT",
            facility_id=self.facility_id,
            organization_id=self.organization_id,
            gula_citizen_identifier=binding.gula_citizen_identifier,
            national_id_hash=binding.national_id_hash,
            metadata={
                "patient_reference": binding.patient_reference,
                "encounter_reference": binding.encounter_reference,
                "order_id": binding.order_id,
                "specimen_id": binding.specimen_id,
                "linkage_action": outcome.action,
                "nid_disposition": outcome.nid_disposition,
                "reviewer": outcome.reviewer,
                "evidence_reference": outcome.evidence_reference,
                "correlation_id": self.correlation_id,
            },
            correlation_id=self.correlation_id,
            raw_nid_values=(
                outcome.reviewer,
                outcome.evidence_reference,
                binding.patient_reference,
                binding.encounter_reference,
            ),
        )
