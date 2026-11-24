"""Framework-agnostic synthetic API client contract and in-memory fake.

The abstract base class is the single interface future client adapters (web,
Android, iOS, desktop) must implement for the 10 readiness-eligible domains.
It uses no HTTP library and contains no endpoint, host, port or credential.

Every operation takes an explicit synthetic tenant and an opaque
:class:`~app.health_core.identity.PatientRef`. The fake implementation resolves
that reference through the shared :class:`PatientIdentityPort`, fails closed on
unknown or cross-tenant references, and emits shared ``DomainEvent`` records
that can be fed directly into the offline outbox.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from app.health_core.common import (
    AggregateType,
    DomainEvent,
    EventType,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    is_synthetic_id,
    new_event,
    new_synthetic_id,
)
from app.health_core.identity import PatientIdentityPort, PatientRef


class DomainCode(StrEnum):
    """The 10 domains eligible under the Health Core readiness assessment."""

    PRACTITIONER = "practitioner"
    FACILITY = "organization_facility"
    MEDICAL_RECORD = "medical_record"
    ENCOUNTER = "encounter"
    DIAGNOSIS = "diagnosis"
    OBSERVATION = "observation"
    LAB_ORDER = "lab_order"
    SPECIMEN = "specimen"
    LAB_RESULT = "lab_result"
    RESULT_VERIFICATION = "result_verification"


ELIGIBLE_DOMAINS: tuple[DomainCode, ...] = tuple(DomainCode)


@dataclass(frozen=True, slots=True)
class ApiResult:
    """Immutable, synthetic-by-construction result record."""

    domain: DomainCode
    tenant_id: str
    patient_ref: str
    entity_id: str
    version: int
    data: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        """Return a stable serialisation for contract tests and audit review."""
        return {
            "domain": self.domain.value,
            "tenant_id": self.tenant_id,
            "patient_ref": self.patient_ref,
            "entity_id": self.entity_id,
            "version": self.version,
            "data": dict(self.data),
        }


class SyntheticApiClient(ABC):
    """Single shared interface for all synthetic client integrations."""

    @abstractmethod
    def create_practitioner(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_practitioners(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_facility(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_facilities(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_medical_record(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_medical_records(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_encounter(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_encounters(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_diagnosis(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_diagnoses(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_observation(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_observations(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_lab_order(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_lab_orders(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_specimen(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_specimens(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_lab_result(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_lab_results(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...

    @abstractmethod
    def create_verification(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult: ...

    @abstractmethod
    def list_verifications(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]: ...


_EVENT_SIGNATURES: Mapping[DomainCode, tuple[EventType, AggregateType, str]] = MappingProxyType(
    {
        DomainCode.PRACTITIONER: (EventType.PRACTITIONER_REGISTERED, AggregateType.PRACTITIONER, "PRAC"),
        DomainCode.FACILITY: (EventType.FACILITY_REGISTERED, AggregateType.FACILITY, "FAC"),
        DomainCode.MEDICAL_RECORD: (
            EventType.MEDICAL_RECORD_OPENED,
            AggregateType.MEDICAL_RECORD,
            "MREC",
        ),
        DomainCode.ENCOUNTER: (EventType.ENCOUNTER_CREATED, AggregateType.ENCOUNTER, "ENC"),
        DomainCode.DIAGNOSIS: (EventType.DIAGNOSIS_RECORDED, AggregateType.DIAGNOSIS, "DIAG"),
        DomainCode.OBSERVATION: (
            EventType.OBSERVATION_RECORDED,
            AggregateType.OBSERVATION,
            "OBS",
        ),
        DomainCode.LAB_ORDER: (EventType.LAB_ORDER_PLACED, AggregateType.LAB_ORDER, "LORD"),
        DomainCode.SPECIMEN: (EventType.SPECIMEN_REGISTERED, AggregateType.SPECIMEN, "SPEC"),
        DomainCode.LAB_RESULT: (EventType.RESULT_RECORDED, AggregateType.LAB_RESULT, "LRES"),
        DomainCode.RESULT_VERIFICATION: (
            EventType.RESULT_VERIFIED,
            AggregateType.VERIFICATION,
            "RVER",
        ),
    }
)


class InMemorySyntheticApiClient(SyntheticApiClient):
    """In-memory fake: process-local records, no persistence and no transport."""

    def __init__(self, identity: PatientIdentityPort) -> None:
        self._identity = identity
        self._records: dict[DomainCode, dict[str, ApiResult]] = {
            domain: {} for domain in DomainCode
        }
        self._events: list[DomainEvent] = []

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        """Emitted synthetic events, in creation order."""
        return tuple(self._events)

    def _scope(self, tenant_id: str, patient_ref: PatientRef) -> PatientRef:
        if not is_synthetic_id(tenant_id):
            raise InvalidSyntheticReferenceError(
                "tenant_id must be a SYN- prefixed synthetic reference",
                details={"field": "tenant_id"},
            )
        resolved = self._identity.resolve_patient(
            tenant_id=tenant_id, patient_ref=patient_ref.ref
        )
        if resolved != patient_ref:
            raise TenantMismatchError(
                "synthetic patient reference does not match its tenant",
                details={"tenant_id": tenant_id},
            )
        return resolved

    def _create(
        self,
        domain: DomainCode,
        tenant_id: str,
        patient_ref: PatientRef,
        data: Mapping[str, object],
    ) -> ApiResult:
        self._scope(tenant_id, patient_ref)
        event_type, aggregate_type, prefix = _EVENT_SIGNATURES[domain]
        entity_id = new_synthetic_id(prefix)
        record = ApiResult(
            domain=domain,
            tenant_id=tenant_id,
            patient_ref=patient_ref.ref,
            entity_id=entity_id,
            version=1,
            data=MappingProxyType(dict(data)),
        )
        self._records[domain][entity_id] = record
        self._events.append(
            new_event(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=entity_id,
                tenant_id=tenant_id,
                payload={
                    "patient_ref": patient_ref.ref,
                    "domain": domain.value,
                    "record": record.to_dict(),
                },
            )
        )
        return record

    def _list(
        self, domain: DomainCode, tenant_id: str, patient_ref: PatientRef
    ) -> tuple[ApiResult, ...]:
        self._scope(tenant_id, patient_ref)
        return tuple(
            record
            for record in self._records[domain].values()
            if record.tenant_id == tenant_id and record.patient_ref == patient_ref.ref
        )

    def create_practitioner(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.PRACTITIONER, tenant_id, patient_ref, data)

    def list_practitioners(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.PRACTITIONER, tenant_id, patient_ref)

    def create_facility(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.FACILITY, tenant_id, patient_ref, data)

    def list_facilities(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.FACILITY, tenant_id, patient_ref)

    def create_medical_record(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.MEDICAL_RECORD, tenant_id, patient_ref, data)

    def list_medical_records(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.MEDICAL_RECORD, tenant_id, patient_ref)

    def create_encounter(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.ENCOUNTER, tenant_id, patient_ref, data)

    def list_encounters(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.ENCOUNTER, tenant_id, patient_ref)

    def create_diagnosis(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.DIAGNOSIS, tenant_id, patient_ref, data)

    def list_diagnoses(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.DIAGNOSIS, tenant_id, patient_ref)

    def create_observation(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.OBSERVATION, tenant_id, patient_ref, data)

    def list_observations(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.OBSERVATION, tenant_id, patient_ref)

    def create_lab_order(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.LAB_ORDER, tenant_id, patient_ref, data)

    def list_lab_orders(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.LAB_ORDER, tenant_id, patient_ref)

    def create_specimen(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.SPECIMEN, tenant_id, patient_ref, data)

    def list_specimens(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.SPECIMEN, tenant_id, patient_ref)

    def create_lab_result(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.LAB_RESULT, tenant_id, patient_ref, data)

    def list_lab_results(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.LAB_RESULT, tenant_id, patient_ref)

    def create_verification(
        self, *, tenant_id: str, patient_ref: PatientRef, data: Mapping[str, object]
    ) -> ApiResult:
        return self._create(DomainCode.RESULT_VERIFICATION, tenant_id, patient_ref, data)

    def list_verifications(self, *, tenant_id: str, patient_ref: PatientRef) -> tuple[ApiResult, ...]:
        return self._list(DomainCode.RESULT_VERIFICATION, tenant_id, patient_ref)
