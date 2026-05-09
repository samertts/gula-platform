"""Bounded trust-domain dataclasses for institutional adapters.

A ``TrustDomain`` is the immutable manifest binding that authorises an
adapter to perform a specific, narrow set of operations on behalf of a
peer institution. It is the single source of truth for what an adapter
may do; runtime code paths must never widen the binding.

See ``docs/sovereign/phase16-interoperability/02-adapter-framework.md``
and ``03-trust-boundaries.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InstitutionType(str, Enum):
    MINISTRY = "ministry"
    INSURER = "insurer"
    HOSPITAL = "hospital"
    LAB = "lab"
    TELCO = "telco"
    PAYMENT = "payment"
    STATISTICS = "statistics"
    NHOP = "nhop"
    PROVINCIAL = "provincial"
    EDGE = "edge"


class TenancyMode(str, Enum):
    SINGLE_TENANT_PROXY = "single_tenant_proxy"
    MULTI_TENANT_AGGREGATOR = "multi_tenant_aggregator"
    NATIONAL_AGGREGATOR = "national_aggregator"


class FailureMode(str, Enum):
    FAIL_CLOSED = "fail_closed"


@dataclass(frozen=True)
class FailurePolicy:
    """Per-adapter failure policy. Only ``fail_closed`` is supported."""

    mode: FailureMode = FailureMode.FAIL_CLOSED
    max_retries: int = 5
    backoff_initial_ms: int = 200
    backoff_max_ms: int = 30_000
    circuit_open_threshold_failures: int = 5
    circuit_half_open_after_s: int = 60


@dataclass(frozen=True)
class TrustDomain:
    """Immutable institutional trust-domain manifest.

    A trust domain is the *only* authority binding for an adapter. Code
    paths that contradict the manifest are defects.
    """

    domain_id: str
    name: str
    institution_type: InstitutionType
    tenancy_mode: TenancyMode
    allowed_operations: frozenset[str]
    data_classes_in: frozenset[str] = field(default_factory=frozenset)
    data_classes_out: frozenset[str] = field(default_factory=frozenset)
    audit_topic: str = ""
    failure_policy: FailurePolicy = field(default_factory=FailurePolicy)
    require_jws: bool = True
    require_jwe_for_classes: frozenset[str] = field(default_factory=frozenset)

    def permits(self, operation: str) -> bool:
        """Capability whitelist check. Returns True iff operation is allowed."""
        return operation in self.allowed_operations

    def permits_data_in(self, data_class: str) -> bool:
        return data_class in self.data_classes_in

    def permits_data_out(self, data_class: str) -> bool:
        return data_class in self.data_classes_out
