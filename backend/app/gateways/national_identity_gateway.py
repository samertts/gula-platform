"""
Iraqi National Identity Gateway — Ministry of Interior Integration
==================================================================
Trust level: NON_CRITICAL — used for identity enrichment, not clinical decisions.

SECURITY:
  - Cache keys are MD5(gateway + national_id) — raw IDs never appear in cache keys.
  - Responses validated strictly before use.
  - CRITICAL operations (clinical decisions) must use internal DB records only.
"""

from __future__ import annotations

from typing import Any

from app.gateways.base import (
    DataTrustLevel,
    ExternalDataResult,
    ExternalGateway,
    FieldRule,
    validate_schema,
)

_gateway: "NationalIdentityGateway | None" = None

_VALID_ID_LENGTHS = {12, 16}


class NationalIdentityGateway(ExternalGateway):
    name                      = "national_identity"
    trust_level               = DataTrustLevel.NON_CRITICAL
    timeout                   = 10.0
    max_retries               = 2
    calls_per_minute          = 20
    circuit_failure_threshold = 3
    circuit_recovery_timeout  = 120.0
    cache_ttl                 = 300.0
    stale_threshold           = 120.0

    _SCHEMA = [
        FieldRule("valid",  bool, required=True),
        FieldRule("source", str,  required=True),
    ]

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="national_identity")

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        national_id: str = kwargs.get("national_id", "")

        # ── Placeholder ───────────────────────────────────────────────────────
        # Replace with real HTTP call when MoI API is available:
        #
        #   return self._http("post", "https://moi.gov.iq/api/id/verify",
        #                     json={"id": national_id},
        #                     headers={"X-API-Key": settings.MOI_API_KEY})
        #
        if len(national_id) not in _VALID_ID_LENGTHS:
            return {
                "valid":   False,
                "source":  "local_validation",
                "message": "Invalid ID length",
            }

        return {
            "valid":   True,
            "source":  "local_validation",
            "message": "Awaiting government registry integration",
        }


def get_national_identity_gateway() -> NationalIdentityGateway:
    global _gateway
    if _gateway is None:
        _gateway = NationalIdentityGateway()
    return _gateway


def verify_national_id(national_id: str) -> ExternalDataResult:
    """
    Verify a national ID number.

    Returns ExternalDataResult. Callers must NOT use this result for any
    clinical decision — it is NON_CRITICAL enrichment only.
    """
    gw = get_national_identity_gateway()
    return gw.call(
        action="verify_national_id",
        cache_key=NationalIdentityGateway._make_cache_key(
            "national_identity", national_id=national_id
        ),
        fallback={"valid": False, "source": "fallback"},
        national_id=national_id,
    )
