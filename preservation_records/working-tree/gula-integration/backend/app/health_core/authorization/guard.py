"""Authorizing facade that wraps the real synthetic clinical and lab services.

Nothing in this module is wired into a route or ``factory.py``. Callers that want
Health Core behaviour must use :class:`AuthorizedHealthCore`: every method first
evaluates (principal, action, resource) through the policy engine and raises
before the wrapped service is touched on a denial. The wrapped clinical and lab
services are private: no caller can reach an unwrapped mutator through the
facade. Resource scope attributes for reads come from an internal index populated
only by guarded writes, so a caller cannot inject a falsified tenant, patient,
organization or facility scope.
"""

from __future__ import annotations

from datetime import datetime

from app.health_core.authorization.engine import AuthorizationEngine
from app.health_core.authorization.errors import AuthorizationDenied
from app.health_core.authorization.models import (
    Action,
    AuthorizationDecision,
    Principal,
    ResourceContext,
)
from app.health_core.clinical import (
    ClinicalContext,
    ClinicalNote,
    Diagnosis,
    Encounter,
    EncounterStatus,
    Facility,
    MedicalRecordView,
    Observation,
    Organization,
    Practitioner,
    PractitionerRole,
    RecordScope,
    Severity,
)
from app.health_core.contracts.catalogue import ContractOperation
from app.health_core.identity import PatientIdentityPort
from app.health_core.lab import (
    LabOrder,
    LabResult,
    LabWorkflowService,
    Priority,
    Specimen,
    SpecimenStatus,
    Verification,
    VerificationDecision,
)

__all__ = ["AuthorizedHealthCore", "ResourceAttributeIndex", "build_authorized_context"]


class ResourceAttributeIndex:
    """Authoritative map of resource id to its guarded scope attributes."""

    def __init__(self) -> None:
        self._by_id: dict[str, ResourceContext] = {}

    def put(self, context: ResourceContext) -> None:
        """Store a resource's attributes, refusing tenant re-assignment."""
        existing = self._by_id.get(context.resource_id)
        if existing is not None and existing.tenant_id != context.tenant_id:
            raise ValueError("a resource id cannot be re-assigned to another tenant")
        self._by_id[context.resource_id] = context

    def get(self, resource_id: str) -> ResourceContext | None:
        """Return the stored attributes or ``None`` (never fabricate any)."""
        return self._by_id.get(resource_id)

    def snapshot(self) -> dict[str, ResourceContext]:
        """Return a defensive copy for inspection and tests."""
        return dict(self._by_id)


class AuthorizedHealthCore:
    """An authorization gate in front of the unwrapped synthetic services."""

    def __init__(
        self,
        *,
        clinical: ClinicalContext,
        lab: LabWorkflowService,
        engine: AuthorizationEngine,
    ) -> None:
        self._clinical = clinical
        self._lab = lab
        self.engine = engine
        self._attributes = ResourceAttributeIndex()

    @property
    def attributes(self) -> ResourceAttributeIndex:
        """The authoritative resource attribute index."""
        return self._attributes

    # ------------------------------------------------------------------ helpers

    def _authorize(
        self,
        principal: Principal,
        *,
        action: Action,
        tenant_id: str,
        resource_id: str,
        use_index: bool = False,
        patient_ref: str | None = None,
        facility_id: str | None = None,
        organization_id: str | None = None,
    ) -> AuthorizationDecision:
        """Evaluate one operation and raise before delegation on any DENY.

        For indexed reads the stored resource context is authoritative for every
        scope attribute, including tenant: a caller cannot pass its own tenant to
        make a resource stored under another tenant look local. With no stored
        entry, the caller-supplied tenant is the only one available and is used
        unchanged (an unknown id is then denied by the normal policy path).
        """
        if use_index:
            stored = self._attributes.get(resource_id)
            context = ResourceContext(
                tenant_id=stored.tenant_id if stored is not None else tenant_id,
                resource_id=resource_id,
                action=action,
                organization_id=stored.organization_id if stored is not None else None,
                facility_id=stored.facility_id if stored is not None else None,
                patient_ref=stored.patient_ref if stored is not None else None,
            )
        else:
            context = ResourceContext(
                tenant_id=tenant_id,
                resource_id=resource_id,
                action=action,
                organization_id=organization_id,
                facility_id=facility_id,
                patient_ref=patient_ref,
            )
        decision = self.engine.evaluate(principal, context)
        if not decision.allowed:
            raise AuthorizationDenied(decision)
        return decision

    def _index_entity(
        self,
        entity: object,
        *,
        resource_id: str,
        action: Action,
        tenant_id: str,
        patient_ref: str | None = None,
        facility_id: str | None = None,
        organization_id: str | None = None,
    ) -> None:
        """Record the authoritative attributes returned by a wrapped service."""
        raw_tenant = getattr(entity, "tenant_id", None)
        resolved_tenant = raw_tenant if isinstance(raw_tenant, str) else tenant_id

        raw_patient = getattr(entity, "patient_ref", None)
        if not isinstance(raw_patient, str):
            patient = getattr(entity, "patient", None)
            raw_patient = getattr(patient, "ref", None) if patient is not None else None
        resolved_patient = raw_patient if isinstance(raw_patient, str) else patient_ref

        raw_facility = getattr(entity, "facility_id", None)
        resolved_facility = raw_facility if isinstance(raw_facility, str) else facility_id

        raw_organization = getattr(entity, "organization_id", None)
        resolved_organization = raw_organization if isinstance(raw_organization, str) else organization_id

        self._attributes.put(
            ResourceContext(
                tenant_id=resolved_tenant,
                resource_id=resource_id,
                action=action,
                organization_id=resolved_organization,
                facility_id=resolved_facility,
                patient_ref=resolved_patient,
            )
        )

    def _indexed_patient(self, resource_id: str) -> str | None:
        """Return the indexed patient scope for a resource, if it has one."""
        stored = self._attributes.get(resource_id)
        return None if stored is None else stored.patient_ref

    # --------------------------------------------------------------- practitioner

    def register_practitioner(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        role: PractitionerRole | str,
        qualification: str,
        active: bool = True,
    ) -> Practitioner:
        """Guard practitioner registration."""
        action = ContractOperation.PRACTITIONER_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
        )
        entity = self._clinical.practitioners.register(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            role=role,
            qualification=qualification,
            active=active,
        )
        self._index_entity(
            entity,
            resource_id=entity.practitioner_id,
            action=action,
            tenant_id=tenant_id,
        )
        return entity

    def get_practitioner(
        self, principal: Principal, *, tenant_id: str, practitioner_id: str
    ) -> Practitioner:
        """Guard practitioner reads with tenant and policy enforcement."""
        self._authorize(
            principal,
            action=ContractOperation.PRACTITIONER_READ,
            tenant_id=tenant_id,
            resource_id=practitioner_id,
            use_index=True,
        )
        return self._clinical.practitioners.get(
            tenant_id=tenant_id, practitioner_id=practitioner_id
        )

    # -------------------------------------------------------------- organization

    def register_organization(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        label: str,
    ) -> Organization:
        """Guard organization registration with an explicit organization scope."""
        action = ContractOperation.ORGANIZATION_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            organization_id=idempotency_key,
        )
        entity = self._clinical.organizations.register_organization(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            label=label,
        )
        self._index_entity(
            entity,
            resource_id=entity.organization_id,
            action=action,
            tenant_id=tenant_id,
            organization_id=entity.organization_id,
        )
        return entity

    def get_organization(
        self, principal: Principal, *, tenant_id: str, organization_id: str
    ) -> Organization:
        """Guard organization reads; the resource is itself an org-scoped object."""
        self._authorize(
            principal,
            action=ContractOperation.ORGANIZATION_READ,
            tenant_id=tenant_id,
            resource_id=organization_id,
            use_index=True,
        )
        return self._clinical.organizations.get_organization(
            tenant_id=tenant_id, organization_id=organization_id
        )

    # ------------------------------------------------------------------- facility

    def register_facility(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        organization_id: str,
        label: str,
        facility_type: str,
    ) -> Facility:
        """Guard facility registration with organization and facility scopes."""
        action = ContractOperation.FACILITY_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            organization_id=organization_id,
            facility_id=idempotency_key,
        )
        entity = self._clinical.organizations.register_facility(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            organization_id=organization_id,
            label=label,
            facility_type=facility_type,
        )
        self._index_entity(
            entity,
            resource_id=entity.facility_id,
            action=action,
            tenant_id=tenant_id,
            organization_id=entity.organization_id,
            facility_id=entity.facility_id,
        )
        return entity

    def get_facility(
        self, principal: Principal, *, tenant_id: str, facility_id: str
    ) -> Facility:
        """Guard facility reads with both organization and facility scope checks."""
        self._authorize(
            principal,
            action=ContractOperation.FACILITY_READ,
            tenant_id=tenant_id,
            resource_id=facility_id,
            use_index=True,
        )
        return self._clinical.organizations.get_facility(
            tenant_id=tenant_id, facility_id=facility_id
        )

    # ------------------------------------------------------------------ encounter

    def create_encounter(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        patient_ref: str,
        practitioner_id: str,
        facility_id: str,
        reason: str,
    ) -> Encounter:
        """Guard encounter creation with explicit patient and facility scopes."""
        action = ContractOperation.ENCOUNTER_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=patient_ref,
            facility_id=facility_id,
        )
        entity = self._clinical.encounters.create(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            patient_ref=patient_ref,
            practitioner_id=practitioner_id,
            facility_id=facility_id,
            reason=reason,
        )
        self._index_entity(
            entity,
            resource_id=entity.encounter_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
            facility_id=facility_id,
        )
        return entity

    def get_encounter(
        self, principal: Principal, *, tenant_id: str, encounter_id: str
    ) -> Encounter:
        """Guard encounter reads using indexed patient/facility attributes."""
        self._authorize(
            principal,
            action=ContractOperation.ENCOUNTER_READ,
            tenant_id=tenant_id,
            resource_id=encounter_id,
            use_index=True,
        )
        return self._clinical.encounters.get_encounter(
            tenant_id=tenant_id, encounter_id=encounter_id
        )

    def transition_encounter(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        encounter_id: str,
        to_status: EncounterStatus | str,
        idempotency_key: str,
    ) -> Encounter:
        """Guard an encounter state change with indexed resource attributes."""
        self._authorize(
            principal,
            action=ContractOperation.ENCOUNTER_CREATE,
            tenant_id=tenant_id,
            resource_id=encounter_id,
            use_index=True,
        )
        return self._clinical.encounters.transition(
            tenant_id=tenant_id,
            encounter_id=encounter_id,
            to_status=to_status,
            idempotency_key=idempotency_key,
        )

    def add_note(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        encounter_id: str,
        idempotency_key: str,
        author_practitioner_id: str,
        text: str,
    ) -> ClinicalNote:
        """Guard clinical note creation against the encounter's patient scope."""
        self._authorize(
            principal,
            action=ContractOperation.ENCOUNTER_CREATE,
            tenant_id=tenant_id,
            resource_id=encounter_id,
            use_index=True,
        )
        entity = self._clinical.encounters.add_note(
            tenant_id=tenant_id,
            encounter_id=encounter_id,
            idempotency_key=idempotency_key,
            author_practitioner_id=author_practitioner_id,
            text=text,
        )
        self._index_entity(
            entity,
            resource_id=entity.note_id,
            action=ContractOperation.ENCOUNTER_CREATE,
            tenant_id=tenant_id,
            patient_ref=self._indexed_patient(encounter_id),
        )
        return entity

    def list_encounters_for_patient(
        self, principal: Principal, *, tenant_id: str, patient_ref: str
    ) -> tuple[Encounter, ...]:
        """Guard a patient-keyed encounter listing."""
        self._authorize(
            principal,
            action=ContractOperation.ENCOUNTER_READ,
            tenant_id=tenant_id,
            resource_id=patient_ref,
            patient_ref=patient_ref,
        )
        return self._clinical.encounters.list_for_patient(
            tenant_id=tenant_id, patient_ref=patient_ref
        )

    # ------------------------------------------------------------------ diagnosis

    def record_diagnosis(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        patient_ref: str,
        encounter_id: str,
        code: str,
        description: str,
        severity: Severity | str,
    ) -> Diagnosis:
        """Guard diagnosis assertion against an explicit patient scope."""
        action = ContractOperation.DIAGNOSIS_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=patient_ref,
        )
        entity = self._clinical.diagnoses.record(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            patient_ref=patient_ref,
            encounter_id=encounter_id,
            code=code,
            description=description,
            severity=severity,
        )
        self._index_entity(
            entity,
            resource_id=entity.diagnosis_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
        )
        return entity

    def get_diagnosis(
        self, principal: Principal, *, tenant_id: str, diagnosis_id: str
    ) -> Diagnosis:
        """Guard diagnosis reads using indexed patient attributes."""
        self._authorize(
            principal,
            action=ContractOperation.DIAGNOSIS_READ,
            tenant_id=tenant_id,
            resource_id=diagnosis_id,
            use_index=True,
        )
        return self._clinical.diagnoses.get_diagnosis(
            tenant_id=tenant_id, diagnosis_id=diagnosis_id
        )

    def list_diagnoses_for_patient(
        self, principal: Principal, *, tenant_id: str, patient_ref: str
    ) -> tuple[Diagnosis, ...]:
        """Guard a patient-keyed diagnosis listing."""
        self._authorize(
            principal,
            action=ContractOperation.DIAGNOSIS_READ,
            tenant_id=tenant_id,
            resource_id=patient_ref,
            patient_ref=patient_ref,
        )
        return self._clinical.diagnoses.list_for_patient(
            tenant_id=tenant_id, patient_ref=patient_ref
        )

    # ---------------------------------------------------------------- observation

    def record_observation(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        idempotency_key: str,
        patient_ref: str,
        encounter_id: str,
        code: str,
        display: str,
        value: float,
        unit: str,
        recorded_at: datetime,
    ) -> Observation:
        """Guard observation recording against an explicit patient scope."""
        action = ContractOperation.OBSERVATION_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=patient_ref,
        )
        entity = self._clinical.observations.record(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            patient_ref=patient_ref,
            encounter_id=encounter_id,
            code=code,
            display=display,
            value=value,
            unit=unit,
            recorded_at=recorded_at,
        )
        self._index_entity(
            entity,
            resource_id=entity.observation_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
        )
        return entity

    def query_observations(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        patient_ref: str,
        encounter_id: str | None = None,
        code: str | None = None,
    ) -> tuple[Observation, ...]:
        """Guard an observation query against an explicit patient scope."""
        self._authorize(
            principal,
            action=ContractOperation.OBSERVATION_READ,
            tenant_id=tenant_id,
            resource_id=patient_ref,
            patient_ref=patient_ref,
        )
        return self._clinical.observations.query(
            tenant_id=tenant_id,
            patient_ref=patient_ref,
            encounter_id=encounter_id,
            code=code,
        )

    # ------------------------------------------------------------- medical record

    def open_medical_record(
        self, principal: Principal, *, tenant_id: str, patient_ref: str
    ) -> MedicalRecordView:
        """Guard the single-patient medical record aggregate."""
        self._authorize(
            principal,
            action=ContractOperation.MEDICAL_RECORD_READ,
            tenant_id=tenant_id,
            resource_id=patient_ref,
            patient_ref=patient_ref,
        )
        return self._clinical.medical_records.open(
            scope=RecordScope(tenant_id=tenant_id, patient_refs=(patient_ref,))
        )

    # --------------------------------------------------------------- lab workflow

    def place_order(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        patient_ref: str,
        test_codes: tuple[str, ...],
        idempotency_key: str,
        priority: Priority = Priority.ROUTINE,
        actor_id: str,
    ) -> LabOrder:
        """Guard lab order placement against an explicit patient scope."""
        action = ContractOperation.LAB_ORDER_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=patient_ref,
        )
        entity = self._lab.place_order(
            tenant_id=tenant_id,
            patient_ref=patient_ref,
            test_codes=test_codes,
            idempotency_key=idempotency_key,
            priority=priority,
            actor_id=actor_id,
        )
        self._index_entity(
            entity,
            resource_id=entity.order_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
        )
        return entity

    def get_order(self, principal: Principal, *, tenant_id: str, order_id: str) -> LabOrder:
        """Guard lab order reads using indexed attributes."""
        self._authorize(
            principal,
            action=ContractOperation.LAB_ORDER_READ,
            tenant_id=tenant_id,
            resource_id=order_id,
            use_index=True,
        )
        return self._lab.get_order(tenant_id=tenant_id, order_id=order_id)

    def list_orders(self, principal: Principal, *, tenant_id: str) -> tuple[LabOrder, ...]:
        """Guard a tenant-level lab order listing."""
        self._authorize(
            principal,
            action=ContractOperation.LAB_ORDER_READ,
            tenant_id=tenant_id,
            resource_id=tenant_id,
        )
        return self._lab.list_orders(tenant_id=tenant_id)

    def register_specimen(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        order_id: str,
        barcode: str,
        actor_id: str,
    ) -> Specimen:
        """Guard specimen registration; patient scope is inherited from the order."""
        action = ContractOperation.SPECIMEN_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=barcode,
            patient_ref=self._indexed_patient(order_id),
        )
        entity = self._lab.register_specimen(
            tenant_id=tenant_id,
            order_id=order_id,
            barcode=barcode,
            actor_id=actor_id,
        )
        self._index_entity(
            entity,
            resource_id=entity.specimen_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=self._indexed_patient(order_id),
        )
        return entity

    def get_specimen(
        self, principal: Principal, *, tenant_id: str, specimen_id: str
    ) -> Specimen:
        """Guard specimen reads using indexed attributes."""
        self._authorize(
            principal,
            action=ContractOperation.SPECIMEN_READ,
            tenant_id=tenant_id,
            resource_id=specimen_id,
            use_index=True,
        )
        return self._lab.get_specimen(tenant_id=tenant_id, specimen_id=specimen_id)

    def transition_specimen(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        specimen_id: str,
        to_status: SpecimenStatus | str,
        actor_id: str,
        reason: str | None = None,
    ) -> Specimen:
        """Guard specimen state changes with indexed resource attributes."""
        self._authorize(
            principal,
            action=ContractOperation.SPECIMEN_CREATE,
            tenant_id=tenant_id,
            resource_id=specimen_id,
            use_index=True,
        )
        return self._lab.transition_specimen(
            tenant_id=tenant_id,
            specimen_id=specimen_id,
            to_status=to_status,
            actor_id=actor_id,
            reason=reason,
        )

    def record_result(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        order_id: str,
        specimen_id: str,
        patient_ref: str,
        test_code: str,
        value: float,
        unit: str,
        idempotency_key: str,
        actor_id: str,
    ) -> LabResult:
        """Guard result recording against an explicit patient scope."""
        action = ContractOperation.LAB_RESULT_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=patient_ref,
        )
        entity = self._lab.record_result(
            tenant_id=tenant_id,
            order_id=order_id,
            specimen_id=specimen_id,
            patient_ref=patient_ref,
            test_code=test_code,
            value=value,
            unit=unit,
            idempotency_key=idempotency_key,
            actor_id=actor_id,
        )
        self._index_entity(
            entity,
            resource_id=entity.result_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=patient_ref,
        )
        return entity

    def get_result(self, principal: Principal, *, tenant_id: str, result_id: str) -> LabResult:
        """Guard result reads using indexed attributes."""
        self._authorize(
            principal,
            action=ContractOperation.LAB_RESULT_READ,
            tenant_id=tenant_id,
            resource_id=result_id,
            use_index=True,
        )
        return self._lab.get_result(tenant_id=tenant_id, result_id=result_id)

    def verify_result(
        self,
        principal: Principal,
        *,
        tenant_id: str,
        result_id: str,
        reviewer_id: str,
        decision: VerificationDecision | str,
        idempotency_key: str,
        reason: str | None = None,
    ) -> Verification:
        """Guard result verification; patient scope is inherited from the result."""
        action = ContractOperation.RESULT_VERIFICATION_CREATE
        self._authorize(
            principal,
            action=action,
            tenant_id=tenant_id,
            resource_id=idempotency_key,
            patient_ref=self._indexed_patient(result_id),
        )
        entity = self._lab.verify_result(
            tenant_id=tenant_id,
            result_id=result_id,
            reviewer_id=reviewer_id,
            decision=decision,
            idempotency_key=idempotency_key,
            reason=reason,
        )
        self._index_entity(
            entity,
            resource_id=entity.verification_id,
            action=action,
            tenant_id=tenant_id,
            patient_ref=self._indexed_patient(result_id),
        )
        return entity

    def get_verification(
        self, principal: Principal, *, tenant_id: str, verification_id: str
    ) -> Verification:
        """Guard verification reads using indexed attributes."""
        self._authorize(
            principal,
            action=ContractOperation.RESULT_VERIFICATION_READ,
            tenant_id=tenant_id,
            resource_id=verification_id,
            use_index=True,
        )
        return self._lab.get_verification(
            tenant_id=tenant_id, verification_id=verification_id
        )


def build_authorized_context(identity: PatientIdentityPort) -> AuthorizedHealthCore:
    """Wire the real synthetic clinical + lab services behind the authorization gate."""
    return AuthorizedHealthCore(
        clinical=ClinicalContext(identity=identity),
        lab=LabWorkflowService(identity=identity),
        engine=AuthorizationEngine(),
    )
