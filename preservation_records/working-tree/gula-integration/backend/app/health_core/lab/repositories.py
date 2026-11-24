"""Process-local in-memory repositories for the synthetic lab workflow.

No repository touches a database, network, filesystem or durable store. Every
query that crosses a tenant boundary is explicitly tenant-scoped, and all
returned collections are immutable tuples so callers cannot mutate stored state.
"""

from __future__ import annotations

from app.health_core.common.events import DomainEvent
from app.health_core.lab.models import (
    CustodyEntry,
    LabOrder,
    LabResult,
    Specimen,
    TestExecution,
    Verification,
)


class InMemoryLabOrderRepository:
    """Stores synthetic lab orders and their idempotency index."""

    def __init__(self) -> None:
        self._orders: dict[str, LabOrder] = {}
        self._by_key: dict[str, str] = {}

    def save(self, order: LabOrder) -> None:
        """Insert or replace a synthetic order."""
        self._orders[order.order_id] = order
        self._by_key[order.idempotency_key] = order.order_id

    def get(self, order_id: str) -> LabOrder | None:
        """Return an order by its synthetic id, or ``None``."""
        return self._orders.get(order_id)

    def find_by_idempotency_key(self, key: str) -> LabOrder | None:
        """Return the original order for a replayed key, or ``None``."""
        order_id = self._by_key.get(key)
        return self._orders.get(order_id) if order_id is not None else None

    def list_for_tenant(self, tenant_id: str) -> tuple[LabOrder, ...]:
        """Return all orders owned by one synthetic tenant."""
        return tuple(order for order in self._orders.values() if order.tenant_id == tenant_id)


class InMemorySpecimenRepository:
    """Stores synthetic specimens with a unique-barcode index."""

    def __init__(self) -> None:
        self._specimens: dict[str, Specimen] = {}
        self._by_barcode: dict[str, str] = {}

    def save(self, specimen: Specimen) -> None:
        """Insert or replace a synthetic specimen."""
        self._specimens[specimen.specimen_id] = specimen
        self._by_barcode[specimen.barcode] = specimen.specimen_id

    def get(self, specimen_id: str) -> Specimen | None:
        """Return a specimen by its synthetic id, or ``None``."""
        return self._specimens.get(specimen_id)

    def find_by_barcode(self, barcode: str) -> Specimen | None:
        """Return the specimen carrying a barcode, or ``None``."""
        specimen_id = self._by_barcode.get(barcode)
        return self._specimens.get(specimen_id) if specimen_id is not None else None

    def list_for_tenant(self, tenant_id: str) -> tuple[Specimen, ...]:
        """Return all specimens owned by one synthetic tenant."""
        return tuple(item for item in self._specimens.values() if item.tenant_id == tenant_id)

    def list_for_order(self, order_id: str, *, tenant_id: str) -> tuple[Specimen, ...]:
        """Return specimens for an order, restricted to one tenant."""
        return tuple(
            item
            for item in self._specimens.values()
            if item.order_id == order_id and item.tenant_id == tenant_id
        )


class InMemoryCustodyRepository:
    """Append-only chain-of-custody records for synthetic specimens."""

    def __init__(self) -> None:
        self._entries: list[CustodyEntry] = []

    def append(self, entry: CustodyEntry) -> None:
        """Append one immutable custody record."""
        self._entries.append(entry)

    def for_specimen(self, specimen_id: str, *, tenant_id: str) -> tuple[CustodyEntry, ...]:
        """Return the ordered custody chain for a specimen within a tenant."""
        return tuple(
            entry
            for entry in self._entries
            if entry.specimen_id == specimen_id and entry.tenant_id == tenant_id
        )


class InMemoryTestExecutionRepository:
    """Stores synthetic testing sessions (no analyzer interaction)."""

    def __init__(self) -> None:
        self._executions: dict[str, TestExecution] = {}

    def save(self, execution: TestExecution) -> None:
        """Insert or replace a synthetic execution record."""
        self._executions[execution.execution_id] = execution

    def get(self, execution_id: str) -> TestExecution | None:
        """Return an execution record, or ``None``."""
        return self._executions.get(execution_id)

    def list_for_tenant(self, tenant_id: str) -> tuple[TestExecution, ...]:
        """Return all execution records owned by one synthetic tenant."""
        return tuple(
            execution
            for execution in self._executions.values()
            if execution.tenant_id == tenant_id
        )


class InMemoryResultRepository:
    """Stores synthetic lab results and their idempotency index."""

    def __init__(self) -> None:
        self._results: dict[str, LabResult] = {}
        self._by_key: dict[str, str] = {}

    def save(self, result: LabResult) -> None:
        """Insert or replace a synthetic result."""
        self._results[result.result_id] = result
        self._by_key[result.idempotency_key] = result.result_id

    def get(self, result_id: str) -> LabResult | None:
        """Return a result by its synthetic id, or ``None``."""
        return self._results.get(result_id)

    def find_by_idempotency_key(self, key: str) -> LabResult | None:
        """Return the original result for a replayed key, or ``None``."""
        result_id = self._by_key.get(key)
        return self._results.get(result_id) if result_id is not None else None

    def list_for_tenant(self, tenant_id: str) -> tuple[LabResult, ...]:
        """Return all results owned by one synthetic tenant."""
        return tuple(result for result in self._results.values() if result.tenant_id == tenant_id)

    def list_for_order(self, order_id: str, *, tenant_id: str) -> tuple[LabResult, ...]:
        """Return results for an order, restricted to one tenant."""
        return tuple(
            result
            for result in self._results.values()
            if result.order_id == order_id and result.tenant_id == tenant_id
        )


class InMemoryVerificationRepository:
    """Stores synthetic verification decisions and their idempotency index."""

    def __init__(self) -> None:
        self._verifications: dict[str, Verification] = {}
        self._by_key: dict[str, str] = {}
        self._by_result: dict[str, str] = {}

    def save(self, verification: Verification) -> None:
        """Insert or replace a synthetic verification."""
        self._verifications[verification.verification_id] = verification
        self._by_key[verification.idempotency_key] = verification.verification_id
        self._by_result[verification.result_id] = verification.verification_id

    def get(self, verification_id: str) -> Verification | None:
        """Return a verification by id, or ``None``."""
        return self._verifications.get(verification_id)

    def find_by_idempotency_key(self, key: str) -> Verification | None:
        """Return the original verification for a replayed key, or ``None``."""
        verification_id = self._by_key.get(key)
        return (
            self._verifications.get(verification_id) if verification_id is not None else None
        )

    def for_result(self, result_id: str) -> Verification | None:
        """Return the verification associated with one synthetic result."""
        verification_id = self._by_result.get(result_id)
        return (
            self._verifications.get(verification_id) if verification_id is not None else None
        )

    def list_for_tenant(self, tenant_id: str) -> tuple[Verification, ...]:
        """Return all verifications owned by one synthetic tenant."""
        return tuple(
            item for item in self._verifications.values() if item.tenant_id == tenant_id
        )


class InMemoryEventStore:
    """Append-only, immutable event log used as the provenance trail."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        """Append one immutable domain event."""
        self._events.append(event)

    def all_events(self) -> tuple[DomainEvent, ...]:
        """Return every recorded event in insertion order."""
        return tuple(self._events)

    def events_for(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        """Return the ordered trail for one aggregate."""
        return tuple(event for event in self._events if event.aggregate_id == aggregate_id)

    def events_for_tenant(self, tenant_id: str) -> tuple[DomainEvent, ...]:
        """Return the ordered trail for one synthetic tenant."""
        return tuple(event for event in self._events if event.tenant_id == tenant_id)
