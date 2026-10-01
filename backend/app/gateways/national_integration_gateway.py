"""Synthetic-only national integration gateway.

This module is deliberately non-production for external connectivity. It provides
an adapter-shaped boundary for contract and UX testing without sending PHI,
financial instructions, or clinical truth to a provider. Any attempt to use a
live/shadow mode is rejected before a network call can be made.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

from app.gateways.base import (
    DataTrustLevel,
    ExternalDataResult,
    ExternalGateway,
    FieldRule,
    ValidationError,
    validate_schema,
)
from app.gateways.mode import AdapterMode, resolve_mode

logger = logging.getLogger("gula.gateways.national_integration")


class SyntheticOnlyViolation(RuntimeError):
    """Raised when an external operation would cross the synthetic-only boundary."""


@dataclass(frozen=True)
class IntegrationReceipt:
    idempotency_key: str
    request_digest: str
    operation: str
    status: str
    result: dict[str, Any]


class SyntheticNationalProvider:
    """Deterministic provider used for demo, CI, and contract tests only."""

    _ALLOWED_OPERATIONS = frozenset({"identity.verify", "facility.lookup", "eligibility.check"})

    def execute(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation not in self._ALLOWED_OPERATIONS:
            raise ValidationError(f"unsupported synthetic operation: {operation}")
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        ).hexdigest()[:16]
        return {
            "provider": "synthetic-national-provider",
            "operation": operation,
            "reference": f"SYN-{digest}",
            "status": "ACCEPTED",
            "synthetic": True,
        }


class NationalIntegrationGateway(ExternalGateway):
    """Canonical adapter boundary with no live network implementation."""

    name = "national_integration"
    trust_level = DataTrustLevel.NON_CRITICAL
    calls_per_minute = 120
    cache_ttl = 300.0
    stale_threshold = 120.0
    _SCHEMA = [
        FieldRule("provider", str),
        FieldRule("operation", str),
        FieldRule("reference", str),
        FieldRule("status", str, allowed=["ACCEPTED"]),
        FieldRule("synthetic", bool, allowed=[True]),
    ]

    def __init__(self, provider: SyntheticNationalProvider | None = None) -> None:
        super().__init__()
        self.provider = provider or SyntheticNationalProvider()
        self._receipts: dict[str, IntegrationReceipt] = {}
        self.requested_mode = resolve_mode(
            "national_gateway",
            ("NATIONAL_GATEWAY_URL", "NATIONAL_GATEWAY_API_KEY"),
        )
        self.mode = AdapterMode.STUB
        if self.requested_mode is not AdapterMode.STUB:
            logger.error(
                "national integration live/shadow mode rejected by synthetic-only policy: %s",
                self.requested_mode.value,
            )

    @staticmethod
    def _digest(payload: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        ).hexdigest()

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not payload:
            raise ValidationError("payload must be a non-empty object")
        if any(token in json.dumps(payload, sort_keys=True).lower() for token in ("clinical_truth", "diagnosis", "lab_result", "phi")):
            raise SyntheticOnlyViolation("clinical truth cannot cross national integration boundary")

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context=self.name)

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        if self.requested_mode is not AdapterMode.STUB:
            raise SyntheticOnlyViolation("live and shadow national integrations are disabled")
        return self.provider.execute(action, kwargs["payload"])

    def submit(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> ExternalDataResult:
        if not idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        self._validate_payload(payload)
        digest = self._digest(payload)
        prior = self._receipts.get(idempotency_key)
        if prior is not None:
            if prior.request_digest != digest or prior.operation != operation:
                raise ValueError("IDEMPOTENCY_KEY_REUSE_WITH_DIFFERENT_REQUEST")
            return ExternalDataResult(
                data=prior.result,
                source="idempotency_receipt",
                trust_level=self.trust_level,
                gateway=self.name,
                action=operation,
                requires_verification=False,
            )

        result = self.call(
            action=operation,
            cache_key=self._make_cache_key(self.name, operation=operation, digest=digest),
            fallback={
                "provider": "synthetic-national-provider",
                "operation": operation,
                "reference": "SYN-FALLBACK",
                "status": "ACCEPTED",
                "synthetic": True,
            },
            payload=payload,
        )
        self._receipts[idempotency_key] = IntegrationReceipt(
            idempotency_key=idempotency_key,
            request_digest=digest,
            operation=operation,
            status=str(result.data.get("status", "UNKNOWN")),
            result=dict(result.data),
        )
        return result


__all__ = [
    "IntegrationReceipt",
    "NationalIntegrationGateway",
    "SyntheticNationalProvider",
    "SyntheticOnlyViolation",
]
