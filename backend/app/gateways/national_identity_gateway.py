"""Iraqi National Identity Gateway — Ministry of Interior Integration
==================================================================
Trust level: NON_CRITICAL — used for identity enrichment, not clinical decisions.

Three operating modes (see ``app.gateways.mode``):

  STUB    — default. Local length-validation only; no network call.
  LIVE    — real HTTPS call to the MoI endpoint if credentials are present.
  SHADOW  — LIVE call is made and logged, but STUB data is returned to the
            caller. Used for pre-production validation.

Environment:
  GULA_ADAPTER_MODE_NID       = stub | live | shadow
  MOI_NID_API_URL             = https://...  (required for live/shadow)
  MOI_NID_API_KEY             = ...          (required for live/shadow)

SECURITY:
  - Cache keys are MD5(gateway + national_id) — raw IDs never appear in cache keys.
  - Responses validated strictly before use.
  - CRITICAL operations (clinical decisions) must use internal DB records only.
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

logger = logging.getLogger("gula.gateways.national_identity")

_gateway: NationalIdentityGateway | None = None

_VALID_ID_LENGTHS = {12, 16}
_ADAPTER_KEY = "nid"
_REQUIRED_CREDS = ("MOI_NID_API_URL", "MOI_NID_API_KEY")


class NationalIdentityGateway(ExternalGateway):
    name = "national_identity"
    trust_level = DataTrustLevel.NON_CRITICAL
    timeout = 10.0
    max_retries = 2
    calls_per_minute = 20
    circuit_failure_threshold = 3
    circuit_recovery_timeout = 120.0
    cache_ttl = 300.0
    stale_threshold = 120.0

    _SCHEMA = [
        FieldRule("valid", bool, required=True),
        FieldRule("source", str, required=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.mode = resolve_mode(_ADAPTER_KEY, _REQUIRED_CREDS)

    # Exposed for health probes
    def current_mode(self) -> AdapterMode:
        return self.mode

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="national_identity")

    def _stub_response(self, national_id: str) -> dict:
        if len(national_id) not in _VALID_ID_LENGTHS:
            return {
                "valid": False,
                "source": "stub_local_validation",
                "message": "Invalid ID length",
            }
        return {
            "valid": True,
            "source": "stub_local_validation",
            "message": "Awaiting MoI production credential",
        }

    def _live_response(self, national_id: str) -> dict:
        base = os.environ["MOI_NID_API_URL"].rstrip("/")
        key = os.environ["MOI_NID_API_KEY"]
        return self._http(
            "post",
            f"{base}/api/id/verify",
            json={"id": national_id},
            headers={"X-API-Key": key, "Accept": "application/json"},
        )

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        national_id: str = kwargs.get("national_id", "") or ""

        if self.mode is AdapterMode.STUB:
            return self._stub_response(national_id)

        if self.mode is AdapterMode.SHADOW:
            stub = self._stub_response(national_id)
            try:
                live = self._live_response(national_id)
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
        return self._live_response(national_id)


def get_national_identity_gateway() -> NationalIdentityGateway:
    global _gateway
    if _gateway is None:
        _gateway = NationalIdentityGateway()
    return _gateway


def verify_national_id(national_id: str) -> ExternalDataResult:
    """Verify a national ID number.

    Returns ExternalDataResult. Callers must NOT use this result for any
    clinical decision — it is NON_CRITICAL enrichment only.
    """
    gw = get_national_identity_gateway()
    return gw.call(
        action="verify_national_id",
        cache_key=NationalIdentityGateway._make_cache_key(
            "national_identity", national_id=national_id,
        ),
        fallback={"valid": False, "source": "fallback"},
        national_id=national_id,
    )
