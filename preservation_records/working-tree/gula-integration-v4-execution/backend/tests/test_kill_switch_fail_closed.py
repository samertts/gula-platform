"""Regression tests for the kill-switch fail-open residual (S-06 follow-up).

Finding
-------
``app/core/kill_switch.is_kill_switch_active()`` consulted the shared Redis key
inside ``try/except: pass`` and fell through to ``False``. In production or
staging that meant a Redis outage could make an **active** emergency stop —
possibly activated from another instance, or persisted from a previous run —
read as inactive, so autonomous actions (auto-repair, self-audit fixes, scaling,
AI decisions) would resume while the operator believed the platform was halted.

Policy under test
-----------------
* The kill-switch state is shared by design. If it cannot be read in
  production/staging, the switch is treated as **ACTIVE** (fail closed):
  autonomous actions stay blocked, normal API traffic and reads are unaffected.
* If the shared state *is* readable and says "inactive", the switch is inactive
  — fail-closed must not invent a permanent outage.
* Development/test keep the previous fail-open behaviour so a Redis-less local
  environment does not block autonomous tooling.
* An in-memory activation still wins over any unreadable shared state.
* The consumer that matters (the policy engine) actually blocks autonomous
  actions when the switch fails closed.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

import app.core.kill_switch as ks
from app.core.policy_engine import ActionType, PolicyEngine
from app.security.redis_client import SecurityStoreUnavailable, _MemoryStore


class _FailingSharedStore:
    """A shared-looking store whose reads fail (Redis died after startup)."""

    is_shared = True

    def get(self, key):  # noqa: ARG002
        raise ConnectionError("redis unavailable")

    def set(self, *args, **kwargs):  # noqa: ARG002
        raise ConnectionError("redis unavailable")

    def delete(self, key):  # noqa: ARG002
        raise ConnectionError("redis unavailable")


class _ReadableStore:
    """Minimal readable store with a fixed value."""

    is_shared = True

    def __init__(self, value):
        self._value = value

    def get(self, key):  # noqa: ARG002
        return self._value

    def set(self, *args, **kwargs):
        return True

    def delete(self, key):
        return True


@pytest.fixture(autouse=True)
def _reset_in_memory_state():
    ks._in_memory_active = False
    ks._activated_at = 0.0
    ks._activated_reason = ""
    yield
    ks._in_memory_active = False
    ks._activated_at = 0.0
    ks._activated_reason = ""


def _production_env():
    """Patch the module-level environment gates the way a production boot sees them."""
    return (
        patch.object(ks, "IS_PRODUCTION", True),
        patch.dict(os.environ, {"KILL_SWITCH": "false", "ALLOW_DEGRADED_REDIS": "false"}),
    )


# ── Fail-closed: unreadable shared state in production/staging ──────────────


def test_production_redis_read_failure_treats_switch_as_active():
    prod, env = _production_env()
    with prod, env, patch("app.security.redis_client.cache", _FailingSharedStore()):
        assert ks.is_kill_switch_active() is True


def test_production_process_local_store_treats_switch_as_active():
    """S-06 boundary: production with a process-local store must raise, not downgrade."""
    prod, env = _production_env()
    with (
        prod,
        env,
        patch("app.security.redis_client.IS_PRODUCTION", True),
        patch("app.security.redis_client.cache", _MemoryStore()),
    ):
        with pytest.raises(SecurityStoreUnavailable):
            # sanity: the shared-state contract really is closed
            from app.security.redis_client import security_store

            security_store("Kill switch")
        assert ks.is_kill_switch_active() is True


def test_production_status_reports_fail_closed_reason():
    prod, env = _production_env()
    with prod, env, patch("app.security.redis_client.cache", _FailingSharedStore()):
        state = ks.status()
    assert state["active"] is True
    assert state["shared_state_readable"] is False
    assert "fail-closed" in (state["reason"] or "")


# ── No false positive: a readable, inactive key stays inactive ──────────────


def test_production_readable_inactive_key_stays_inactive():
    prod, env = _production_env()
    with prod, env, patch("app.security.redis_client.security_store", lambda _op: _ReadableStore(None)):
        assert ks.is_kill_switch_active() is False
        assert ks.status()["shared_state_readable"] is True


def test_production_readable_active_key_stays_active():
    prod, env = _production_env()
    with prod, env, patch("app.security.redis_client.security_store", lambda _op: _ReadableStore("1")):
        assert ks.is_kill_switch_active() is True


# ── Scope: development/test keep fail-open behaviour ────────────────────────


def test_non_production_redis_failure_stays_inactive():
    with (
        patch.object(ks, "IS_PRODUCTION", False),
        patch.dict(os.environ, {"KILL_SWITCH": "false", "ALLOW_DEGRADED_REDIS": "false"}),
        patch("app.security.redis_client.cache", _FailingSharedStore()),
    ):
        assert ks.is_kill_switch_active() is False


def test_in_memory_activation_wins_over_unreadable_shared_state():
    prod, env = _production_env()
    with prod, env, patch("app.security.redis_client.cache", _FailingSharedStore()):
        ks.activate("operator emergency stop", propagate=True)
        assert ks.is_kill_switch_active() is True
        assert ks.status()["reason"] == "operator emergency stop"


# ── Consumer proof: autonomous actions are actually blocked ─────────────────


def test_policy_engine_blocks_autonomous_action_when_switch_fails_closed():
    prod, env = _production_env()
    engine = PolicyEngine()
    with prod, env, patch("app.security.redis_client.cache", _FailingSharedStore()):
        decision = engine.evaluate(ActionType.AUTO_REPAIR, {"env": "production"})
    assert decision.allowed is False
    assert "kill switch" in decision.reason.lower()


def test_policy_engine_still_allows_when_state_is_readable_and_inactive():
    prod, env = _production_env()
    engine = PolicyEngine()
    with prod, env, patch("app.security.redis_client.security_store", lambda _op: _ReadableStore(None)):
        decision = engine.evaluate(ActionType.AUTO_REPAIR, {"env": "production"})
    assert decision.allowed is True
