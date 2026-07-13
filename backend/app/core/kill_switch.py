"""
GULA Platform — Kill Switch
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

logger = logging.getLogger("gula.killswitch")

_REDIS_KEY = "gula:kill_switch"
_ENV_KEY = "KILL_SWITCH"

# In-memory override (set via API, survives without Redis)
_in_memory_active: bool = False
_activated_at: float = 0.0
_activated_reason: str = ""


def is_kill_switch_active() -> bool:
    """
    Return True if kill switch is active.
    Checks (in order): in-memory flag → Redis key → env var.
    """
    global _in_memory_active

    # In-memory (fastest, set by API)
    if _in_memory_active:
        return True

    # Environment variable (requires restart)
    if os.getenv(_ENV_KEY, "false").lower() in ("true", "1", "yes"):
        return True

    # Redis key (instant cross-instance propagation)
    try:
        from app.security.redis_client import cache

        val = cache.get(_REDIS_KEY)
        if val and str(val) not in ("0", "false", ""):
            return True
    except Exception:
        pass  # Redis unavailable — fall through to False

    return False


def activate(reason: str = "manual", propagate: bool = True) -> dict:
    """
    Activate the kill switch immediately.
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
    active = is_kill_switch_active()
    return {
        "active": active,
        "reason": _activated_reason if active else None,
        "activated_at": _activated_at if active else None,
        "env_override": os.getenv(_ENV_KEY, "false").lower() in ("true", "1"),
    }
