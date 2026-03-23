"""
Iraqi Health Insurance Gateway — Law No.22 of 2020
====================================================
Trust level: NON_CRITICAL — insurance status affects billing, not clinical decisions.

Schema validation enforced: rejects any response that doesn't have the exact
expected shape. Stale cache is flagged. Fallback includes requires_verification=True
so the caller knows the data needs human confirmation.
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

_gateway: "InsuranceGateway | None" = None


class InsuranceGateway(ExternalGateway):
    name                      = "insurance"
    trust_level               = DataTrustLevel.NON_CRITICAL
    timeout                   = 8.0
    max_retries               = 1
    calls_per_minute          = 30
    circuit_failure_threshold = 3
    circuit_recovery_timeout  = 120.0
    cache_ttl                 = 600.0   # 10 min — insurance status is slow-changing
    stale_threshold           = 300.0   # flag as stale after 5 min

    # ── Schema: what the government API must return ───────────────────────────
    _SCHEMA = [
        FieldRule("insured",  bool, required=True),
        FieldRule("source",   str,  required=True),
    ]

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="insurance")

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        insurance_id: str = kwargs.get("insurance_id", "")

        # ── Placeholder ───────────────────────────────────────────────────────
        # Replace with real HTTP call when government API is available:
        #
        #   return self._http("post", "https://nhi.gov.iq/api/verify",
        #                     json={"id": insurance_id},
        #                     headers={"X-API-Key": settings.INSURANCE_API_KEY})
        #
        if not insurance_id:
            return {"insured": False, "source": "local_validation"}

        return {
            "insured":  True,
            "provider": "national_health_insurance",
            "status":   "pending_verification",
            "source":   "local_validation",
        }


def get_insurance_gateway() -> InsuranceGateway:
    global _gateway
    if _gateway is None:
        _gateway = InsuranceGateway()
    return _gateway


def check_insurance(insurance_id: str) -> ExternalDataResult:
    """
    Check insurance status for a given ID.

    Returns ExternalDataResult. Callers must check ``requires_verification``
    before using the result in billing logic.
    """
    gw = get_insurance_gateway()
    return gw.call(
        action="check_insurance",
        cache_key=InsuranceGateway._make_cache_key("insurance", insurance_id=insurance_id),
        fallback={"insured": False, "source": "fallback"},
        insurance_id=insurance_id,
    )
