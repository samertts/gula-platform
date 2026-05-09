"""Synthetic principal carried by adapter calls.

An ``InteropPrincipal`` is the only authority an adapter can speak as. It
is NEVER assignable to a human ``lab_user``; assignment from a real user
context must raise.

See ``docs/sovereign/phase16-interoperability/07-rbac-extensions.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InteropRole(str, Enum):
    READER = "INTEROP_READER"
    WRITER_LIMITED = "INTEROP_WRITER_LIMITED"
    REGULATOR_READ = "INTEROP_REGULATOR_READ"
    AGGREGATOR_DEID = "INTEROP_AGGREGATOR_DEID"


@dataclass(frozen=True)
class InteropPrincipal:
    """Principal scoped to a single adapter invocation.

    ``lab_id`` is required for any operation whose data class includes
    patient data. National-aggregator domains may set ``lab_id=None`` only
    on de-identified flows; the adapter is responsible for that
    correctness check.
    """

    domain_id: str
    peer_subject: str
    role: InteropRole
    permissions: frozenset[str]
    operation: str
    lab_id: str | None = None
    request_id: str | None = None

    @property
    def subject(self) -> str:
        return f"interop:{self.domain_id}:{self.peer_subject}"

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions
