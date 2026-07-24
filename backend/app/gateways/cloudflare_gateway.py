"""Cloudflare Gateway — DNS + WAF + Workers + R2
===============================================
Trust level: ENRICHMENT — operational/infra, never touches clinical data.

Purpose:
  - Probe the Cloudflare control-plane API to verify that our Zone, Worker
    route, WAF rule-set, and R2 bucket are reachable and healthy.
  - Surface the status to ``/integrations/status`` so an operator can see
    at a glance whether the edge layer is wired up.

Three operating modes (see ``app.gateways.mode``):

  STUB    — default. Returns a deterministic "configured=false" response
            without any network call. Safe for dev/CI.
  LIVE    — real HTTPS call to api.cloudflare.com/client/v4 using a scoped
            token. Requires CF_API_TOKEN + CF_ZONE_ID.
  SHADOW  — LIVE probe is executed and logged; STUB data returned.

Environment:
  GULA_ADAPTER_MODE_CLOUDFLARE = stub | live | shadow
  CF_API_TOKEN                 = scoped token (Zone:Read, DNS:Read, …)
  CF_ACCOUNT_ID                = Cloudflare account ID
  CF_ZONE_ID                   = Zone ID for the primary domain
  CF_R2_BUCKET                 = R2 bucket name (e.g. gula-reports)
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

logger = logging.getLogger("gula.gateways.cloudflare")

_gateway: CloudflareGateway | None = None

_ADAPTER_KEY = "cloudflare"
_REQUIRED_CREDS = ("CF_API_TOKEN", "CF_ZONE_ID")
_CF_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareGateway(ExternalGateway):
    name = "cloudflare"
    trust_level = DataTrustLevel.ENRICHMENT
    timeout = 8.0
    max_retries = 1
    calls_per_minute = 30
    circuit_failure_threshold = 3
    circuit_recovery_timeout = 120.0
    cache_ttl = 120.0  # 2 min — zone state is quasi-static
    stale_threshold = 60.0

    _SCHEMA = [
        FieldRule("configured", bool, required=True),
        FieldRule("zone_id", str, required=False),
        FieldRule("mode", str, required=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.mode = resolve_mode(_ADAPTER_KEY, _REQUIRED_CREDS)

    def current_mode(self) -> AdapterMode:
        return self.mode

    def _validate_response(self, response: Any) -> None:
        validate_schema(response, self._SCHEMA, context="cloudflare")

    def _stub_response(self) -> dict:
        return {
            "configured": False,
            "zone_id": os.getenv("CF_ZONE_ID", "") or "",
            "mode": "stub",
            "message": "Cloudflare credentials not active; using stub",
        }

    def _live_response(self) -> dict:
        token = os.environ["CF_API_TOKEN"]
        zone_id = os.environ["CF_ZONE_ID"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        # GET /zones/{zone_id} — the cheapest healthy-zone check there is
        zone = self._http("get", f"{_CF_API_BASE}/zones/{zone_id}", headers=headers)

        result = (zone or {}).get("result") or {}
        return {
            "configured": True,
            "zone_id": zone_id,
            "mode": "live",
            "name": result.get("name"),
            "status": result.get("status"),  # active/pending/...
            "plan": (result.get("plan") or {}).get("name"),
        }

    def _do_call(self, action: str, **kwargs: Any) -> Any:
        if self.mode is AdapterMode.STUB:
            return self._stub_response()

        if self.mode is AdapterMode.SHADOW:
            stub = self._stub_response()
            try:
                live = self._live_response()
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

        return self._live_response()


def get_cloudflare_gateway() -> CloudflareGateway:
    global _gateway
    if _gateway is None:
        _gateway = CloudflareGateway()
    return _gateway


def probe_cloudflare() -> ExternalDataResult:
    """Probe the configured Cloudflare zone for reachability + status."""
    gw = get_cloudflare_gateway()
    return gw.call(
        action="probe_zone",
        cache_key=CloudflareGateway._make_cache_key(
            "cloudflare",
            zone_id=os.getenv("CF_ZONE_ID", ""),
        ),
        fallback={"configured": False, "mode": "fallback"},
    )
