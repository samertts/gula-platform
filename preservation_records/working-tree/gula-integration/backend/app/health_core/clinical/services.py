"""Services implementing the six synthetic clinical domains.

All services depend on an identity port, in-memory repositories and an event
sink. They never create canonical identity records, never link patients and
never touch a database. Duplicate operations are idempotent: replay returns the
original entity, while a conflicting reuse of a synthetic key fails closed.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from app.health_core.clinical.entities import (
    ClinicalNote,
    Diagnosis,
    DiagnosisStatus,
    Encounter,
    EncounterStatus,
    Facility,
    FacilityType,
    MedicalRecordView,
    Observation,
    Organization,
    Practitioner,
    PractitionerRole,
    RecordScope,
    Severity,
)
from app.health_core.clinical.errors import ClinicalValidationError, UnknownClinicalEntityError
from app.health_core.clinical.ports import ClinicalRepository, EventSink, T
from app.health_core.clinical.repositories import InMemoryRepository
from app.health_core.clinical.validation import (
    require_finite_number,
    require_icd_code,
    require_label,
    require_loinc_code,
    require_synthetic_ref,
    require_unit,
    require_utc_timestamp,
    utc_now_iso,
)
from app.health_core.common import (
    AggregateType,
    DomainEvent,
    DuplicateEntityError,
    EventType,
    ForbiddenSyntheticOperationError,
    InvalidStateTransitionError,
    TenantMismatchError,
    new_event,
)
from app.health_core.contracts.events import validate_domain_event
from app.health_core.identity import PatientIdentityPort, PatientRef

__all__ = [
    "TRANSITION_EVENTS",
    "DiagnosisService",
    "EncounterService",
    "MedicalRecordService",
    "ObservationService",
    "OrganizationRegistry",
    "PractitionerRegistry",
]

KEY_PREFIXES = {
    "practitioner": "SYN-PRC-",
    "organization": "SYN-ORG-",
    "facility": "SYN-FAC-",
    "encounter": "SYN-ENC-",
    "note": "SYN-NOT-",
    "diagnosis": "SYN-DIA-",
    "observation": "SYN-OBS-",
    "transition": "SYN-TRN-",
}

# Event schema 1.1.0 added the explicit ``encounter.started`` value, so the
# planned -> in_progress transition no longer reuses ENCOUNTER_CREATED. The
# legacy ``transition``/``from_status``/``to_status``/``version`` payload keys
# are kept unchanged for backward compatibility (additive semantics only).
TRANSITION_EVENTS: dict[EncounterStatus, EventType] = {
    EncounterStatus.IN_PROGRESS: EventType.ENCOUNTER_STARTED,
    EncounterStatus.ADMITTED: EventType.ENCOUNTER_ADMITTED,
    EncounterStatus.TRANSFERRED: EventType.ENCOUNTER_TRANSFERRED,
    EncounterStatus.DISCHARGED: EventType.ENCOUNTER_DISCHARGED,
    EncounterStatus.CANCELLED: EventType.ENCOUNTER_CANCELLED,
}


def _fingerprint(**values: object) -> str:
    """Build a stable fingerprint for an operation's normalised arguments."""
    return json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)


def _require_entity(entity: T | None, *, kind: str, key: str) -> T:
    """Return an entity or raise a structured not-found error."""
    if entity is None:
        raise UnknownClinicalEntityError(
            f"synthetic {kind} not found",
            details={"kind": kind, "key": key},
        )
    return entity


def _check_tenant(actual: str, *, expected: str, kind: str, key: str) -> None:
    """Refuse to address an entity belonging to a different synthetic tenant."""
    if actual != expected:
        raise TenantMismatchError(
            f"synthetic {kind} belongs to a different tenant",
            details={"kind": kind, "key": key, "tenant_id": expected},
        )


def _as_enum(enumeration: type[T], value: T | str, *, field: str) -> T:
    """Convert a string to an enum member with a domain-level validation error."""
    try:
        return enumeration(value)  # type: ignore[call-arg]
    except ValueError as exc:
        raise ClinicalValidationError(
            f"{field} is not a supported value",
            details={"field": field, "value": str(value)},
        ) from exc


class _ClinicalService:
    """Shared idempotency and event-emission behaviour."""

    def __init__(self, events: EventSink) -> None:
        self._events = events

    def _emit(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        tenant_id: str,
        payload: dict[str, object] | None = None,
    ) -> DomainEvent:
        """Build, catalogue-validate and only then append one domain event.

        The contract catalogue is enforced at the producer boundary: an event
        that does not satisfy its declared payload keys is rejected before it
        reaches the sink, so no invalid event can be observed downstream.
        """
        event = new_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            payload=payload,
        )
        validate_domain_event(event)
        self._events.append(event)
        return event

    def _create_once(
        self,
        repo: ClinicalRepository[T],
        *,
        key: str,
        entity: T,
        fingerprint: str,
    ) -> tuple[T, bool]:
        stored, created = repo.add_if_absent(key, entity, fingerprint)
        if not created and repo.fingerprint_of(key) != fingerprint:
            raise DuplicateEntityError(
                "synthetic idempotency key was used for a different operation",
                details={"key": key},
            )
        return stored, created

    def _change_once(
        self,
        repo: ClinicalRepository[T],
        *,
        key: str,
        fingerprint: str,
        apply: Callable[[], T],
    ) -> tuple[T, bool]:
        stored = repo.get(key)
        if stored is not None:
            if repo.fingerprint_of(key) != fingerprint:
                raise DuplicateEntityError(
                    "synthetic idempotency key was used for a different transition",
                    details={"key": key},
                )
            return stored, False
        updated = apply()
        repo.add_if_absent(key, updated, fingerprint)
        return updated, True

    @staticmethod
    def _key(value: str, *, kind: str) -> str:
        return require_synthetic_ref(value, field="idempotency_key", prefix=KEY_PREFIXES[kind])

    @staticmethod
    def _tenant(value: str) -> str:
        return require_synthetic_ref(value, field="tenant_id")


class _PatientScopedService(_ClinicalService):
    """Base for services that must resolve a patient through the identity port."""

    def __init__(self, identity: PatientIdentityPort, events: EventSink) -> None:
        super().__init__(events)
        self._identity = identity

    def _require_patient(self, *, tenant_id: str, patient_ref: str) -> PatientRef:
        patient = self._identity.resolve_patient(tenant_id=tenant_id, patient_ref=patient_ref)
        _check_tenant(patient.tenant_id, expected=tenant_id, kind="patient", key=patient.ref)
        return patient


class PractitionerRegistry(_ClinicalService):
    """Synthetic practitioner registry with qualification and active status."""

    def __init__(
        self,
        events: EventSink,
        practitioners: ClinicalRepository[Practitioner] | None = None,
    ) -> None:
        super().__init__(events)
        self._repo: ClinicalRepository[Practitioner] = (
            practitioners or InMemoryRepository[Practitioner]()
        )

    def register(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        role: PractitionerRole | str,
        qualification: str,
        active: bool = True,
    ) -> Practitioner:
        """Register a practitioner or replay an identical prior registration."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="practitioner")
        practitioner_role = _as_enum(PractitionerRole, role, field="role")
        qualification_text = require_label(qualification, field="qualification", max_length=120)
        fingerprint = _fingerprint(
            tenant_id=tenant,
            role=practitioner_role.value,
            qualification=qualification_text,
            active=active,
        )
        practitioner = Practitioner(
            practitioner_id=key,
            tenant_id=tenant,
            role=practitioner_role,
            qualification=qualification_text,
            active=active,
        )
        stored, created = self._create_once(
            self._repo, key=key, entity=practitioner, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.PRACTITIONER_REGISTERED,
                aggregate_type=AggregateType.PRACTITIONER,
                aggregate_id=key,
                tenant_id=tenant,
                payload={
                    "practitioner_ref": key,
                    "tenant_id": tenant,
                    "role": practitioner_role.value,
                    "qualification": qualification_text,
                    "active": active,
                },
            )
        return stored

    def get(self, *, tenant_id: str, practitioner_id: str) -> Practitioner:
        """Return a practitioner by synthetic id, scoped to the tenant."""
        tenant = self._tenant(tenant_id)
        key = require_synthetic_ref(
            practitioner_id, field="practitioner_id", prefix=KEY_PREFIXES["practitioner"]
        )
        practitioner = _require_entity(self._repo.get(key), kind="practitioner", key=key)
        _check_tenant(practitioner.tenant_id, expected=tenant, kind="practitioner", key=key)
        return practitioner

    def active_for_tenant(self, tenant_id: str) -> tuple[Practitioner, ...]:
        """Return active practitioners belonging to one synthetic tenant."""
        tenant = self._tenant(tenant_id)
        return tuple(
            practitioner
            for practitioner in self._repo.all()
            if practitioner.tenant_id == tenant and practitioner.active
        )


class OrganizationRegistry(_ClinicalService):
    """Synthetic organisation/facility registry with hierarchy validation."""

    def __init__(
        self,
        events: EventSink,
        organizations: ClinicalRepository[Organization] | None = None,
        facilities: ClinicalRepository[Facility] | None = None,
    ) -> None:
        super().__init__(events)
        self._organizations: ClinicalRepository[Organization] = (
            organizations or InMemoryRepository[Organization]()
        )
        self._facilities: ClinicalRepository[Facility] = (
            facilities or InMemoryRepository[Facility]()
        )

    def register_organization(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        label: str,
    ) -> Organization:
        """Register a synthetic organisation.

        Event schema 1.1.0 reserves ``EventType.ORGANIZATION_REGISTERED`` and
        ``AggregateType.ORGANIZATION`` for this structural container. This
        emitter is intentionally unchanged: the read-only cross-module
        conformance suite pins the exact clinical event count, so turning the
        previously silent registration into an emit is tracked as a handoff in
        ``GOVERNANCE/PRODUCTION_READINESS/WS_B_EVENT_SEMANTICS_REPORT.md``
        rather than silently changing that gate.
        """
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="organization")
        organization_label = require_label(label, field="label", max_length=120)
        fingerprint = _fingerprint(tenant_id=tenant, label=organization_label)
        organization = Organization(
            organization_id=key,
            tenant_id=tenant,
            label=organization_label,
            active=True,
        )
        stored, _ = self._create_once(
            self._organizations, key=key, entity=organization, fingerprint=fingerprint
        )
        return stored

    def register_facility(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        organization_id: str,
        label: str,
        facility_type: FacilityType | str,
    ) -> Facility:
        """Register a facility under an existing organisation in the same tenant."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="facility")
        organization = self.get_organization(tenant_id=tenant, organization_id=organization_id)
        if not organization.active:
            raise ClinicalValidationError(
                "organisation is not active", details={"field": "organization_id"}
            )
        facility_label = require_label(label, field="label", max_length=120)
        kind = _as_enum(FacilityType, facility_type, field="facility_type")
        fingerprint = _fingerprint(
            tenant_id=tenant,
            organization_id=organization.organization_id,
            label=facility_label,
            facility_type=kind.value,
        )
        facility = Facility(
            facility_id=key,
            tenant_id=tenant,
            organization_id=organization.organization_id,
            label=facility_label,
            facility_type=kind,
            active=True,
        )
        stored, created = self._create_once(
            self._facilities, key=key, entity=facility, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.FACILITY_REGISTERED,
                aggregate_type=AggregateType.FACILITY,
                aggregate_id=key,
                tenant_id=tenant,
                payload={
                    "facility_ref": key,
                    "tenant_id": tenant,
                    "organization_id": organization.organization_id,
                    "facility_type": kind.value,
                },
            )
        return stored

    def get_organization(self, *, tenant_id: str, organization_id: str) -> Organization:
        """Return an organisation scoped to the tenant."""
        tenant = self._tenant(tenant_id)
        key = require_synthetic_ref(
            organization_id, field="organization_id", prefix=KEY_PREFIXES["organization"]
        )
        organization = _require_entity(self._organizations.get(key), kind="organization", key=key)
        _check_tenant(organization.tenant_id, expected=tenant, kind="organization", key=key)
        return organization

    def get_facility(self, *, tenant_id: str, facility_id: str) -> Facility:
        """Return a facility scoped to the tenant."""
        tenant = self._tenant(tenant_id)
        key = require_synthetic_ref(
            facility_id, field="facility_id", prefix=KEY_PREFIXES["facility"]
        )
        facility = _require_entity(self._facilities.get(key), kind="facility", key=key)
        _check_tenant(facility.tenant_id, expected=tenant, kind="facility", key=key)
        return facility

    def require_facility(
        self,
        *,
        tenant_id: str,
        facility_id: str,
        organization_id: str | None = None,
    ) -> Facility:
        """Validate a facility and optionally its parent organisation."""
        facility = self.get_facility(tenant_id=tenant_id, facility_id=facility_id)
        if not facility.active:
            raise ClinicalValidationError("facility is not active", details={"key": facility_id})
        if organization_id is not None:
            organization = self.get_organization(
                tenant_id=tenant_id, organization_id=organization_id
            )
            if facility.organization_id != organization.organization_id:
                raise ForbiddenSyntheticOperationError(
                    "facility does not belong to the given organisation",
                    details={"facility_id": facility_id, "organization_id": organization_id},
                )
        return facility

    def facilities_for_organization(
        self, *, tenant_id: str, organization_id: str
    ) -> tuple[Facility, ...]:
        """Return the facilities owned by one organisation."""
        organization = self.get_organization(tenant_id=tenant_id, organization_id=organization_id)
        return tuple(
            facility
            for facility in self._facilities.all()
            if facility.organization_id == organization.organization_id
            and facility.tenant_id == organization.tenant_id
        )


class EncounterService(_PatientScopedService):
    """Encounter lifecycle state machine with notes and patient scoping."""

    def __init__(
        self,
        identity: PatientIdentityPort,
        practitioners: PractitionerRegistry,
        organizations: OrganizationRegistry,
        events: EventSink,
        encounters: ClinicalRepository[Encounter] | None = None,
        notes: ClinicalRepository[ClinicalNote] | None = None,
        transitions: ClinicalRepository[Encounter] | None = None,
    ) -> None:
        super().__init__(identity, events)
        self._practitioners = practitioners
        self._organizations = organizations
        self._repo: ClinicalRepository[Encounter] = encounters or InMemoryRepository[Encounter]()
        self._notes: ClinicalRepository[ClinicalNote] = notes or InMemoryRepository[ClinicalNote]()
        self._transitions: ClinicalRepository[Encounter] = (
            transitions or InMemoryRepository[Encounter]()
        )

    def create(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        patient_ref: str,
        practitioner_id: str,
        facility_id: str,
        reason: str,
    ) -> Encounter:
        """Create a planned encounter or replay an identical prior creation."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="encounter")
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        practitioner = self._practitioners.get(tenant_id=tenant, practitioner_id=practitioner_id)
        if not practitioner.active:
            raise ClinicalValidationError(
                "practitioner is not active", details={"key": practitioner_id}
            )
        self._organizations.require_facility(tenant_id=tenant, facility_id=facility_id)
        reason_text = require_label(reason, field="reason", max_length=500)
        fingerprint = _fingerprint(
            tenant_id=tenant,
            patient_ref=patient.ref,
            practitioner_id=practitioner.practitioner_id,
            facility_id=facility_id,
            reason=reason_text,
        )
        encounter = Encounter(
            encounter_id=key,
            tenant_id=tenant,
            patient_ref=patient.ref,
            practitioner_id=practitioner.practitioner_id,
            facility_id=facility_id,
            status=EncounterStatus.PLANNED,
            reason=reason_text,
            version=1,
            created_at=utc_now_iso(),
        )
        stored, created = self._create_once(
            self._repo, key=key, entity=encounter, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.ENCOUNTER_CREATED,
                aggregate_type=AggregateType.ENCOUNTER,
                aggregate_id=key,
                tenant_id=tenant,
                payload={
                    "encounter_ref": key,
                    "tenant_id": tenant,
                    "patient_ref": patient.ref,
                    "status": EncounterStatus.PLANNED.value,
                    "practitioner_id": practitioner.practitioner_id,
                    "facility_id": facility_id,
                },
            )
        return stored

    def transition(
        self,
        *,
        tenant_id: str,
        encounter_id: str,
        to_status: EncounterStatus | str,
        idempotency_key: str,
        to_facility_ref: str | None = None,
        disposition: str | None = None,
    ) -> Encounter:
        """Apply a legal lifecycle transition or replay an identical one.

        The richer encounter lifecycle events carry real context from the
        encounter and its facility: an admission carries ``facility_ref``, a
        transfer carries ``from_facility_ref``/``to_facility_ref``, a discharge
        carries ``disposition`` and a cancellation carries ``reason``. When a
        caller does not supply ``to_facility_ref`` or ``disposition``, the
        encounter's own facility and the target status are used as documented
        synthetic defaults so the event catalogue is always satisfied from real
        state rather than fabricated identifiers.
        """
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="transition")
        target = _as_enum(EncounterStatus, to_status, field="to_status")
        current = self.get_encounter(tenant_id=tenant, encounter_id=encounter_id)
        self._require_patient(tenant_id=tenant, patient_ref=current.patient_ref)
        safe_to_facility = (
            require_synthetic_ref(
                to_facility_ref, field="to_facility_ref", prefix=KEY_PREFIXES["facility"]
            )
            if to_facility_ref is not None
            else current.facility_id
        )
        safe_disposition = (
            require_label(disposition, field="disposition", max_length=120)
            if disposition is not None
            else target.value
        )
        fingerprint = _fingerprint(
            tenant_id=tenant,
            encounter_id=current.encounter_id,
            to_status=target.value,
            to_facility_ref=safe_to_facility,
            disposition=safe_disposition,
        )

        def apply() -> Encounter:
            if not current.can_transition_to(target):
                raise InvalidStateTransitionError(
                    "illegal synthetic encounter transition",
                    details={
                        "encounter_id": current.encounter_id,
                        "from_status": current.status.value,
                        "to_status": target.value,
                    },
                )
            updated = replace(
                current,
                status=target,
                version=current.version + 1,
            )
            self._repo.save(current.encounter_id, updated)
            payload: dict[str, object] = {
                "encounter_ref": current.encounter_id,
                "tenant_id": tenant,
                "patient_ref": current.patient_ref,
                "transition": True,
                "from_status": current.status.value,
                "to_status": target.value,
                "version": updated.version,
            }
            if target is EncounterStatus.ADMITTED:
                payload["facility_ref"] = current.facility_id
            elif target is EncounterStatus.TRANSFERRED:
                payload["from_facility_ref"] = current.facility_id
                payload["to_facility_ref"] = safe_to_facility
            elif target is EncounterStatus.DISCHARGED:
                payload["disposition"] = safe_disposition
            elif target is EncounterStatus.CANCELLED:
                payload["reason"] = current.reason
            self._emit(
                event_type=TRANSITION_EVENTS[target],
                aggregate_type=AggregateType.ENCOUNTER,
                aggregate_id=current.encounter_id,
                tenant_id=tenant,
                payload=payload,
            )
            return updated

        updated, _ = self._change_once(
            self._transitions, key=key, fingerprint=fingerprint, apply=apply
        )
        return updated

    def add_note(
        self,
        *,
        tenant_id: str,
        encounter_id: str,
        idempotency_key: str,
        author_practitioner_id: str,
        text: str,
    ) -> ClinicalNote:
        """Add a note to one encounter, scoped to its patient and tenant."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="note")
        encounter = self.get_encounter(tenant_id=tenant, encounter_id=encounter_id)
        self._require_patient(tenant_id=tenant, patient_ref=encounter.patient_ref)
        author = self._practitioners.get(tenant_id=tenant, practitioner_id=author_practitioner_id)
        if not author.active:
            raise ClinicalValidationError(
                "note author is not active", details={"key": author_practitioner_id}
            )
        note_text = require_label(text, field="text", max_length=2000)
        fingerprint = _fingerprint(
            tenant_id=tenant,
            encounter_id=encounter.encounter_id,
            author_practitioner_id=author.practitioner_id,
            text=note_text,
        )
        note = ClinicalNote(
            note_id=key,
            tenant_id=tenant,
            encounter_id=encounter.encounter_id,
            patient_ref=encounter.patient_ref,
            author_practitioner_id=author.practitioner_id,
            text=note_text,
            created_at=utc_now_iso(),
        )
        stored, created = self._create_once(
            self._notes, key=key, entity=note, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.NOTE_ADDED,
                aggregate_type=AggregateType.ENCOUNTER,
                aggregate_id=encounter.encounter_id,
                tenant_id=tenant,
                payload={
                    "note_ref": key,
                    "medical_record_ref": encounter.patient_ref,
                    "note_id": key,
                    "patient_ref": encounter.patient_ref,
                },
            )
        return stored

    def get_encounter(self, *, tenant_id: str, encounter_id: str) -> Encounter:
        """Return an encounter scoped to the tenant."""
        tenant = self._tenant(tenant_id)
        key = require_synthetic_ref(
            encounter_id, field="encounter_id", prefix=KEY_PREFIXES["encounter"]
        )
        encounter = _require_entity(self._repo.get(key), kind="encounter", key=key)
        _check_tenant(encounter.tenant_id, expected=tenant, kind="encounter", key=key)
        return encounter

    def list_for_patient(self, *, tenant_id: str, patient_ref: str) -> tuple[Encounter, ...]:
        """Return all encounters of one synthetic patient in one tenant."""
        tenant = self._tenant(tenant_id)
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        return tuple(
            sorted(
                (
                    encounter
                    for encounter in self._repo.all()
                    if encounter.patient_ref == patient.ref and encounter.tenant_id == tenant
                ),
                key=lambda encounter: (encounter.created_at, encounter.encounter_id),
            )
        )

    def notes_for_encounter(self, *, tenant_id: str, encounter_id: str) -> tuple[ClinicalNote, ...]:
        """Return notes attached to one encounter."""
        encounter = self.get_encounter(tenant_id=tenant_id, encounter_id=encounter_id)
        return tuple(
            sorted(
                (
                    note
                    for note in self._notes.all()
                    if note.encounter_id == encounter.encounter_id
                    and note.tenant_id == encounter.tenant_id
                ),
                key=lambda note: (note.created_at, note.note_id),
            )
        )

    def notes_for_patient(self, *, tenant_id: str, patient_ref: str) -> tuple[ClinicalNote, ...]:
        """Return all notes of one synthetic patient across their encounters."""
        encounters = self.list_for_patient(tenant_id=tenant_id, patient_ref=patient_ref)
        notes: list[ClinicalNote] = []
        for encounter in encounters:
            notes.extend(
                self.notes_for_encounter(tenant_id=tenant_id, encounter_id=encounter.encounter_id)
            )
        return tuple(notes)


class DiagnosisService(_PatientScopedService):
    """Coded problems asserted against one synthetic encounter."""

    def __init__(
        self,
        identity: PatientIdentityPort,
        encounters: EncounterService,
        events: EventSink,
        diagnoses: ClinicalRepository[Diagnosis] | None = None,
        transitions: ClinicalRepository[Diagnosis] | None = None,
    ) -> None:
        super().__init__(identity, events)
        self._encounters = encounters
        self._repo: ClinicalRepository[Diagnosis] = diagnoses or InMemoryRepository[Diagnosis]()
        self._transitions: ClinicalRepository[Diagnosis] = (
            transitions or InMemoryRepository[Diagnosis]()
        )

    def record(
        self,
        *,
        tenant_id: str,
        idempotency_key: str,
        patient_ref: str,
        encounter_id: str,
        code: str,
        description: str,
        severity: Severity | str,
    ) -> Diagnosis:
        """Assert an ICD-style problem on one encounter of the patient."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="diagnosis")
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        encounter = self._encounters.get_encounter(tenant_id=tenant, encounter_id=encounter_id)
        if encounter.patient_ref != patient.ref:
            raise ForbiddenSyntheticOperationError(
                "encounter belongs to a different synthetic patient",
                details={"encounter_id": encounter_id},
            )
        icd_code = require_icd_code(code)
        description_text = require_label(description, field="description", max_length=500)
        level = _as_enum(Severity, severity, field="severity")
        fingerprint = _fingerprint(
            tenant_id=tenant,
            patient_ref=patient.ref,
            encounter_id=encounter.encounter_id,
            code=icd_code,
            description=description_text,
            severity=level.value,
        )
        diagnosis = Diagnosis(
            diagnosis_id=key,
            tenant_id=tenant,
            patient_ref=patient.ref,
            encounter_id=encounter.encounter_id,
            code=icd_code,
            description=description_text,
            severity=level,
            status=DiagnosisStatus.ACTIVE,
            asserted_at=utc_now_iso(),
            resolved_at=None,
            version=1,
        )
        stored, created = self._create_once(
            self._repo, key=key, entity=diagnosis, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.DIAGNOSIS_RECORDED,
                aggregate_type=AggregateType.DIAGNOSIS,
                aggregate_id=key,
                tenant_id=tenant,
                payload={
                    "diagnosis_ref": key,
                    "encounter_ref": encounter.encounter_id,
                    "patient_ref": patient.ref,
                    "encounter_id": encounter.encounter_id,
                    "code": icd_code,
                    "severity": level.value,
                },
            )
        return stored

    def resolve(
        self,
        *,
        tenant_id: str,
        diagnosis_id: str,
        idempotency_key: str,
    ) -> Diagnosis:
        """Resolve an active problem; replaying the same resolve is idempotent."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="transition")
        current = self.get_diagnosis(tenant_id=tenant, diagnosis_id=diagnosis_id)
        self._require_patient(tenant_id=tenant, patient_ref=current.patient_ref)
        fingerprint = _fingerprint(
            tenant_id=tenant,
            diagnosis_id=current.diagnosis_id,
            action="resolve",
        )

        def apply() -> Diagnosis:
            if current.status is DiagnosisStatus.RESOLVED:
                raise InvalidStateTransitionError(
                    "diagnosis is already resolved",
                    details={"diagnosis_id": current.diagnosis_id},
                )
            updated = replace(
                current,
                status=DiagnosisStatus.RESOLVED,
                resolved_at=utc_now_iso(),
                version=current.version + 1,
            )
            self._repo.save(current.diagnosis_id, updated)
            self._emit(
                event_type=EventType.DIAGNOSIS_RESOLVED,
                aggregate_type=AggregateType.DIAGNOSIS,
                aggregate_id=current.diagnosis_id,
                tenant_id=tenant,
                payload={
                    "diagnosis_ref": current.diagnosis_id,
                    "encounter_ref": current.encounter_id,
                    "patient_ref": current.patient_ref,
                    "transition": "resolve",
                    "status": DiagnosisStatus.RESOLVED.value,
                    "version": updated.version,
                },
            )
            return updated

        updated, _ = self._change_once(
            self._transitions, key=key, fingerprint=fingerprint, apply=apply
        )
        return updated

    def get_diagnosis(self, *, tenant_id: str, diagnosis_id: str) -> Diagnosis:
        """Return a diagnosis scoped to the tenant."""
        tenant = self._tenant(tenant_id)
        key = require_synthetic_ref(
            diagnosis_id, field="diagnosis_id", prefix=KEY_PREFIXES["diagnosis"]
        )
        diagnosis = _require_entity(self._repo.get(key), kind="diagnosis", key=key)
        _check_tenant(diagnosis.tenant_id, expected=tenant, kind="diagnosis", key=key)
        return diagnosis

    def list_for_encounter(self, *, tenant_id: str, encounter_id: str) -> tuple[Diagnosis, ...]:
        """Return problems asserted on one encounter."""
        encounter = self._encounters.get_encounter(tenant_id=tenant_id, encounter_id=encounter_id)
        return tuple(
            sorted(
                (
                    diagnosis
                    for diagnosis in self._repo.all()
                    if diagnosis.encounter_id == encounter.encounter_id
                    and diagnosis.tenant_id == encounter.tenant_id
                ),
                key=lambda diagnosis: (diagnosis.asserted_at, diagnosis.diagnosis_id),
            )
        )

    def list_for_patient(self, *, tenant_id: str, patient_ref: str) -> tuple[Diagnosis, ...]:
        """Return problems asserted for one synthetic patient."""
        tenant = self._tenant(tenant_id)
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        return tuple(
            sorted(
                (
                    diagnosis
                    for diagnosis in self._repo.all()
                    if diagnosis.patient_ref == patient.ref and diagnosis.tenant_id == tenant
                ),
                key=lambda diagnosis: (diagnosis.asserted_at, diagnosis.diagnosis_id),
            )
        )


class ObservationService(_PatientScopedService):
    """Coded vital signs and observations with validated units and ordering."""

    def __init__(
        self,
        identity: PatientIdentityPort,
        encounters: EncounterService,
        events: EventSink,
        observations: ClinicalRepository[Observation] | None = None,
    ) -> None:
        super().__init__(identity, events)
        self._encounters = encounters
        self._repo: ClinicalRepository[Observation] = (
            observations or InMemoryRepository[Observation]()
        )

    def record(
        self,
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
        """Record an observation or replay an identical prior recording."""
        tenant = self._tenant(tenant_id)
        key = self._key(idempotency_key, kind="observation")
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        encounter = self._encounters.get_encounter(tenant_id=tenant, encounter_id=encounter_id)
        if encounter.patient_ref != patient.ref:
            raise ForbiddenSyntheticOperationError(
                "encounter belongs to a different synthetic patient",
                details={"encounter_id": encounter_id},
            )
        loinc_code = require_loinc_code(code)
        display_text = require_label(display, field="display", max_length=200)
        number = require_finite_number(value, field="value")
        valid_unit = require_unit(loinc_code, unit)
        moment = require_utc_timestamp(recorded_at, field="recorded_at")
        fingerprint = _fingerprint(
            tenant_id=tenant,
            patient_ref=patient.ref,
            encounter_id=encounter.encounter_id,
            code=loinc_code,
            display=display_text,
            value=number,
            unit=valid_unit,
            recorded_at=moment,
        )
        observation = Observation(
            observation_id=key,
            tenant_id=tenant,
            patient_ref=patient.ref,
            encounter_id=encounter.encounter_id,
            code=loinc_code,
            display=display_text,
            value=number,
            unit=valid_unit,
            recorded_at=moment,
        )
        stored, created = self._create_once(
            self._repo, key=key, entity=observation, fingerprint=fingerprint
        )
        if created:
            self._emit(
                event_type=EventType.OBSERVATION_RECORDED,
                aggregate_type=AggregateType.OBSERVATION,
                aggregate_id=key,
                tenant_id=tenant,
                payload={
                    "observation_ref": key,
                    "patient_ref": patient.ref,
                    "encounter_id": encounter.encounter_id,
                    "code": loinc_code,
                    "unit": valid_unit,
                },
            )
        return stored

    def query(
        self,
        *,
        tenant_id: str,
        patient_ref: str,
        encounter_id: str | None = None,
        code: str | None = None,
    ) -> tuple[Observation, ...]:
        """Return one patient's observations in recorded-at order."""
        tenant = self._tenant(tenant_id)
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        allowed_encounter: str | None = None
        if encounter_id is not None:
            encounter = self._encounters.get_encounter(tenant_id=tenant, encounter_id=encounter_id)
            if encounter.patient_ref != patient.ref:
                raise ForbiddenSyntheticOperationError(
                    "encounter belongs to a different synthetic patient",
                    details={"encounter_id": encounter_id},
                )
            allowed_encounter = encounter.encounter_id
        wanted_code = require_loinc_code(code) if code is not None else None
        matches = (
            observation
            for observation in self._repo.all()
            if observation.patient_ref == patient.ref
            and observation.tenant_id == tenant
            and (allowed_encounter is None or observation.encounter_id == allowed_encounter)
            and (wanted_code is None or observation.code == wanted_code)
        )
        return tuple(
            sorted(
                matches,
                key=lambda observation: (observation.recorded_at, observation.observation_id),
            )
        )


class MedicalRecordService(_PatientScopedService):
    """Non-identity-linkage aggregate over one synthetic patient's clinical data."""

    def __init__(
        self,
        identity: PatientIdentityPort,
        encounters: EncounterService,
        diagnoses: DiagnosisService,
        observations: ObservationService,
        events: EventSink,
    ) -> None:
        super().__init__(identity, events)
        self._encounters = encounters
        self._diagnoses = diagnoses
        self._observations = observations

    def aggregate(self, *, scope: RecordScope) -> MedicalRecordView:
        """Aggregate all clinical items for exactly one synthetic patient."""
        patient_ref = scope.assert_single_patient()
        tenant = self._tenant(scope.tenant_id)
        patient = self._require_patient(tenant_id=tenant, patient_ref=patient_ref)
        return MedicalRecordView(
            tenant_id=tenant,
            patient_ref=patient.ref,
            encounters=self._encounters.list_for_patient(tenant_id=tenant, patient_ref=patient.ref),
            diagnoses=self._diagnoses.list_for_patient(tenant_id=tenant, patient_ref=patient.ref),
            observations=self._observations.query(tenant_id=tenant, patient_ref=patient.ref),
            notes=self._encounters.notes_for_patient(tenant_id=tenant, patient_ref=patient.ref),
            opened_at=utc_now_iso(),
        )

    def open(self, *, scope: RecordScope) -> MedicalRecordView:
        """Aggregate and emit a medical-record-opened event for one patient."""
        view = self.aggregate(scope=scope)
        self._emit(
            event_type=EventType.MEDICAL_RECORD_OPENED,
            aggregate_type=AggregateType.MEDICAL_RECORD,
            aggregate_id=view.patient_ref,
            tenant_id=view.tenant_id,
            payload={
                "medical_record_ref": view.patient_ref,
                "patient_ref": view.patient_ref,
                "encounter_count": len(view.encounters),
                "diagnosis_count": len(view.diagnoses),
                "observation_count": len(view.observations),
                "note_count": len(view.notes),
            },
        )
        return view
