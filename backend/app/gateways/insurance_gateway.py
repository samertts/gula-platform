"""
Iraqi Health Insurance Gateway — Law No.22 of 2020
====================================================
Wraps the (future) national health insurance API behind the ExternalGateway
safe layer: circuit breaker, rate limiter, caching, validation, audit log.

Current state: placeholder local validation.
When the government API is ready, override _do_call to make the real HTTP call.
"""

from __future__ import annotations

from typing import Any

from app.gateways.base import ExternalGateway

# Singleton — one circuit breaker shared across all calls to this service
_gateway: "InsuranceGateway | None" = None


class InsuranceGateway(ExternalGateway):
    name                      = "insurance"
    timeout                   = 8.0    # government APIs can be slow
    max_retries               = 1      # one retry is enough for status checks
    calls_per_minute          = 30
    circuit_failure_threshold = 3
    circuit_recovery_timeout  = 120.0  # 2-minute cooldown
    cache_ttl                 = 600.0  # insurance status valid for 10 min

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        insurance_id: str = kwargs.get("insurance_id", "")

        # ── Placeholder: local format check ──────────────────────────────────
        # Replace this block with an httpx call when the real API is available:
        #
        #   return self._http("post", "https://nhi.gov.iq/api/verify", json={...})
        #
        if not insurance_id:
            return {"insured": False, "source": "local_validation"}

        return {
            "insured":  True,
            "provider": "national_health_insurance",
            "status":   "pending_verification",
            "source":   "local_validation",
        }

    def _validate_response(self, response: Any) -> bool:
        return (
            isinstance(response, dict)
            and "insured" in response
            and isinstance(response["insured"], bool)
        )


def get_insurance_gateway() -> InsuranceGateway:
    global _gateway
    if _gateway is None:
        _gateway = InsuranceGateway()
    return _gateway


def check_insurance(insurance_id: str) -> dict:
    """
    Public API — check insurance status for a given ID.

    Returns a dict with at least ``{"insured": bool}``.
    Never raises — falls back to ``{"insured": False, "source": "fallback"}``
    if the service is unavailable.
    """
    gw = get_insurance_gateway()
    cache_key = InsuranceGateway._make_cache_key("insurance", insurance_id=insurance_id)
    return gw.call(
        action="check_insurance",
        cache_key=cache_key,
        fallback={"insured": False, "source": "fallback"},
        insurance_id=insurance_id,
    )
