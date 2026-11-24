"""GULA Platform — Kill Switch
==============================
Central emergency stop for all autonomous system actions.

When ACTIVE:
  - All auto_repair actions are blocked
  - Self-audit auto-fix is blocked
  - Scaling operations are blocked
  - All AI autonomous decisions are blocked

Normal API traffic and reads continue unaffected.
This is NOT a system shutdown — only autonomous AI/repair actions stop.

Activation:
  # Via environment (requires container restart)
  KILL_SWITCH=true docker compose restart gula-backend

  # Via API (instant, no restart needed — admin only)
  POST /admin/kill-switch/activate
  POST /admin/kill-switch/deactivate
  GET  /admin/kill-switch/status

  # Via Redis (instant, propagates to all instances)
  redis-cli SET gula:kill_switch 1
  redis-cli DEL gula:kill_switch
"""

from __future__ import annotations

import logging
import os
import time

from app.config import IS_PRODUCTION

logger = logging.getLogger("gula.killswitch")

_REDIS_KEY = "gula:kill_switch"
_ENV_KEY = "KILL_SWITCH"

# In-memory override (set via API, survives without Redis)
_in_memory_active: bool = False
_activated_at: float = 0.0
_activated_reason: str = ""


def _read_shared_state() -> tuple[bool, bool]:
    """Read the cross-instance kill-switch key.

    Returns ``(remote_active, readable)``. ``readable`` is ``False`` when the
    shared store could not be consulted at all (Redis down, or a process-local
    store in production/staging). The caller decides whether an unreadable
    state may mean "inactive" (development/test) or must mean "active"
    (production/staging — fail closed).
    """
    try:
        from app.security.redis_client import security_store

        store = security_store("Kill switch")
        val = store.get(_REDIS_KEY)
    except Exception as exc:  # noqa: BLE001 — any read failure must be classified
        logger.debug("[KILL-SWITCH] Shared state unreadable: %s", exc)
        return False, False
    return bool(val and str(val) not in ("0", "false", "")), True


def _evaluate() -> tuple[bool, bool, bool]:
    """Return ``(active, shared_state_readable, fail_closed)``.

    Order: in-memory override → env var → shared Redis state.
    """
    # In-memory (fastest, set by API)
    if _in_memory_active:
        return True, True, False

    # Environment variable (requires restart)
    if os.getenv(_ENV_KEY, "false").lower() in ("true", "1", "yes"):
        return True, True, False

    remote_active, readable = _read_shared_state()
    if readable:
        return remote_active, True, False

    # The emergency-stop state lives in shared storage by design: an operator
    # may have activated it on another instance. When that state cannot be
    # read, silently assuming "inactive" would let autonomous actions run
    # against an active switch (fail-open). In production/staging the only
    # safe assumption is ACTIVE; autonomous actions are blocked while normal
    # API traffic and reads continue (S-06 residual).
    if IS_PRODUCTION:
        logger.critical(
            "[KILL-SWITCH] Shared emergency-stop state is unreadable — failing "
            "CLOSED (treating the switch as ACTIVE). Autonomous actions stay "
            "blocked until shared state is readable.",
        )
        return True, False, True

    return False, False, False


def is_kill_switch_active() -> bool:
    """Return True if kill switch is active.

    Checks (in order): in-memory flag → env var → shared Redis key. If the
    shared key cannot be read in production/staging the switch is treated as
    ACTIVE (fail closed) so a Redis outage can never disable an emergency stop.
    """
    return _evaluate()[0]


def activate(reason: str = "manual", propagate: bool = True) -> dict:
    """Activate the kill switch immediately.
    propagate=True writes to Redis so all instances see it.
    """
    global _in_memory_active, _activated_at, _activated_reason
    _in_memory_active = True
    _activated_at = time.time()
    _activated_reason = reason

    logger.critical("[KILL-SWITCH] ACTIVATED — reason: %s", reason)

    if propagate:
        try:
            from app.security.redis_client import cache

            cache.set(_REDIS_KEY, "1", ex=86400)  # auto-expire after 24h
        except Exception as e:
            logger.warning("[KILL-SWITCH] Redis propagation failed: %s", e)

    return status()


def deactivate(reason: str = "manual", propagate: bool = True) -> dict:
    """Deactivate the kill switch."""
    global _in_memory_active, _activated_at, _activated_reason
    _in_memory_active = False
    _activated_at = 0.0
    _activated_reason = ""

    logger.warning("[KILL-SWITCH] DEACTIVATED — reason: %s", reason)

    if propagate:
        try:
            from app.security.redis_client import cache

            cache.delete(_REDIS_KEY)
        except Exception as e:
            logger.warning("[KILL-SWITCH] Redis propagation failed: %s", e)

    return status()


def status() -> dict:
    active, shared_state_readable, fail_closed = _evaluate()
    return {
        "active": active,
        "reason": (
            "shared state unreadable — fail-closed (autonomous actions blocked)"
            if fail_closed
            else (_activated_reason if active else None)
        ),
        "activated_at": _activated_at if active else None,
        "env_override": os.getenv(_ENV_KEY, "false").lower() in ("true", "1"),
        "shared_state_readable": shared_state_readable,
    }
