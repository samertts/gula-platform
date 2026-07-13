"""Abstract adapter contract for institutional interoperability.

Every institutional integration MUST extend ``AdapterBase``. The base
contract is intentionally narrow: capability check, audit emission,
failure isolation, no inheritance of user privileges.

See ``docs/sovereign/phase16-interoperability/02-adapter-framework.md``.
"""

from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum

from .audit_event import InteropAuditEvent
from .principal import InteropPrincipal
from .trust_domain import TrustDomain


class AdapterStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class AdapterHealth:
    status: AdapterStatus
    detail: str = ""


@dataclass(frozen=True)
class AdapterContext:
    """Per-call context carried through an adapter invocation."""

    principal: InteropPrincipal
    request_id: str
    operation: str
    lab_id: str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterResult:
    """Result of an adapter invocation.

    ``ok`` is True for successful invocations. Failures (denials, circuit
    open, peer 5xx, replay rejections) MUST set ``ok=False`` and provide
    an ``error_class`` from the documented enumeration. Bodies are
    intentionally NOT logged at audit time; their hashes are.
    """

    ok: bool
    payload: Mapping[str, Any] | None = None
    error_class: str | None = None
    audit_event: InteropAuditEvent | None = None


class CapabilityDenied(PermissionError):
    """Raised when an adapter call is not authorised by the manifest."""


class AdapterUnavailable(RuntimeError):
    """Raised when an adapter is unavailable (circuit open, peer down)."""


class AdapterBase(abc.ABC):
    """Abstract institutional adapter base class.

    Subclasses are leaves of the dependency graph. They MUST NOT import
    from ``backend/app/routes/`` and MUST NOT obtain user-bearing
    principals; they receive an ``InteropPrincipal`` synthesised from
    their ``TrustDomain``.
    """

    name: str
    domain: TrustDomain

    def __init__(self, *, name: str, domain: TrustDomain) -> None:
        if not name:
            raise ValueError("adapter name is required")
        self.name = name
        self.domain = domain

    # ---- Capability check ------------------------------------------------

    def check_capability(self, operation: str) -> None:
        """Raise ``CapabilityDenied`` if ``operation`` is not in the manifest."""
        if not self.domain.permits(operation):
            raise CapabilityDenied(f"adapter {self.name!r} not permitted to perform {operation!r}")

    # ---- Lifecycle / health ---------------------------------------------

    @abc.abstractmethod
    async def health(self) -> AdapterHealth:
        """Return current adapter health (no side effects beyond probe)."""

    # ---- Outbound -------------------------------------------------------

    @abc.abstractmethod
    async def call_outbound(
        self,
        operation: str,
        payload: Mapping[str, Any],
        context: AdapterContext,
    ) -> AdapterResult:
        """Perform an outbound call to the peer institution.

        Implementations MUST:
            1. Call ``self.check_capability(operation)`` first.
            2. Emit an ``InteropAuditEvent`` regardless of outcome.
            3. Honor the failure policy declared in ``self.domain``.
        """

    # ---- Inbound --------------------------------------------------------

    @abc.abstractmethod
    async def handle_inbound(
        self,
        operation: str,
        payload: Mapping[str, Any],
        context: AdapterContext,
    ) -> AdapterResult:
        """Handle an inbound call from the peer institution.

        Same MUST list as ``call_outbound``.
        """

    # ---- Outbox replay --------------------------------------------------

    @abc.abstractmethod
    async def replay_outbox(self) -> int:
        """Drain the adapter's outbox; return the number of events replayed."""
