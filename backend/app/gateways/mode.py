"""Adapter mode resolution for external gateways.

Every external adapter (gov NID, insurance, residency, Cloudflare, …) runs
in one of three modes, selected via environment variables:

  STUB    — fully offline, deterministic local logic. Default everywhere.
            Safe for dev, CI, demo environments, and production prior to
            government credentialing.
  LIVE    — real HTTPS call to the external provider. Requires the
            adapter's API key / URL to be set in the environment. Falls
            back to STUB automatically if credentials are missing.
  SHADOW  — LIVE call is made and logged for comparison, but the adapter
            returns STUB data to the caller. Used to validate a new
            external provider before trusting its responses.

Per-adapter selection, with a global default:

  GULA_ADAPTER_MODE=stub              (global default)
  GULA_ADAPTER_MODE_NID=live          (overrides the global for gov_nid)
  GULA_ADAPTER_MODE_INSURANCE=shadow
  GULA_ADAPTER_MODE_RESIDENCY=stub
  GULA_ADAPTER_MODE_CLOUDFLARE=live
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

from app._compat import StrEnum

logger = logging.getLogger("gula.gateways.mode")


class AdapterMode(StrEnum):
    STUB = "stub"
    LIVE = "live"
    SHADOW = "shadow"


_DEFAULT_ENV = "GULA_ADAPTER_MODE"


def resolve_mode(adapter_key: str, required_credentials: Iterable[str] = ()) -> AdapterMode:
    """Return the effective :class:`AdapterMode` for ``adapter_key``.

    Resolution order:

    1. ``GULA_ADAPTER_MODE_<KEY>`` — per-adapter override
    2. ``GULA_ADAPTER_MODE``       — global default
    3. ``AdapterMode.STUB``        — safe fallback

    If the requested mode is ``LIVE`` or ``SHADOW`` but any of the
    ``required_credentials`` are missing/empty in the environment, we
    down-grade to ``STUB`` and log a warning. This guarantees the system
    stays functional even when half-configured — critical for a national
    platform bootstrapping across labs that may not all have credentials
    yet.
    """
    key = adapter_key.upper().replace("-", "_")
    raw = os.getenv(f"{_DEFAULT_ENV}_{key}") or os.getenv(_DEFAULT_ENV) or "stub"
    try:
        mode = AdapterMode(raw.strip().lower())
    except ValueError:
        logger.warning(
            "gula.adapter.mode.invalid adapter=%s value=%r — falling back to STUB",
            adapter_key,
            raw,
        )
        return AdapterMode.STUB

    if mode is AdapterMode.STUB:
        return mode

    missing = [c for c in required_credentials if not os.getenv(c)]
    if missing:
        logger.warning(
            "gula.adapter.mode.downgrade adapter=%s requested=%s missing=%s — falling back to STUB",
            adapter_key,
            mode.value,
            ",".join(missing),
        )
        return AdapterMode.STUB

    return mode


__all__ = ["AdapterMode", "resolve_mode"]
