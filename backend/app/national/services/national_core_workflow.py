"""Synthetic national core workflow facade.

This module composes the completed Phase 1 citizen registration lifecycle with
the existing synthetic ``NationalClinicalIntegration`` chain. It is an additive
service-layer facade only:

* no HTTP route, national router mount, migration, DDL, trigger, or schema change;
* no database, external broker, government connector, production credential, or
  real citizen/patient data;
* no second identity, MPI, LIMS, FHIR, audit, event, or metrics engine;
* no activation of medical access and no production readiness claim.

The facade accepts tightly bound authorization decisions from a trusted
server-side caller, domain objects created by canonical services, and an
in-memory persistence adapter. All unresolved identity, authorization, consent,
audit, and clinical-safety conditions fail closed. Offline store-forward
failure is reported as non-blocking continuity evidence, never as a clinical
safety gate. All identifiers used by tests and examples must remain synthetic.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Any

from app._compat import UTC
from app.clinical.observability import clinical_safety_metrics, reason_code
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecision,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.integration.offline import OfflineQueueEntry, OfflineSyncEngine, StoreForwardEngine
from app.lab_slice.event_pipeline import PipelineSummary, SyntheticLabEventPipeline
from app.lab_slice.models import (
    RELEASE_QUARANTINED,
    RELEASE_RELEASED,
    SyntheticLabCase,
    require_synthetic_id,
)
from app.national.clinical_integration import (
    ChainBinding,
    IdentityLinkageOutcome,
    IntegratedClinicalRecord,
    NationalClinicalIntegration,
)
from app.national.intelligence.laboratory.analytics import DeltaCheckEngine
from app.national.services.citizen_registration import (
    ActorType,
    CitizenRegistrationAccount,
    InMemoryRegistrationAccountStore,
    InMemoryRegistrationTransitionStore,
    MedicalDataAccessDeniedError,
    RegistrationContext,
    RegistrationLifecycleService,
    assert_medical_data_access_allowed,
)
from app.national.services.document_authenticity import NidpEvidenceBundle
from app.national.services.identity_access import IdentityRole
from app.national.services.identity_governance import LinkageCandidate, LinkageReviewer
from app.national.services.identity_persistence import (
    InMemoryIdempotencyStore,
    RegistrationRequest,
)
from app.national.services.patient_identity_safety import FacilityIdentityRecord
from app.platform.sync import SyncService
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

WORKFLOW_SCHEMA = "national_core_workflow.v1.synthetic"
WORKFLOW_SOURCE = "national_core_workflow_synthetic"
WORKFLOW_LAYERS: tuple[str, ...] = (
    "Citizen/Staff Interface",
    "Contract",
    "Authorization",
    "Domain Services",
    "Canonical Identity/MPI",
    "Clinical/Laboratory Services",
    "Persistence Adapter",
    "Event/Audit",
    "Observability",
    "End-to-End Tests",
)
_METRIC_OPERATION = "national_core_workflow"
_CITIZEN_METRIC_OPERATION = "national_core_citizen_access"
_HEX_HASH = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_RAW_NID_RUN = re.compile(r"(?<!\d)\d{9,18}(?!\d)")


class NationalCoreWorkflowError(RuntimeError):
    """Base bounded failure for the national core facade."""


class NationalCoreWorkflowReplayError(NationalCoreWorkflowError):
    """A workflow key was reused with different decision inputs."""


# -- Interface contracts ----------------------------------------------------


@dataclass(frozen=True, slots=True)
class NationalCoreRegistrationInput:
    """Synthetic citizen/staff registration command payload."""

    idempotency_key: str
    subject_reference: str
    contact_reference: str
    contact_code: str
    evidence: NidpEvidenceBundle

    def __post_init__(self) -> None:
        for label, value in (
            ("idempotency_key", self.idempotency_key),
            ("subject_reference", self.subject_reference),
            ("contact_reference", self.contact_reference),
            ("contact_code", self.contact_code),
        ):
            _bounded(value, label)


@dataclass(frozen=True, slots=True)
class NationalCoreIdentityInput:
    """Protected cross-facility view used by canonical MPI safety guards."""

    primary_facility_id: str
    secondary_facility_id: str
    primary_local_patient_id: str
    secondary_local_patient_id: str
    secondary_gula_citizen_identifier: str
    linkage_evidence_reference: str
    national_id_hash: str
    birth_year: int
    birth_month: int
    birth_day: int
    phone_last10: str
    secondary_nid_hash: str | None = None
    nid_verified: bool = True

    def __post_init__(self) -> None:
        for label, value in (
            ("primary_facility_id", self.primary_facility_id),
            ("secondary_facility_id", self.secondary_facility_id),
            ("primary_local_patient_id", self.primary_local_patient_id),
            ("secondary_local_patient_id", self.secondary_local_patient_id),
            ("secondary_gula_citizen_identifier", self.secondary_gula_citizen_identifier),
            ("linkage_evidence_reference", self.linkage_evidence_reference),
        ):
            _bounded(value, label)
        if re.fullmatch(r"\d{10}", self.phone_last10) is None:
            raise NationalCoreWorkflowError("phone_last10 must be a protected 10-digit suffix")
        _hash(self.national_id_hash, "national_id_hash")
        if self.secondary_nid_hash is not None:
            _hash(self.secondary_nid_hash, "secondary_nid_hash")
        if not 1900 <= self.birth_year <= datetime.now(UTC).year:
            raise NationalCoreWorkflowError("birth_year is outside the synthetic range")
        if not 1 <= self.birth_month <= 12 or not 1 <= self.birth_day <= 31:
            raise NationalCoreWorkflowError("birth date components are invalid")

    def facility_records(
        self, primary_gula_citizen_identifier: str
    ) -> tuple[FacilityIdentityRecord, FacilityIdentityRecord]:
        """Build protected facility records after registration creates the primary reference."""

        primary = FacilityIdentityRecord(
            facility_id=self.primary_facility_id,
            local_patient_id=self.primary_local_patient_id,
            gula_citizen_identifier=primary_gula_citizen_identifier,
            nid_hash=self.national_id_hash,
            nid_verified=self.nid_verified,
            birth_year=self.birth_year,
            birth_month=self.birth_month,
            birth_day=self.birth_day,
            phone_last10=self.phone_last10,
        )
        secondary = FacilityIdentityRecord(
            facility_id=self.secondary_facility_id,
            local_patient_id=self.secondary_local_patient_id,
            gula_citizen_identifier=self.secondary_gula_citizen_identifier,
            nid_hash=self.secondary_nid_hash or self.national_id_hash,
            nid_verified=self.nid_verified,
            birth_year=self.birth_year,
            birth_month=self.birth_month,
            birth_day=self.birth_day,
            phone_last10=self.phone_last10,
        )
        return primary, secondary


@dataclass(frozen=True, slots=True)
class NationalCoreClinicalInput:
    """Synthetic clinical/laboratory command payload."""

    encounter_reference: str
    case: SyntheticLabCase
    release_idempotency_key: str
    event_idempotency_key: str
    encounter: Any | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("encounter_reference", self.encounter_reference),
            ("release_idempotency_key", self.release_idempotency_key),
            ("event_idempotency_key", self.event_idempotency_key),
        ):
            _bounded(value, label)


@dataclass(frozen=True, slots=True)
class NationalCoreAccessInput:
    """Trusted server-side access inputs; not an HTTP-visible interface."""

    actor: AuthorizationActor
    request: AuthorizationRequest
    consent_id: str
    citizen_account_id: str

    def __post_init__(self) -> None:
        _bounded(self.consent_id, "consent_id")
        _bounded(self.citizen_account_id, "citizen_account_id")


@dataclass(frozen=True, slots=True)
class NationalCoreWorkflowCommand:
    """One synthetic vertical workflow command, bound by an idempotency key."""

    workflow_key: str
    correlation_id: str
    organization_id: str
    facility_id: str
    reviewer_name: str
    reviewer_user_id: int
    review_reason: str
    registration: NationalCoreRegistrationInput
    identity: NationalCoreIdentityInput
    clinical: NationalCoreClinicalInput
    access: NationalCoreAccessInput
    citizen_decision: AuthorizationDecision
    staff_decision: AuthorizationDecision
    now: datetime | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("workflow_key", self.workflow_key),
            ("correlation_id", self.correlation_id),
            ("organization_id", self.organization_id),
            ("facility_id", self.facility_id),
        ):
            _bounded(value, label)
        _reason(self.review_reason, "review_reason")
        try:
            require_synthetic_id(self.reviewer_name, "reviewer_name")
        except ValueError as exc:
            raise NationalCoreWorkflowError(str(exc)) from exc
        if self.reviewer_user_id <= 0:
            raise NationalCoreWorkflowError("reviewer_user_id must be positive")
        _assert_decision("citizen_decision", self.citizen_decision)
        _assert_decision("staff_decision", self.staff_decision)


# -- Result and persistence adapter -----------------------------------------


@dataclass(frozen=True, slots=True)
class NationalCoreWorkflowResult:
    """Bounded synthetic evidence; never carries a FHIR body or raw identity."""

    schema_version: str
    workflow_key: str
    correlation_id: str
    replayed: bool
    layers: tuple[str, ...]
    registration_status: dict[str, Any]
    registration_transitions: int
    linkage: IdentityLinkageOutcome
    binding: ChainBinding
    release_status: str
    bundle_reference: str | None
    event_summary: PipelineSummary | None
    citizen_view: dict[str, Any]
    offline_summary: dict[str, Any]
    audit_verification: dict[str, Any]
    decision_summary: dict[str, Any]
    stages: tuple[str, ...]

    def to_public_dict(self) -> dict[str, Any]:
        """Return a compact projection for test evidence.

        ``registration_status`` intentionally includes the synthetic 12-digit
        case reference produced by Phase 1. It is not a national identifier and
        is included only as bounded synthetic evidence; no raw NID, name,
        contact code, clinical value, actor, or FHIR body is projected.
        """

        return {
            "schema_version": self.schema_version,
            "workflow_key": self.workflow_key,
            "correlation_id": self.correlation_id,
            "replayed": self.replayed,
            "layers": list(self.layers),
            "registration_status": dict(self.registration_status),
            "registration_transitions": self.registration_transitions,
            "linkage_action": self.linkage.action,
            "patient_reference": self.binding.patient_reference,
            "result_id": self.binding.result_id,
            "release_status": self.release_status,
            "bundle_reference": self.bundle_reference,
            "event_summary": {
                "delivered": list(self.event_summary.delivered) if self.event_summary else [],
                "duplicates": list(self.event_summary.duplicates) if self.event_summary else [],
                "conflicts": list(self.event_summary.conflicts) if self.event_summary else [],
                "queue_status": dict(self.event_summary.queue_status) if self.event_summary else {},
            },
            "citizen_view": dict(self.citizen_view),
            "offline_summary": dict(self.offline_summary),
            "audit_verification": dict(self.audit_verification),
            "decision_summary": dict(self.decision_summary),
            "stages": list(self.stages),
        }


class InMemoryNationalCorePersistenceAdapter:
    """Process-local adapter over existing synthetic stores and event primitives.

    This is not a database and not an audit authority. It only owns references
    to stores already defined by canonical synthetic modules, plus workflow
    receipts needed to make a repeated synthetic command idempotent.
    """

    def __init__(
        self,
        *,
        event_pipeline: SyntheticLabEventPipeline | None = None,
        store_forward: StoreForwardEngine | None = None,
        sync_service: SyncService | None = None,
        catalog: NationalLaboratoryCatalog | None = None,
        delta_engine: DeltaCheckEngine | None = None,
        precompleted_registrations: Mapping[str, str] | None = None,
    ) -> None:
        self.idempotency_store = InMemoryIdempotencyStore()
        self.account_store = InMemoryRegistrationAccountStore()
        self.transition_store = InMemoryRegistrationTransitionStore()
        self.event_pipeline = event_pipeline or SyntheticLabEventPipeline()
        self.store_forward = store_forward or StoreForwardEngine()
        self.catalog = catalog or NationalLaboratoryCatalog()
        self.delta_engine = delta_engine or DeltaCheckEngine()
        for key, identifier in (precompleted_registrations or {}).items():
            _bounded(key, "precompleted registration key")
            if re.fullmatch(r"\d{12}", identifier) is None:
                raise NationalCoreWorkflowError(
                    "precompleted registration identifier must be a 12-digit synthetic reference"
                )
            at = datetime.now(UTC)
            seeded_request = RegistrationRequest(
                idempotency_key=key,
                subject_reference="PREESEEDED-SYNTHETIC",
                birth_year=1990,
                requested_at=at,
            )
            self.idempotency_store.reserve(seeded_request, at=at)
            self.idempotency_store.reserve_identifier(identifier)
            self.idempotency_store.complete(key, identifier, at=at)
        self.sync_service = sync_service or SyncService()
        self.offline_sync = OfflineSyncEngine(
            sync_service=self.sync_service,
            store_forward=self.store_forward,
        )
        self._runs: dict[str, tuple[str, NationalCoreWorkflowResult]] = {}

    def registration_service(self) -> RegistrationLifecycleService:
        return RegistrationLifecycleService(
            idempotency_store=self.idempotency_store,
            account_store=self.account_store,
            transition_store=self.transition_store,
        )

    def check_run(self, key: str, fingerprint: str) -> NationalCoreWorkflowResult | None:
        existing = self._runs.get(key)
        if existing is None:
            return None
        stored_fingerprint, result = existing
        if stored_fingerprint != fingerprint:
            raise NationalCoreWorkflowReplayError("workflow key was reused with different inputs")
        return result

    def remember_run(self, key: str, fingerprint: str, result: NationalCoreWorkflowResult) -> None:
        self._runs[key] = (fingerprint, result)


# -- Orchestration ----------------------------------------------------------


class NationalCoreWorkflow:
    """Compose Phase 1 registration with the synthetic national clinical chain."""

    def __init__(self, adapter: InMemoryNationalCorePersistenceAdapter | None = None) -> None:
        self.adapter = adapter or InMemoryNationalCorePersistenceAdapter()
        self._run_locks: dict[tuple[str, int], asyncio.Lock] = {}

    def _run_lock(self, workflow_key: str) -> asyncio.Lock:
        """Give each workflow key and event loop an async check/execute/remember lock."""

        key = (workflow_key, id(asyncio.get_running_loop()))
        lock = self._run_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._run_locks[key] = lock
        return lock

    async def run(self, session: Any, command: NationalCoreWorkflowCommand) -> NationalCoreWorkflowResult:
        """Execute one bounded synthetic workflow and return non-sensitive evidence."""

        async with self._run_lock(command.workflow_key):
            fingerprint = self._fingerprint(command)
            try:
                existing = self.adapter.check_run(command.workflow_key, fingerprint)
            except NationalCoreWorkflowReplayError:
                clinical_safety_metrics.record_command(
                    operation=_METRIC_OPERATION,
                    resource_type="national_core_workflow",
                    outcome="rejected",
                    reason="duplicate_command",
                )
                raise
            if existing is not None:
                clinical_safety_metrics.record_command(
                    operation=_METRIC_OPERATION,
                    resource_type="national_core_workflow",
                    outcome="completed",
                )
                return replace(existing, replayed=True)

            try:
                result = await self._execute(session, command)
            except Exception as exc:
                if "audit" in str(exc).casefold():
                    clinical_safety_metrics.record_audit_failure(
                        operation=_METRIC_OPERATION,
                        resource_type="national_core_workflow",
                    )
                clinical_safety_metrics.record_command(
                    operation=_METRIC_OPERATION,
                    resource_type="national_core_workflow",
                    outcome="rejected",
                    reason=reason_code(str(exc)),
                )
                raise
            self.adapter.remember_run(command.workflow_key, fingerprint, result)
            clinical_safety_metrics.record_command(
                operation=_METRIC_OPERATION,
                resource_type="national_core_workflow",
                outcome="completed",
            )
            return result

    async def _execute(
        self, session: Any, command: NationalCoreWorkflowCommand
    ) -> NationalCoreWorkflowResult:
        registration = command.registration
        identity = command.identity
        clinical = command.clinical
        access = command.access
        now = command.now or datetime.now(UTC)

        request = RegistrationRequest(
            idempotency_key=registration.idempotency_key,
            subject_reference=registration.subject_reference,
            birth_year=identity.birth_year,
            requested_at=now,
        )
        create_context = self._context(
            command,
            correlation_id=f"{command.correlation_id}-CREATE",
            decision=command.citizen_decision,
            actor_id=registration.subject_reference,
            actor_type=ActorType.CITIZEN,
            purpose="citizen_workspace",
            role=None,
            now=now,
        )
        contact_context = self._context(
            command,
            correlation_id=f"{command.correlation_id}-CONTACT",
            decision=command.citizen_decision,
            actor_id=registration.subject_reference,
            actor_type=ActorType.CITIZEN,
            purpose="citizen_workspace",
            role=None,
            now=now,
        )
        submit_context = self._context(
            command,
            correlation_id=f"{command.correlation_id}-SUBMIT",
            decision=command.citizen_decision,
            actor_id=registration.subject_reference,
            actor_type=ActorType.CITIZEN,
            purpose="citizen_workspace",
            role=None,
            national_id_hash=identity.national_id_hash,
            now=now,
        )
        staff_context = self._context(
            command,
            correlation_id=f"{command.correlation_id}-APPROVE",
            decision=command.staff_decision,
            actor_id=access.request.subject_account_id,
            actor_type=ActorType.STAFF,
            purpose="ADMINISTRATION",
            role=IdentityRole.IDENTITY_REVIEWER,
            national_id_hash=identity.national_id_hash,
            now=now,
        )

        service = self.adapter.registration_service()
        created = service.create(
            request=request,
            context=create_context,
            contact_reference=registration.contact_reference,
        )
        service.verify_contact(
            gula_citizen_identifier=created.account.gula_citizen_identifier,
            contact_code=registration.contact_code,
            context=contact_context,
        )
        service.submit_identity(
            gula_citizen_identifier=created.account.gula_citizen_identifier,
            evidence=registration.evidence,
            context=submit_context,
        )

        primary, secondary = identity.facility_records(created.account.gula_citizen_identifier)
        reviewer = LinkageReviewer(name=command.reviewer_name, user_id=command.reviewer_user_id)
        primary_candidate = LinkageCandidate(
            id=primary.gula_citizen_identifier,
            status=primary.status,
            birth_year=primary.birth_year,
            birth_month=primary.birth_month,
            birth_day=primary.birth_day,
            phone_last10=primary.phone_last10,
        )
        secondary_candidate = LinkageCandidate(
            id=secondary.gula_citizen_identifier,
            status=secondary.status,
            birth_year=secondary.birth_year,
            birth_month=secondary.birth_month,
            birth_day=secondary.birth_day,
            phone_last10=secondary.phone_last10,
        )
        approved = service.approve_health_identity(
            gula_citizen_identifier=created.account.gula_citizen_identifier,
            primary=primary_candidate,
            secondary=secondary_candidate,
            reviewer=reviewer,
            reason=command.review_reason,
            evidence_reference=identity.linkage_evidence_reference,
            context=staff_context,
        )
        account = approved.account

        integration = NationalClinicalIntegration(
            correlation_id=command.correlation_id,
            organization_id=command.organization_id,
            facility_id=command.facility_id,
            reviewer=command.reviewer_name,
            review_reason=command.review_reason,
            release_idempotency_key=clinical.release_idempotency_key,
            event_idempotency_key=clinical.event_idempotency_key,
            catalog=self.adapter.catalog,
            delta_engine=self.adapter.delta_engine,
            event_pipeline=self.adapter.event_pipeline,
        )
        linkage = integration.link_health_identity(
            primary,
            secondary,
            reviewer=reviewer,
            reason=command.review_reason,
            evidence_reference=identity.linkage_evidence_reference,
            decided_at=now,
        )
        binding = integration.bind_chain(
            clinical.case,
            patient_reference=clinical.case.patient.patient_id,
            encounter_reference=clinical.encounter_reference,
            gula_citizen_identifier=account.gula_citizen_identifier,
            encounter=clinical.encounter,
            national_id_hash=identity.national_id_hash,
            linkage=linkage,
            profile_hash=identity.national_id_hash,
            candidate_hash=identity.national_id_hash,
            candidate_verified=identity.nid_verified,
            corroborated=True,
        )
        await integration.record_linkage_audit(session, linkage, binding)

        decision = integration.validate_and_release(clinical.case)
        bundle: dict[str, Any] | None = None
        event_summary: PipelineSummary | None = None
        access_outcome = None
        if decision.status == RELEASE_RELEASED:
            bundle = integration.project_clinical_record(clinical.case, decision)
            event_summary = integration.publish_result_event(clinical.case, decision)
            access_outcome = await integration.authorize_citizen_access(
                session,
                actor=access.actor,
                request=access.request,
                consent_id=access.consent_id,
                citizen_account_id=access.citizen_account_id,
                expected_gula_identifier=account.gula_citizen_identifier,
                national_id_hash=identity.national_id_hash,
                binding=binding,
                now=now,
            )
        elif decision.status != RELEASE_QUARANTINED:
            raise NationalCoreWorkflowError(f"unexpected release status: {decision.status}")

        citizen_view = await self._citizen_view(session, account, command, bundle is not None, now)
        offline_summary = await self._queue_offline_receipt(
            command,
            entity_id=(bundle or {}).get("id") or binding.result_id,
            decision_id=decision.decision_id,
            released=bundle is not None,
        )
        audit_verification = await CanonicalAuditService(session).verify(
            organization_id=command.organization_id,
        )
        if audit_verification.get("status") != "VALID":
            raise NationalCoreWorkflowError("canonical audit chain verification failed")
        record: IntegratedClinicalRecord = integration.build_record(
            linkage=linkage,
            binding=binding,
            decision=decision,
            bundle=bundle,
            event_summary=event_summary,
            access=access_outcome,
        )
        decision_summary: dict[str, Any] = {
            "citizen": command.citizen_decision.public(),
            "staff": command.staff_decision.public(),
            "clinical_access": access_outcome.decision.public() if access_outcome else None,
        }
        return NationalCoreWorkflowResult(
            schema_version=WORKFLOW_SCHEMA,
            workflow_key=command.workflow_key,
            correlation_id=command.correlation_id,
            replayed=False,
            layers=WORKFLOW_LAYERS,
            registration_status=service.status(account.gula_citizen_identifier),
            registration_transitions=len(service.history(account.gula_citizen_identifier)),
            linkage=linkage,
            binding=binding,
            release_status=decision.status,
            bundle_reference=(bundle or {}).get("id") if bundle else None,
            event_summary=event_summary,
            citizen_view=citizen_view,
            offline_summary=offline_summary,
            audit_verification=audit_verification,
            decision_summary=decision_summary,
            stages=tuple(stage.name for stage in record.stages),
        )

    @staticmethod
    def _context(
        command: NationalCoreWorkflowCommand,
        *,
        correlation_id: str | None,
        decision: AuthorizationDecision,
        actor_id: str,
        actor_type: ActorType,
        purpose: str,
        role: IdentityRole | None,
        now: datetime,
        national_id_hash: str | None = None,
    ) -> RegistrationContext:
        return RegistrationContext(
            decision=decision,
            actor_id=actor_id,
            actor_type=actor_type,
            organization_id=command.organization_id,
            facility_id=command.facility_id,
            purpose=purpose,
            now=now,
            role=role,
            correlation_id=correlation_id or command.correlation_id,
            national_id_hash=national_id_hash or "0" * 64,
        )

    async def _citizen_view(
        self,
        session: Any,
        account: CitizenRegistrationAccount,
        command: NationalCoreWorkflowCommand,
        result_available: bool,
        now: datetime,
    ) -> dict[str, Any]:
        """Return only a synthetic status; withhold medical results until activation."""

        context = self._context(
            command,
            correlation_id=f"{command.correlation_id}-CITIZEN_VIEW",
            decision=command.staff_decision,
            actor_id=command.access.request.subject_account_id,
            actor_type=ActorType.STAFF,
            purpose="ADMINISTRATION",
            role=IdentityRole.HEALTHCARE_PROVIDER,
            now=now,
            national_id_hash=command.identity.national_id_hash,
        )
        try:
            assert_medical_data_access_allowed(account=account, context=context)
        except MedicalDataAccessDeniedError as exc:
            await self._record_withheld_audit(session, account, command, str(exc))
            clinical_safety_metrics.record_command(
                operation=_CITIZEN_METRIC_OPERATION,
                resource_type="patient_record",
                outcome="rejected",
                reason="activation owner gate",
            )
            return {
                "lifecycle_state": account.lifecycle_state.value,
                "verification_state": account.verification_state,
                "can_access_medical_data": False,
                "next_step": "await_owner_activation_decision",
                "medical_result_withheld": True,
                "withheld_reason_code": "ACTIVATION_OWNER_GATE",
                "result_generated_in_synthetic_chain": result_available,
                "official_verification": False,
                "synthetic": True,
            }
        raise NationalCoreWorkflowError("unexpected activation: citizen result projection is blocked")

    @staticmethod
    async def _record_withheld_audit(
        session: Any,
        account: CitizenRegistrationAccount,
        command: NationalCoreWorkflowCommand,
        message: str,
    ) -> None:
        event = AuditEventInput(
            event_type="NATIONAL_CORE_CITIZEN_RESULT_WITHHELD",
            category="ACCESS_CONTROL",
            action="patient_record.read",
            actor_id=account.gula_citizen_identifier,
            organization_id=command.organization_id,
            facility_id=command.facility_id,
            target_type="citizen_clinical_view",
            target_id=account.gula_citizen_identifier,
            decision="DENY",
            reason_code="ACTIVATION_OWNER_GATE",
            request_id=command.correlation_id,
            correlation_id=command.correlation_id,
            source=WORKFLOW_SOURCE,
            data_classification="SENSITIVE",
            metadata={"reason": message[:200], "synthetic": True},
        )
        try:
            await CanonicalAuditService(session).record(event)
        except Exception as exc:
            raise NationalCoreWorkflowError(
                f"canonical audit failure while withholding result: {type(exc).__name__}"
            ) from exc

    async def _queue_offline_receipt(
        self,
        command: NationalCoreWorkflowCommand,
        *,
        entity_id: str,
        decision_id: str,
        released: bool,
    ) -> dict[str, Any]:
        receipt_fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "workflow_key": command.workflow_key,
                    "correlation_id": command.correlation_id,
                    "entity_id": entity_id,
                    "decision_id": decision_id,
                    "released": released,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:16]
        entry = OfflineQueueEntry(
            id=f"{command.workflow_key}:clinical-record:{receipt_fingerprint}",
            entity_type="clinical_record_projection",
            entity_id=entity_id,
            action="sync" if released else "quarantine_sync",
            payload={
                "version": 1,
                "correlation_id": command.correlation_id,
                "result_id": entity_id,
                "decision_id": decision_id,
                "synthetic": True,
            },
            timestamp=time.time(),
        )
        enqueued = self.adapter.store_forward.enqueue(entry)
        summary = await self.adapter.offline_sync.sync_all()
        return {
            "enqueued": enqueued,
            **{key: value for key, value in summary.items() if key != "results"},
            "queue_status": self.adapter.store_forward.queue_size(),
        }

    @staticmethod
    def _fingerprint(command: NationalCoreWorkflowCommand) -> str:
        """Bind the receipt to every field consumed by execution and authorization."""

        payload = {
            "schema_version": WORKFLOW_SCHEMA,
            "command": NationalCoreWorkflow._jsonable(command),
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @classmethod
    def _jsonable(cls, value: Any) -> Any:
        """Deterministically serialize dataclasses, enums, mappings, and fixtures."""

        if is_dataclass(value) and not isinstance(value, type):
            return {
                item.name: cls._jsonable(getattr(value, item.name))
                for item in fields(value)
            }
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, SimpleNamespace):
            return {
                key: cls._jsonable(item)
                for key, item in sorted(vars(value).items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, Mapping):
            return {
                str(key): cls._jsonable(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, (set, frozenset)):
            return sorted((cls._jsonable(item) for item in value), key=repr)
        if isinstance(value, (list, tuple)):
            return [cls._jsonable(item) for item in value]
        return value


def _assert_decision(name: str, decision: AuthorizationDecision) -> None:
    """Require a decision object with canonical engine issuance references.

    Decision objects remain trusted server-side inputs because this additive
    facade cannot cryptographically prove engine provenance. Allow decisions
    must at least carry a policy id, policy version, and audit reference; an
    unattested hand-built allow is rejected before any domain mutation.
    """

    if not isinstance(decision, AuthorizationDecision):
        raise NationalCoreWorkflowError(f"{name} must be a canonical AuthorizationDecision")
    if decision.allowed and not all(
        isinstance(item, str) and item.strip()
        for item in (decision.policy_id, decision.policy_version, decision.audit_reference)
    ):
        raise NationalCoreWorkflowError(
            f"{name} allow decision requires policy, version, and audit references"
        )


def _bounded(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise NationalCoreWorkflowError(f"{name} must be a bounded non-empty string")
    if _OPAQUE.fullmatch(value) is None:
        raise NationalCoreWorkflowError(f"{name} must be an opaque synthetic reference")
    if _RAW_NID_RUN.search(value):
        raise NationalCoreWorkflowError(f"{name} must not contain a national identifier")
    return value


def _reason(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise NationalCoreWorkflowError(f"{name} must be a bounded non-empty reason")
    if _RAW_NID_RUN.search(value):
        raise NationalCoreWorkflowError(f"{name} must not contain a national identifier")
    return value


def _hash(value: str, name: str) -> str:
    if not isinstance(value, str) or _HEX_HASH.fullmatch(value) is None:
        raise NationalCoreWorkflowError(f"{name} must be a 64-character lowercase hash")
    return value


__all__ = [
    "WORKFLOW_LAYERS",
    "WORKFLOW_SCHEMA",
    "InMemoryNationalCorePersistenceAdapter",
    "NationalCoreAccessInput",
    "NationalCoreClinicalInput",
    "NationalCoreIdentityInput",
    "NationalCoreRegistrationInput",
    "NationalCoreWorkflow",
    "NationalCoreWorkflowCommand",
    "NationalCoreWorkflowError",
    "NationalCoreWorkflowReplayError",
    "NationalCoreWorkflowResult",
]
