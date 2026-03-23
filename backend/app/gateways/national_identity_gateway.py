"""
Iraqi National Identity Gateway — Ministry of Interior Integration
==================================================================
Wraps the (future) government national ID verification API behind the
ExternalGateway safe layer: circuit breaker, rate limiter, caching,
validation, audit log.

Current state: local format validation only.
When the MoI API is ready, override _do_call to make the real HTTP call.

SECURITY NOTE: national IDs are sensitive PII.
  - We never cache a raw national_id string as a cache key.
  - Cache keys are MD5(gateway_name + national_id) — not reversible.
  - Responses are validated before use; unexpected shapes are rejected.
"""

from __future__ import annotations

from typing import Any

from app.gateways.base import ExternalGateway

_gateway: "NationalIdentityGateway | None" = None

_VALID_ID_LENGTHS = {12, 16}


class NationalIdentityGateway(ExternalGateway):
    name                      = "national_identity"
    timeout                   = 10.0
    max_retries               = 2
    calls_per_minute          = 20    # government API quota is usually tight
    circuit_failure_threshold = 3
    circuit_recovery_timeout  = 120.0
    cache_ttl                 = 300.0  # 5 min — IDs don't change, but limit staleness

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        national_id: str = kwargs.get("national_id", "")

        # ── Placeholder: local format check ──────────────────────────────────
        # Replace with real HTTP call when MoI API is available:
        #
        #   return self._http("post", "https://moi.gov.iq/api/id/verify",
        #                     json={"id": national_id}, headers={"X-API-Key": API_KEY})
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

    def _validate_response(self, response: Any) -> bool:
        return (
            isinstance(response, dict)
            and "valid" in response
            and isinstance(response["valid"], bool)
        )


def get_national_identity_gateway() -> NationalIdentityGateway:
    global _gateway
    if _gateway is None:
        _gateway = NationalIdentityGateway()
    return _gateway


def verify_national_id(national_id: str) -> dict:
    """
    Public API — verify a national ID number.

    Returns a dict with at least ``{"valid": bool}``.
    Never raises — falls back to ``{"valid": False, "source": "fallback"}``
    if the service is unavailable.
    """
    gw = get_national_identity_gateway()
    # Use hashed key so the raw ID is not stored in the cache dict keys
    cache_key = NationalIdentityGateway._make_cache_key(
        "national_identity", national_id=national_id
    )
    return gw.call(
        action="verify_national_id",
        cache_key=cache_key,
        fallback={"valid": False, "source": "fallback"},
        national_id=national_id,
    )
