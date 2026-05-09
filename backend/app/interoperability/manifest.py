"""Manifest validation helpers.

A ``TrustDomain`` instance is the in-memory manifest. This module provides
lightweight invariant checks. It does NOT load YAML; the manifest format
is documented in the governance docs but the loader is deliberately left
to the future, explicitly-approved wiring phase.

See ``docs/sovereign/phase16-interoperability/02-adapter-framework.md``
("Manifest Validation").
"""

from __future__ import annotations

from .trust_domain import FailureMode, TenancyMode, TrustDomain


class ManifestError(ValueError):
    """Raised when a manifest fails the static invariant checks."""


def validate_manifest(domain: TrustDomain) -> None:
    """Validate a ``TrustDomain`` against the static manifest invariants.

    The checks here are intentionally minimal and stable. Richer checks
    (cross-adapter uniqueness, audit-topic registry membership) belong to
    the registry layer in a future wiring phase.
    """
    if not domain.domain_id:
        raise ManifestError("domain_id is required")
    if not domain.name:
        raise ManifestError("name is required")
    if not domain.allowed_operations:
        raise ManifestError("allowed_operations cannot be empty")
    for op in domain.allowed_operations:
        if not isinstance(op, str) or not op:
            raise ManifestError("allowed_operations must be non-empty strings")
    if domain.failure_policy.mode is not FailureMode.FAIL_CLOSED:
        raise ManifestError(
            "failure_policy.mode must be fail_closed for sovereign adapters"
        )
    if domain.failure_policy.max_retries < 0:
        raise ManifestError("failure_policy.max_retries must be >= 0")
    if domain.failure_policy.circuit_open_threshold_failures < 1:
        raise ManifestError(
            "failure_policy.circuit_open_threshold_failures must be >= 1"
        )
    if domain.tenancy_mode is TenancyMode.NATIONAL_AGGREGATOR:
        # National aggregators must NOT carry inbound patient-class data;
        # they receive de-identified flows only.
        forbidden = {"patient", "national_id", "phone", "free_text_note"}
        leakage = forbidden & set(domain.data_classes_in)
        if leakage:
            raise ManifestError(
                "national_aggregator must not declare data_classes_in: "
                + ", ".join(sorted(leakage))
            )
    if domain.require_jwe_for_classes - domain.data_classes_in - domain.data_classes_out:
        raise ManifestError(
            "require_jwe_for_classes must reference declared data classes"
        )
