"""Integrations health + probe API.

Endpoints:

  GET  /integrations/status            — snapshot of every adapter's mode, circuit
                                         state, and trust level. Admin-only.
  POST /integrations/{name}/probe      — force a live probe against ``name``
                                         (currently: national_identity, insurance,
                                         residency, cloudflare). Admin-only.

Design:
  - Never exposes raw API keys or identifiers, only mode + health flags.
  - STUB mode is the safe default — the probe runs against the stub unless
    the operator has set GULA_ADAPTER_MODE_* + the adapter's credentials.
  - The registry is declarative: adding a new gateway means adding one
    line to ``_REGISTRY``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..gateways.base import CircuitState, ExternalGateway
from ..gateways.cloudflare_gateway import (
    get_cloudflare_gateway,
    probe_cloudflare,
)
from ..gateways.insurance_gateway import (
    check_insurance,
    get_insurance_gateway,
)
from ..gateways.national_identity_gateway import (
    get_national_identity_gateway,
    verify_national_id,
)
from ..gateways.residency_gateway import (
    get_residency_gateway,
    verify_residency,
)
from ..models.lab_user import LabUser
from ..security.rbac import require_role

router = APIRouter(prefix="/integrations", tags=["integrations"])


_PROBE_KWARGS: dict[str, dict[str, Any]] = {
    "national_identity": {"national_id": "000000000000"},
    "insurance": {"insurance_id": "probe-placeholder"},
    "residency": {"passport_no": "PROBE123"},
    "cloudflare": {},
}

_GETTERS: dict[str, Callable[[], ExternalGateway]] = {
    "national_identity": get_national_identity_gateway,
    "insurance": get_insurance_gateway,
    "residency": get_residency_gateway,
    "cloudflare": get_cloudflare_gateway,
}

_PROBES: dict[str, Callable[[], Any]] = {
    "national_identity": lambda: verify_national_id("000000000000"),
    "insurance": lambda: check_insurance("probe-placeholder"),
    "residency": lambda: verify_residency("PROBE123"),
    "cloudflare": probe_cloudflare,
}


def _snapshot(name: str, gw: ExternalGateway) -> dict:
    """Serialize one gateway's health signal without exposing secrets."""
    # `mode` is set in __init__ on mode-aware gateways; fall back to "n/a".
    mode = getattr(gw, "mode", None)
    mode_value = mode.value if mode is not None else "n/a"

    circuit = gw._circuit  # introspection only; no mutation
    return {
        "name": name,
        "trust_level": gw.trust_level.value,
        "mode": mode_value,
        "circuit": circuit.state.value,
        "healthy": circuit.state is not CircuitState.OPEN,
        "cache_size": len(gw._cache),
        "cache_ttl": gw.cache_ttl,
        "timeout": gw.timeout,
    }


# ── GET /integrations/status ─────────────────────────────────────────────────


@router.get("/status")
def integrations_status(
    _user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
) -> dict:
    """Snapshot of every registered adapter — mode + circuit + trust level."""
    return {
        "adapters": [_snapshot(name, getter()) for name, getter in _GETTERS.items()],
    }


# ── POST /integrations/{name}/probe ──────────────────────────────────────────


@router.post("/{name}/probe")
def integrations_probe(
    name: str,
    _user: LabUser = Depends(require_role("master_admin", "ministry_admin")),
) -> dict:
    """Force a probe call against a single adapter."""
    if name not in _PROBES:
        raise HTTPException(status_code=404, detail=f"unknown adapter: {name}")

    try:
        result = _PROBES[name]()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Probe failed") from exc

    # Result is ExternalDataResult — reduce to safe dict
    return {
        "name": name,
        "source": result.source,
        "is_stale": result.is_stale,
        "requires_verification": result.requires_verification,
        "trust_level": result.trust_level.value,
        "data": result.data,
    }
