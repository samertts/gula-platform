"""Iraqi Residency Gateway — foreign traveler residency verification
===================================================================
Trust level: NON_CRITICAL — used for patient-registry enrichment (whether a
presented passport/residency number maps to a currently valid residency
record in the Ministry of Interior's Directorate of Residency Affairs).
Never drives clinical decisions.

Three operating modes (see ``app.gateways.mode``):

  STUB    — default. Local shape-validation only (passport must be 6–12
            alphanumerics). Returns a deterministic placeholder.
  LIVE    — real HTTPS call to the residency directorate endpoint.
  SHADOW  — LIVE call made and logged; STUB data returned to caller.

Environment:
  GULA_ADAPTER_MODE_RESIDENCY = stub | live | shadow
  RESIDENCY_API_URL           = https://residency.moi.gov.iq
  RESIDENCY_API_KEY           = ...
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from app.gateways.base import (
    DataTrustLevel,
    ExternalDataResult,
    ExternalGateway,
    FieldRule,
    validate_schema,
)
from app.gateways.mode import AdapterMode, resolve_mode

logger = logging.getLogger("gula.gateways.residency")

_gateway: ResidencyGateway | None = None

_ADAPTER_KEY = "residency"
_REQUIRED_CREDS = ("RESIDENCY_API_URL", "RESIDENCY_API_KEY")
_PASSPORT_RE = re.compile(r"^[A-Z0-9]{6,12}$", re.IGNORECASE)


class ResidencyGateway(ExternalGateway):
    name = "residency"
    trust_level = DataTrustLevel.NON_CRITICAL
    timeout = 10.0
    max_retries = 2
    calls_per_minute = 20
    circuit_failure_threshold = 3
    circuit_recovery_timeout = 120.0
    cache_ttl = 600.0
    stale_threshold = 300.0

    _SCHEMA = [
        FieldRule("valid", bool, required=True),
        FieldRule("source", str, required=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.mode = resolve_mode(_ADAPTER_KEY, _REQUIRED_CREDS)

    def _mask_sensitive(self, data: Any) -> Any:
        if isinstance(data, dict):
            masked = data.copy()
            for key in ["passport_no", "national_id", "phone", "address", "full_name"]:
                if key in masked:
                    masked[key] = "***MASKED***"
            return masked
        return data

    def current_mode(self) -> AdapterMode:
        return self.mode

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="residency")

    def _stub_response(self, passport_no: str, nationality: str | None) -> dict:
        if not passport_no or not _PASSPORT_RE.match(passport_no):
            return {
                "valid": False,
                "source": "stub_local_validation",
                "message": "Invalid passport format",
            }
        return {
            "valid": True,
            "source": "stub_local_validation",
            "nationality": (nationality or "unknown").upper(),
            "status": "pending_verification",
            "message": "Awaiting residency directorate credential",
        }

    def _live_response(self, passport_no: str, nationality: str | None) -> dict:
        base = os.environ["RESIDENCY_API_URL"].rstrip("/")
        key = os.environ["RESIDENCY_API_KEY"]
        return self._http(
            "post",
            f"{base}/api/residency/verify",
            json={"passport_no": passport_no, "nationality": nationality},
            headers={"X-API-Key": key, "Accept": "application/json"},
        )

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        passport_no = (kwargs.get("passport_no") or "").strip()
        nationality = kwargs.get("nationality")

        if self.mode is AdapterMode.STUB:
            return self._stub_response(passport_no, nationality)

        if self.mode is AdapterMode.SHADOW:
            stub = self._stub_response(passport_no, nationality)
            try:
                live = self._live_response(passport_no, nationality)
                logger.info(
                    "[SHADOW] gateway=%s action=%s stub=%r live=%r",
                    self.name,
                    action,
                    self._mask_sensitive(stub),
                    self._mask_sensitive(live),
                )
            except Exception as exc:
                logger.warning(
                    "[SHADOW] gateway=%s action=%s live_error=%s",
                    self.name,
                    action,
                    exc,
                )
            return stub

        return self._live_response(passport_no, nationality)


def get_residency_gateway() -> ResidencyGateway:
    global _gateway
    if _gateway is None:
        _gateway = ResidencyGateway()
    return _gateway


def verify_residency(passport_no: str, nationality: str | None = None) -> ExternalDataResult:
    """Verify a foreign traveller's Iraqi residency record."""
    gw = get_residency_gateway()
    return gw.call(
        action="verify_residency",
        cache_key=ResidencyGateway._make_cache_key(
            "residency",
            passport_no=passport_no,
            nationality=nationality or "",
        ),
        fallback={"valid": False, "source": "fallback"},
        passport_no=passport_no,
        nationality=nationality,
    )
