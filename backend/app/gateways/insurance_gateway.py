"""
Iraqi Health Insurance Gateway — Law No.22 of 2020
====================================================
Trust level: NON_CRITICAL — insurance status affects billing, not clinical decisions.

Three operating modes (see ``app.gateways.mode``):

  STUB    — default. Always returns a placeholder ``pending_verification``
            record — safe for dev/CI and pre-credential production.
  LIVE    — real HTTPS call to the Iraqi National Health Insurance API if
            ``INSURANCE_API_URL`` + ``INSURANCE_API_KEY`` are set.
  SHADOW  — LIVE call made and logged; STUB data returned to caller.

Environment:
  GULA_ADAPTER_MODE_INSURANCE = stub | live | shadow
  INSURANCE_API_URL           = https://nhi.gov.iq
  INSURANCE_API_KEY           = ...
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.gateways.base import (
    DataTrustLevel,
    ExternalDataResult,
    ExternalGateway,
    FieldRule,
    validate_schema,
)
from app.gateways.mode import AdapterMode, resolve_mode

logger = logging.getLogger("gula.gateways.insurance")

_gateway: InsuranceGateway | None = None

_ADAPTER_KEY = "insurance"
_REQUIRED_CREDS = ("INSURANCE_API_URL", "INSURANCE_API_KEY")


class InsuranceGateway(ExternalGateway):
    name = "insurance"
    trust_level = DataTrustLevel.NON_CRITICAL
    timeout = 8.0
    max_retries = 1
    calls_per_minute = 30
    circuit_failure_threshold = 3
    circuit_recovery_timeout = 120.0
    cache_ttl = 600.0  # 10 min — insurance status is slow-changing
    stale_threshold = 300.0  # flag as stale after 5 min

    # ── Schema: what the government API must return ───────────────────────────
    _SCHEMA = [
        FieldRule("insured", bool, required=True),
        FieldRule("source", str, required=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.mode = resolve_mode(_ADAPTER_KEY, _REQUIRED_CREDS)

    def current_mode(self) -> AdapterMode:
        return self.mode

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="insurance")

    def _stub_response(self, insurance_id: str) -> dict:
        if not insurance_id:
            return {"insured": False, "source": "stub_local_validation"}
        return {
            "insured": True,
            "provider": "national_health_insurance",
            "status": "pending_verification",
            "source": "stub_local_validation",
        }

    def _live_response(self, insurance_id: str) -> dict:
        base = os.environ["INSURANCE_API_URL"].rstrip("/")
        key = os.environ["INSURANCE_API_KEY"]
        return self._http(
            "post",
            f"{base}/api/verify",
            json={"id": insurance_id},
            headers={"X-API-Key": key, "Accept": "application/json"},
        )

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        insurance_id: str = kwargs.get("insurance_id", "") or ""

        if self.mode is AdapterMode.STUB:
            return self._stub_response(insurance_id)

        if self.mode is AdapterMode.SHADOW:
            stub = self._stub_response(insurance_id)
            try:
                live = self._live_response(insurance_id)
                logger.info(
                    "[SHADOW] gateway=%s action=%s stub=%r live=%r",
                    self.name,
                    action,
                    stub,
                    live,
                )
            except Exception as exc:
                logger.warning(
                    "[SHADOW] gateway=%s action=%s live_error=%s",
                    self.name,
                    action,
                    exc,
                )
            return stub

        # LIVE
        return self._live_response(insurance_id)


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
