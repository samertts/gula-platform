"""Wave 05.3 reversible registration idempotency and reservation helpers.

This module does not add a database column, migration, DDL, trigger, or route.
It wraps the existing Wave 05.2 GULA Citizen Identifier generator with an
atomic in-memory idempotency store so that duplicate submissions cannot create
a second registration file. A real implementation must replace this store with
a transactional database adapter backed by UNIQUE constraints; that step is
PROPOSED and PENDING SCHEMA OWNER APPROVAL.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app._compat import UTC
from app.national.exceptions import (
    GulaCitizenIdentifierCollisionError,
    GulaCitizenIdentifierExhaustedError,
)
from app.national.services.citizen_service import generate_gula_citizen_identifier


class RegistrationCoordinatorError(ValueError):
    """Base error for registration idempotency violations."""


class RegistrationInProgressError(RegistrationCoordinatorError):
    """Raised when a duplicate request arrives while the first is pending."""


class RegistrationState(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_NUMERIC_REFERENCE = re.compile(r"^\d{9,14}$")


@dataclass(frozen=True)
class RegistrationRequest:
    """Idempotent registration request carrying no raw national number."""

    idempotency_key: str
    subject_reference: str
    birth_year: int
    requested_at: datetime

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip():
            raise RegistrationCoordinatorError("idempotency key is required")
        if not self.subject_reference.strip():
            raise RegistrationCoordinatorError("subject reference is required")
        if _NUMERIC_REFERENCE.fullmatch(self.subject_reference):
            raise RegistrationCoordinatorError(
                "subject reference must not be a raw national number",
            )
        if not 1000 <= self.birth_year <= 9999:
            raise RegistrationCoordinatorError("birth_year must be four digits")


@dataclass(frozen=True)
class RegistrationRecord:
    request: RegistrationRequest
    state: RegistrationState
    reserved_identifier: str | None = None
    failure_reason: str | None = None
    updated_at: datetime | None = None


class IdempotencyStore(Protocol):
    """Atomic store contract required by a future approved persistence layer."""

    def reserve(
        self,
        request: RegistrationRequest,
        *,
        at: datetime,
    ) -> tuple[RegistrationRecord, bool]: ...

    def reserve_identifier(self, identifier: str) -> bool: ...

    def complete(
        self,
        idempotency_key: str,
        identifier: str,
        *,
        at: datetime,
    ) -> RegistrationRecord: ...

    def fail(
        self,
        idempotency_key: str,
        reason: str,
        *,
        at: datetime,
    ) -> RegistrationRecord: ...

    def release_identifier(self, identifier: str, *, at: datetime) -> None: ...

    def records(self) -> tuple[RegistrationRecord, ...]: ...


class InMemoryIdempotencyStore:
    """Synthetic-only atomic store using a process lock, not a second database."""

    def __init__(self, *, collisions: frozenset[str] = frozenset()) -> None:
        self._records: dict[str, RegistrationRecord] = {}
        self._identifiers: set[str] = set()
        self._collisions = set(collisions)
        self._lock = threading.Lock()

    def reserve(
        self,
        request: RegistrationRequest,
        *,
        at: datetime,
    ) -> tuple[RegistrationRecord, bool]:
        with self._lock:
            existing = self._records.get(request.idempotency_key)
            if existing is not None:
                return existing, False
            record = RegistrationRecord(request=request, state=RegistrationState.PENDING, updated_at=at)
            self._records[request.idempotency_key] = record
            return record, True

    def reserve_identifier(self, identifier: str) -> bool:
        with self._lock:
            if identifier in self._identifiers or identifier in self._collisions:
                raise GulaCitizenIdentifierCollisionError(identifier)
            self._identifiers.add(identifier)
            return True

    def complete(
        self,
        idempotency_key: str,
        identifier: str,
        *,
        at: datetime,
    ) -> RegistrationRecord:
        with self._lock:
            existing = self._records.get(idempotency_key)
            if existing is None:
                raise RegistrationCoordinatorError("registration idempotency key is unknown")
            if existing.state is RegistrationState.COMPLETED:
                if existing.reserved_identifier != identifier:
                    raise RegistrationCoordinatorError("completed registration identifier changed")
                return existing
            completed = RegistrationRecord(
                request=existing.request,
                state=RegistrationState.COMPLETED,
                reserved_identifier=identifier,
                updated_at=at,
            )
            self._records[idempotency_key] = completed
            return completed

    def fail(
        self,
        idempotency_key: str,
        reason: str,
        *,
        at: datetime,
    ) -> RegistrationRecord:
        with self._lock:
            existing = self._records.get(idempotency_key)
            if existing is None:
                raise RegistrationCoordinatorError("registration idempotency key is unknown")
            if existing.state is RegistrationState.COMPLETED:
                raise RegistrationCoordinatorError("completed registration cannot be failed")
            failed = RegistrationRecord(
                request=existing.request,
                state=RegistrationState.FAILED,
                reserved_identifier=existing.reserved_identifier,
                failure_reason=reason[:500],
                updated_at=at,
            )
            self._records[idempotency_key] = failed
            return failed

    def release_identifier(self, identifier: str, *, at: datetime) -> None:
        del at
        with self._lock:
            self._identifiers.discard(identifier)

    def records(self) -> tuple[RegistrationRecord, ...]:
        with self._lock:
            return tuple(self._records.values())


def register_citizen_idempotently(
    request: RegistrationRequest,
    *,
    store: IdempotencyStore,
    random_source: Callable[[], int] | None = None,
    max_attempts: int = 10,
    after_reservation: Callable[[str], None] | None = None,
    now: datetime | None = None,
) -> RegistrationRecord:
    """Generate and reserve one immutable identifier per idempotency key.

    A duplicate request returns the already stored record and never invokes the
    generator again. Any failure after a candidate was reserved releases the
    reservation and marks only that idempotency key as FAILED.
    """
    at = now or datetime.now(UTC)
    existing, created = store.reserve(request, at=at)
    if not created:
        if existing.state is RegistrationState.PENDING:
            raise RegistrationInProgressError("registration is already in progress")
        return existing

    identifier: str | None = None
    try:
        identifier = generate_gula_citizen_identifier(
            birth_year=request.birth_year,
            reserve=store.reserve_identifier,
            random_source=random_source,
            max_attempts=max_attempts,
        )
        if after_reservation is not None:
            after_reservation(identifier)
        return store.complete(request.idempotency_key, identifier, at=at)
    except Exception as exc:
        if identifier is not None:
            store.release_identifier(identifier, at=at)
        store.fail(request.idempotency_key, f"{type(exc).__name__}: {exc}", at=at)
        raise


def assert_single_completed_registration(
    records: Iterable[RegistrationRecord],
    subject_reference: str,
) -> RegistrationRecord:
    """Fail if idempotency leaked into more than one completed citizen file."""
    matches = [
        record
        for record in records
        if record.state is RegistrationState.COMPLETED
        and record.request.subject_reference == subject_reference
    ]
    if len(matches) != 1:
        raise RegistrationCoordinatorError(
            f"expected one completed registration for subject reference, found {len(matches)}",
        )
    return matches[0]


__all__ = [
    "GulaCitizenIdentifierCollisionError",
    "GulaCitizenIdentifierExhaustedError",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "RegistrationCoordinatorError",
    "RegistrationInProgressError",
    "RegistrationRecord",
    "RegistrationRequest",
    "RegistrationState",
    "assert_single_completed_registration",
    "register_citizen_idempotently",
]
