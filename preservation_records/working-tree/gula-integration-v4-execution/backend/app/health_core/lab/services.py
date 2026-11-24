"""Synthetic laboratory workflow service.

This service is the only public entry point for lab operations. It resolves every
patient through :class:`PatientIdentityPort`, enforces tenant ownership on every
operation, emits immutable domain events and never touches a database, network,
MPI or analyzer. All identifiers are generated locally with a ``SYN-`` prefix.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime

from app.health_core.common.errors import (
    DuplicateEntityError,
    InvalidStateTransitionError,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
)
from app.health_core.common.event_types import AggregateType, EventType
from app.health_core.common.events import DomainEvent, new_event
from app.health_core.common.ids import is_synthetic_id, new_synthetic_id, reject_national_identifier
from app.health_core.identity.port import PatientIdentityPort, PatientRef
from app.health_core.lab.catalogue import TestDefinition, get_test_definition
from app.health_core.lab.errors import (
    InvalidActorError,
    InvalidResultError,
    LabWorkflowError,
    UnknownLabEntityError,
)
from app.health_core.lab.models import (
    LEGAL_SPECIMEN_TRANSITIONS,
    LEGAL_VERIFICATION_TRANSITIONS,
    RESULT_VERIFICATION_REJECTED_EVENT,
    SPECIMEN_FINAL_EVENT,
    SPECIMEN_IN_TESTING_EVENT,
    TEST_COMPLETED_EVENT,
    TEST_ENTERED_EVENT,
    VERIFICATION_PENDING_EVENT,
    CustodyEntry,
    LabOrder,
    LabOrderStatus,
    LabResult,
    Priority,
    ResultAmendment,
    Specimen,
    SpecimenStatus,
    TestExecution,
    TestExecutionStatus,
    Verification,
    VerificationDecision,
    VerificationStatus,
)
from app.health_core.lab.repositories import (
    InMemoryCustodyRepository,
    InMemoryEventStore,
    InMemoryLabOrderRepository,
    InMemoryResultRepository,
    InMemorySpecimenRepository,
    InMemoryTestExecutionRepository,
    InMemoryVerificationRepository,
)

_SPECIMEN_EVENT_TYPES: dict[SpecimenStatus, str] = {
    SpecimenStatus.COLLECTED: str(EventType.SPECIMEN_COLLECTED),
    SpecimenStatus.RECEIVED: str(EventType.SPECIMEN_RECEIVED),
    SpecimenStatus.IN_TESTING: SPECIMEN_IN_TESTING_EVENT,
    SpecimenStatus.REJECTED: str(EventType.SPECIMEN_REJECTED),
    SpecimenStatus.FINAL: SPECIMEN_FINAL_EVENT,
}


class LabWorkflowService:
    """Coordinate the six synthetic lab domains in a single in-memory workflow."""

    def __init__(
        self,
        *,
        identity: PatientIdentityPort,
        orders: InMemoryLabOrderRepository | None = None,
        specimens: InMemorySpecimenRepository | None = None,
        custody: InMemoryCustodyRepository | None = None,
        executions: InMemoryTestExecutionRepository | None = None,
        results: InMemoryResultRepository | None = None,
        verifications: InMemoryVerificationRepository | None = None,
        events: InMemoryEventStore | None = None,
    ) -> None:
        self._identity = identity
        self._orders = orders or InMemoryLabOrderRepository()
        self._specimens = specimens or InMemorySpecimenRepository()
        self._custody = custody or InMemoryCustodyRepository()
        self._executions = executions or InMemoryTestExecutionRepository()
        self._results = results or InMemoryResultRepository()
        self._verifications = verifications or InMemoryVerificationRepository()
        self._events = events or InMemoryEventStore()

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _require_synthetic(value: str, *, field: str) -> str:
        reject_national_identifier(value, field=field)
        if not is_synthetic_id(value):
            raise InvalidSyntheticReferenceError(
                f"{field} must be a SYN- prefixed synthetic reference",
                details={"field": field},
            )
        return value

    def _require_actor(self, actor: str, *, field: str = "actor_id") -> str:
        try:
            return self._require_synthetic(actor, field=field)
        except InvalidSyntheticReferenceError as exc:
            raise InvalidActorError(
                f"{field} must be a synthetic SYN- reference",
                details={"field": field},
            ) from exc

    @classmethod
    def _require_barcode(cls, barcode: str) -> str:
        cls._require_synthetic(barcode, field="barcode")
        if not barcode.startswith("SYN-BAR-"):
            raise InvalidSyntheticReferenceError(
                "barcode must use the SYN-BAR- synthetic prefix",
                details={"field": "barcode"},
            )
        return barcode

    def _resolve_patient(self, tenant_id: str, patient_ref: str) -> PatientRef:
        self._require_synthetic(tenant_id, field="tenant_id")
        self._require_synthetic(patient_ref, field="patient_ref")
        return self._identity.resolve_patient(tenant_id=tenant_id, patient_ref=patient_ref)

    def _get_order(self, tenant_id: str, order_id: str) -> LabOrder:
        self._require_synthetic(tenant_id, field="tenant_id")
        order = self._orders.get(order_id)
        if order is None:
            raise UnknownLabEntityError("synthetic lab order not found", details={"order_id": order_id})
        if order.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic lab order belongs to another tenant",
                details={"order_id": order_id, "tenant_id": tenant_id},
            )
        return order

    def _get_specimen(self, tenant_id: str, specimen_id: str) -> Specimen:
        self._require_synthetic(tenant_id, field="tenant_id")
        specimen = self._specimens.get(specimen_id)
        if specimen is None:
            raise UnknownLabEntityError(
                "synthetic specimen not found", details={"specimen_id": specimen_id}
            )
        if specimen.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic specimen belongs to another tenant",
                details={"specimen_id": specimen_id, "tenant_id": tenant_id},
            )
        return specimen

    def _get_result(self, tenant_id: str, result_id: str) -> LabResult:
        self._require_synthetic(tenant_id, field="tenant_id")
        result = self._results.get(result_id)
        if result is None:
            raise UnknownLabEntityError("synthetic result not found", details={"result_id": result_id})
        if result.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic result belongs to another tenant",
                details={"result_id": result_id, "tenant_id": tenant_id},
            )
        return result

    def _get_execution(self, tenant_id: str, execution_id: str) -> TestExecution:
        self._require_synthetic(tenant_id, field="tenant_id")
        execution = self._executions.get(execution_id)
        if execution is None:
            raise UnknownLabEntityError(
                "synthetic test execution not found", details={"execution_id": execution_id}
            )
        if execution.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic test execution belongs to another tenant",
                details={"execution_id": execution_id, "tenant_id": tenant_id},
            )
        return execution

    def _get_verification(self, tenant_id: str, verification_id: str) -> Verification:
        self._require_synthetic(tenant_id, field="tenant_id")
        verification = self._verifications.get(verification_id)
        if verification is None:
            raise UnknownLabEntityError(
                "synthetic verification not found", details={"verification_id": verification_id}
            )
        if verification.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic verification belongs to another tenant",
                details={"verification_id": verification_id, "tenant_id": tenant_id},
            )
        return verification

    def _emit(
        self,
        *,
        event_type: str,
        aggregate_type: AggregateType,
        aggregate_id: str,
        tenant_id: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        self._events.append(
            new_event(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                tenant_id=tenant_id,
                payload=payload,
            )
        )

    def _append_custody(
        self,
        specimen: Specimen,
        *,
        from_status: SpecimenStatus | None,
        to_status: SpecimenStatus,
        actor_id: str,
        reason: str | None,
    ) -> None:
        entry = CustodyEntry(
            entry_id=new_synthetic_id("CUST"),
            specimen_id=specimen.specimen_id,
            tenant_id=specimen.tenant_id,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            occurred_at=self._now(),
            reason=reason,
        )
        self._custody.append(entry)

    @staticmethod
    def _critical_flag(definition: TestDefinition, value: float) -> bool:
        return bool(
            (definition.critical_low is not None and value < definition.critical_low)
            or (definition.critical_high is not None and value > definition.critical_high)
        )

    def _transition_specimen(
        self,
        specimen: Specimen,
        target: SpecimenStatus,
        actor: str,
        reason: str | None,
    ) -> Specimen:
        allowed = LEGAL_SPECIMEN_TRANSITIONS.get(specimen.status, frozenset())
        if target not in allowed:
            raise InvalidStateTransitionError(
                f"illegal specimen transition {specimen.status.value} -> {target.value}",
                details={"from": specimen.status.value, "to": target.value},
            )
        clean_reason = reason.strip() if reason and reason.strip() else None
        if target is SpecimenStatus.REJECTED and clean_reason is None:
            raise LabWorkflowError("a rejection reason is required")
        updated = replace(
            specimen,
            status=target,
            rejection_reason=clean_reason if target is SpecimenStatus.REJECTED else specimen.rejection_reason,
        )
        self._specimens.save(updated)
        self._append_custody(
            specimen,
            from_status=specimen.status,
            to_status=target,
            actor_id=actor,
            reason=clean_reason,
        )
        event_payload: dict[str, object] = {
            "specimen_ref": specimen.specimen_id,
            "from_status": specimen.status.value,
            "to_status": target.value,
            "actor_id": actor,
            "reason": clean_reason,
        }
        if target is SpecimenStatus.COLLECTED:
            event_payload["collected_at"] = self._now()
        elif target is SpecimenStatus.RECEIVED:
            event_payload["received_at"] = self._now()
        self._emit(
            event_type=_SPECIMEN_EVENT_TYPES[target],
            aggregate_type=AggregateType.SPECIMEN,
            aggregate_id=specimen.specimen_id,
            tenant_id=specimen.tenant_id,
            payload=event_payload,
        )
        return updated

    @staticmethod
    def _coerce_enum(enum_type: type[SpecimenStatus], value: SpecimenStatus | str) -> SpecimenStatus:
        try:
            return enum_type(value)
        except ValueError as exc:
            raise LabWorkflowError(f"unknown specimen status: {value!r}") from exc

    # --------------------------------------------------------------- lab orders

    def place_order(
        self,
        *,
        tenant_id: str,
        patient_ref: str,
        test_codes: Sequence[str],
        idempotency_key: str,
        priority: Priority = Priority.ROUTINE,
        actor_id: str,
    ) -> LabOrder:
        """Place a synthetic order; identical key replay returns the original."""
        patient = self._resolve_patient(tenant_id, patient_ref)
        self._require_synthetic(idempotency_key, field="idempotency_key")
        self._require_actor(actor_id)
        codes: tuple[str, ...] = tuple(dict.fromkeys(code.strip().upper() for code in test_codes))
        if not codes:
            raise LabWorkflowError("an order must contain at least one test code")
        for code in codes:
            get_test_definition(code)
        normalized_priority = Priority(priority)

        existing = self._orders.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            if (
                existing.tenant_id == tenant_id
                and existing.patient == patient
                and existing.test_codes == codes
                and existing.priority is normalized_priority
            ):
                return existing
            raise DuplicateEntityError(
                "idempotency key already used for a different order",
                details={"idempotency_key": idempotency_key},
            )

        order = LabOrder(
            order_id=new_synthetic_id("ORD"),
            idempotency_key=idempotency_key,
            patient=patient,
            tenant_id=tenant_id,
            test_codes=codes,
            priority=normalized_priority,
            status=LabOrderStatus.PLACED,
            created_at=self._now(),
        )
        self._orders.save(order)
        self._emit(
            event_type=str(EventType.LAB_ORDER_PLACED),
            aggregate_type=AggregateType.LAB_ORDER,
            aggregate_id=order.order_id,
            tenant_id=tenant_id,
            payload={
                "order_ref": order.order_id,
                "patient_ref": patient.ref,
                "practitioner_ref": actor_id,
                "test_codes": list(codes),
                "priority": normalized_priority.value,
                "actor_id": actor_id,
            },
        )
        return order

    def cancel_order(
        self, *, tenant_id: str, order_id: str, reason: str, actor_id: str
    ) -> LabOrder:
        """Cancel a synthetic order; repeat cancellation is an idempotent no-op."""
        order = self._get_order(tenant_id, order_id)
        self._require_actor(actor_id)
        if order.status is LabOrderStatus.CANCELLED:
            return order
        if order.status is not LabOrderStatus.PLACED:
            raise InvalidStateTransitionError("only a placed order can be cancelled")
        clean_reason = reason.strip()
        if not clean_reason:
            raise LabWorkflowError("a cancellation reason is required")
        updated = replace(
            order,
            status=LabOrderStatus.CANCELLED,
            cancelled_at=self._now(),
            cancellation_reason=clean_reason,
        )
        self._orders.save(updated)
        self._emit(
            event_type=str(EventType.LAB_ORDER_CANCELLED),
            aggregate_type=AggregateType.LAB_ORDER,
            aggregate_id=order.order_id,
            tenant_id=tenant_id,
            payload={"reason": clean_reason, "actor_id": actor_id},
        )
        return updated

    def get_order(self, *, tenant_id: str, order_id: str) -> LabOrder:
        """Return a tenant-scoped synthetic order."""
        return self._get_order(tenant_id, order_id)

    def list_orders(self, *, tenant_id: str) -> tuple[LabOrder, ...]:
        """List all synthetic orders owned by one tenant."""
        self._require_synthetic(tenant_id, field="tenant_id")
        return self._orders.list_for_tenant(tenant_id)

    # --------------------------------------------------------------- specimens

    def register_specimen(
        self,
        *,
        tenant_id: str,
        order_id: str,
        barcode: str,
        actor_id: str,
    ) -> Specimen:
        """Register a synthetic specimen with a unique ``SYN-BAR-`` barcode."""
        order = self._get_order(tenant_id, order_id)
        self._require_actor(actor_id)
        if order.status is not LabOrderStatus.PLACED:
            raise InvalidStateTransitionError("cannot register a specimen on a cancelled order")
        patient = self._resolve_patient(tenant_id, order.patient.ref)
        self._require_barcode(barcode)

        existing = self._specimens.find_by_barcode(barcode)
        if existing is not None:
            if (
                existing.tenant_id == tenant_id
                and existing.order_id == order_id
                and existing.patient == patient
            ):
                return existing
            raise DuplicateEntityError(
                "synthetic barcode already registered for a different specimen",
                details={"barcode": barcode},
            )

        specimen = Specimen(
            specimen_id=new_synthetic_id("SPC"),
            barcode=barcode,
            order_id=order.order_id,
            tenant_id=tenant_id,
            patient=patient,
            status=SpecimenStatus.REGISTERED,
            registered_at=self._now(),
        )
        self._specimens.save(specimen)
        self._append_custody(
            specimen,
            from_status=None,
            to_status=SpecimenStatus.REGISTERED,
            actor_id=actor_id,
            reason=None,
        )
        self._emit(
            event_type=str(EventType.SPECIMEN_REGISTERED),
            aggregate_type=AggregateType.SPECIMEN,
            aggregate_id=specimen.specimen_id,
            tenant_id=tenant_id,
            payload={
                "specimen_ref": specimen.specimen_id,
                "order_ref": order.order_id,
                "barcode": barcode,
                "order_id": order.order_id,
                "actor_id": actor_id,
            },
        )
        return specimen

    def transition_specimen(
        self,
        *,
        tenant_id: str,
        specimen_id: str,
        to_status: SpecimenStatus | str,
        actor_id: str,
        reason: str | None = None,
    ) -> Specimen:
        """Apply one legal specimen lifecycle transition with custody evidence."""
        specimen = self._get_specimen(tenant_id, specimen_id)
        self._require_actor(actor_id)
        target = self._coerce_enum(SpecimenStatus, to_status)
        return self._transition_specimen(specimen, target, actor_id, reason)

    def get_specimen(self, *, tenant_id: str, specimen_id: str) -> Specimen:
        """Return a tenant-scoped synthetic specimen."""
        return self._get_specimen(tenant_id, specimen_id)

    def list_specimens(self, *, tenant_id: str) -> tuple[Specimen, ...]:
        """List all synthetic specimens owned by one tenant."""
        self._require_synthetic(tenant_id, field="tenant_id")
        return self._specimens.list_for_tenant(tenant_id)

    def custody_chain(self, *, tenant_id: str, specimen_id: str) -> tuple[CustodyEntry, ...]:
        """Return the immutable chain of custody for a tenant-owned specimen."""
        self._get_specimen(tenant_id, specimen_id)
        return self._custody.for_specimen(specimen_id, tenant_id=tenant_id)

    # ------------------------------------------------------------ test workflow

    def enter_testing(
        self, *, tenant_id: str, specimen_id: str, actor_id: str
    ) -> TestExecution:
        """Move a received specimen into synthetic testing (no analyzer call)."""
        specimen = self._get_specimen(tenant_id, specimen_id)
        self._require_actor(actor_id)
        if specimen.status is not SpecimenStatus.RECEIVED:
            raise InvalidStateTransitionError(
                "only a received specimen can enter testing",
                details={"status": specimen.status.value},
            )
        self._transition_specimen(specimen, SpecimenStatus.IN_TESTING, actor_id, None)
        execution = TestExecution(
            execution_id=new_synthetic_id("EXE"),
            specimen_id=specimen.specimen_id,
            order_id=specimen.order_id,
            tenant_id=tenant_id,
            status=TestExecutionStatus.ENTERED,
            entered_at=self._now(),
            actor_id=actor_id,
        )
        self._executions.save(execution)
        self._emit(
            event_type=TEST_ENTERED_EVENT,
            aggregate_type=AggregateType.SPECIMEN,
            aggregate_id=specimen.specimen_id,
            tenant_id=tenant_id,
            payload={
                "execution_ref": execution.execution_id,
                "specimen_ref": specimen.specimen_id,
                "execution_id": execution.execution_id,
                "actor_id": actor_id,
            },
        )
        return execution

    def complete_testing(
        self, *, tenant_id: str, execution_id: str, actor_id: str
    ) -> TestExecution:
        """Complete a synthetic testing session and finalise its specimen."""
        execution = self._get_execution(tenant_id, execution_id)
        self._require_actor(actor_id)
        if execution.status is TestExecutionStatus.COMPLETED:
            return execution
        if execution.status is not TestExecutionStatus.ENTERED:
            raise InvalidStateTransitionError("only an entered execution can be completed")
        specimen = self._get_specimen(tenant_id, execution.specimen_id)
        self._transition_specimen(specimen, SpecimenStatus.FINAL, actor_id, None)
        updated = replace(
            execution,
            status=TestExecutionStatus.COMPLETED,
            completed_at=self._now(),
        )
        self._executions.save(updated)
        self._emit(
            event_type=TEST_COMPLETED_EVENT,
            aggregate_type=AggregateType.SPECIMEN,
            aggregate_id=specimen.specimen_id,
            tenant_id=tenant_id,
            payload={
                "execution_ref": updated.execution_id,
                "specimen_ref": specimen.specimen_id,
                "execution_id": execution.execution_id,
                "actor_id": actor_id,
            },
        )
        return updated

    # ------------------------------------------------------------------ results

    def record_result(
        self,
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
        """Record a synthetic result; identical key replay returns the original."""
        order = self._get_order(tenant_id, order_id)
        specimen = self._get_specimen(tenant_id, specimen_id)
        if specimen.order_id != order.order_id:
            raise LabWorkflowError("specimen does not belong to the given order")
        if specimen.status in {
            SpecimenStatus.REGISTERED,
            SpecimenStatus.COLLECTED,
            SpecimenStatus.REJECTED,
        }:
            raise InvalidStateTransitionError(
                "results require a received, testing or final specimen",
                details={"status": specimen.status.value},
            )
        patient = self._resolve_patient(tenant_id, patient_ref)
        if patient != order.patient or patient != specimen.patient:
            raise LabWorkflowError("patient reference does not match the order and specimen")
        self._require_synthetic(idempotency_key, field="idempotency_key")
        self._require_actor(actor_id)
        if not math.isfinite(value):
            raise InvalidResultError("result value must be finite")
        definition = get_test_definition(test_code)
        if definition.code not in order.test_codes:
            raise LabWorkflowError("test code was not ordered", details={"test_code": definition.code})
        normalized_unit = unit.strip()
        if normalized_unit != definition.unit:
            raise InvalidResultError(
                "unit does not match the synthetic test definition",
                details={"expected": definition.unit, "received": normalized_unit},
            )

        existing = self._results.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            if (
                existing.tenant_id == tenant_id
                and existing.patient == patient
                and existing.order_id == order_id
                and existing.specimen_id == specimen_id
                and existing.test_code == definition.code
                and existing.value == value
                and existing.unit == normalized_unit
            ):
                return existing
            raise DuplicateEntityError(
                "idempotency key already used for a different result",
                details={"idempotency_key": idempotency_key},
            )

        critical = self._critical_flag(definition, value)
        result = LabResult(
            result_id=new_synthetic_id("RES"),
            idempotency_key=idempotency_key,
            order_id=order.order_id,
            specimen_id=specimen.specimen_id,
            patient=patient,
            tenant_id=tenant_id,
            test_code=definition.code,
            value=value,
            unit=normalized_unit,
            reference_low=definition.reference_low,
            reference_high=definition.reference_high,
            critical_flag=critical,
            recorded_at=self._now(),
        )
        self._results.save(result)
        self._emit(
            event_type=str(EventType.RESULT_RECORDED),
            aggregate_type=AggregateType.LAB_RESULT,
            aggregate_id=result.result_id,
            tenant_id=tenant_id,
            payload={
                "result_ref": result.result_id,
                "order_ref": order.order_id,
                "specimen_ref": specimen.specimen_id,
                "test_code": definition.code,
                "value": value,
                "unit": normalized_unit,
                "critical_flag": critical,
                "actor_id": actor_id,
            },
        )
        return result

    def correct_result(
        self,
        *,
        tenant_id: str,
        result_id: str,
        new_value: float,
        reason: str,
        actor_id: str,
    ) -> LabResult:
        """Amend a synthetic result, preserving an immutable correction history."""
        result = self._get_result(tenant_id, result_id)
        self._require_actor(actor_id)
        clean_reason = reason.strip()
        if not clean_reason:
            raise LabWorkflowError("a correction reason is required")
        if not math.isfinite(new_value):
            raise InvalidResultError("corrected value must be finite")
        definition = get_test_definition(result.test_code)
        amendment = ResultAmendment(
            amendment_id=new_synthetic_id("AMD"),
            result_id=result.result_id,
            tenant_id=tenant_id,
            previous_value=result.value,
            new_value=new_value,
            reason=clean_reason,
            actor_id=actor_id,
            occurred_at=self._now(),
            version=result.version + 1,
        )
        updated = replace(
            result,
            value=new_value,
            version=result.version + 1,
            critical_flag=self._critical_flag(definition, new_value),
            amendments=(*result.amendments, amendment),
        )
        self._results.save(updated)
        self._emit(
            event_type=str(EventType.RESULT_CORRECTED),
            aggregate_type=AggregateType.LAB_RESULT,
            aggregate_id=result.result_id,
            tenant_id=tenant_id,
            payload={
                "result_ref": result.result_id,
                "previous_value": result.value,
                "new_value": new_value,
                "version": updated.version,
                "reason": clean_reason,
                "actor_id": actor_id,
            },
        )
        return updated

    def get_result(self, *, tenant_id: str, result_id: str) -> LabResult:
        """Return a tenant-scoped synthetic result."""
        return self._get_result(tenant_id, result_id)

    def list_results(self, *, tenant_id: str) -> tuple[LabResult, ...]:
        """List all synthetic results owned by one tenant."""
        self._require_synthetic(tenant_id, field="tenant_id")
        return self._results.list_for_tenant(tenant_id)

    # -------------------------------------------------------------- verification

    def verify_result(
        self,
        *,
        tenant_id: str,
        result_id: str,
        reviewer_id: str,
        decision: VerificationDecision | str,
        idempotency_key: str,
        reason: str | None = None,
    ) -> Verification:
        """Verify or reject a synthetic result with a synthetic reviewer id."""
        result = self._get_result(tenant_id, result_id)
        self._require_actor(reviewer_id, field="reviewer_id")
        self._require_synthetic(idempotency_key, field="idempotency_key")
        try:
            target_decision = VerificationDecision(decision)
        except ValueError as exc:
            raise LabWorkflowError(f"unknown verification decision: {decision!r}") from exc

        existing = self._verifications.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            if (
                existing.tenant_id == tenant_id
                and existing.result_id == result.result_id
                and existing.reviewer_id == reviewer_id
                and existing.decision is target_decision
                and existing.reason == reason
            ):
                return existing
            raise DuplicateEntityError(
                "idempotency key already used for a different verification",
                details={"idempotency_key": idempotency_key},
            )

        verification = Verification(
            verification_id=new_synthetic_id("VER"),
            result_id=result.result_id,
            tenant_id=tenant_id,
            reviewer_id=reviewer_id,
            decision=target_decision,
            status=VerificationStatus.PENDING,
            idempotency_key=idempotency_key,
            created_at=self._now(),
            reason=reason,
        )
        self._verifications.save(verification)
        self._emit(
            event_type=VERIFICATION_PENDING_EVENT,
            aggregate_type=AggregateType.VERIFICATION,
            aggregate_id=verification.verification_id,
            tenant_id=tenant_id,
            payload={
                "result_ref": result.result_id,
                "verifier_ref": reviewer_id,
                "result_id": result.result_id,
                "reviewer_id": reviewer_id,
            },
        )
        target_status = (
            VerificationStatus.VERIFIED
            if target_decision is VerificationDecision.VERIFIED
            else VerificationStatus.REJECTED
        )
        return self.transition_verification(
            tenant_id=tenant_id,
            verification_id=verification.verification_id,
            to_status=target_status,
            reviewer_id=reviewer_id,
            reason=reason,
        )

    def transition_verification(
        self,
        *,
        tenant_id: str,
        verification_id: str,
        to_status: VerificationStatus | str,
        reviewer_id: str,
        reason: str | None = None,
    ) -> Verification:
        """Apply one legal verification lifecycle transition."""
        verification = self._get_verification(tenant_id, verification_id)
        self._require_actor(reviewer_id, field="reviewer_id")
        if verification.reviewer_id != reviewer_id:
            raise LabWorkflowError("only the assigned synthetic reviewer may transition")
        try:
            target = VerificationStatus(to_status)
        except ValueError as exc:
            raise LabWorkflowError(f"unknown verification status: {to_status!r}") from exc
        allowed = LEGAL_VERIFICATION_TRANSITIONS.get(verification.status, frozenset())
        if target not in allowed:
            raise InvalidStateTransitionError(
                f"illegal verification transition "
                f"{verification.status.value} -> {target.value}"
            )
        clean_reason = reason.strip() if reason and reason.strip() else None
        if target is VerificationStatus.REJECTED and clean_reason is None:
            raise LabWorkflowError("a rejection reason is required")
        updated = replace(
            verification,
            status=target,
            reason=clean_reason if clean_reason is not None else verification.reason,
        )
        self._verifications.save(updated)
        event_type = (
            str(EventType.RESULT_VERIFIED)
            if target is VerificationStatus.VERIFIED
            else RESULT_VERIFICATION_REJECTED_EVENT
        )
        self._emit(
            event_type=event_type,
            aggregate_type=AggregateType.VERIFICATION,
            aggregate_id=verification.verification_id,
            tenant_id=tenant_id,
            payload={
                "result_ref": verification.result_id,
                "verifier_ref": reviewer_id,
                "from_status": verification.status.value,
                "to_status": target.value,
                "result_id": verification.result_id,
                "reviewer_id": reviewer_id,
                "reason": clean_reason,
            },
        )
        return updated

    def get_verification(self, *, tenant_id: str, verification_id: str) -> Verification:
        """Return a tenant-scoped synthetic verification."""
        return self._get_verification(tenant_id, verification_id)

    def verification_for_result(
        self, *, tenant_id: str, result_id: str
    ) -> Verification | None:
        """Return the verification for a tenant-owned result, if one exists."""
        self._get_result(tenant_id, result_id)
        verification = self._verifications.for_result(result_id)
        if verification is not None and verification.tenant_id != tenant_id:
            raise TenantMismatchError(
                "synthetic verification belongs to another tenant",
                details={"result_id": result_id, "tenant_id": tenant_id},
            )
        return verification

    # --------------------------------------------------------------- provenance

    def provenance(self, *, tenant_id: str, aggregate_id: str) -> tuple[DomainEvent, ...]:
        """Return the immutable, insertion-ordered event trail for one aggregate."""
        self._require_synthetic(tenant_id, field="tenant_id")
        events = self._events.events_for(aggregate_id)
        if events and events[0].tenant_id != tenant_id:
            raise TenantMismatchError(
                "event trail belongs to another tenant",
                details={"aggregate_id": aggregate_id, "tenant_id": tenant_id},
            )
        return events

    def all_events(self, *, tenant_id: str) -> tuple[DomainEvent, ...]:
        """Return the immutable event trail for one synthetic tenant."""
        self._require_synthetic(tenant_id, field="tenant_id")
        return self._events.events_for_tenant(tenant_id)
