"""NR-103 — the self-healing Redis repair reported success while Redis was down.

`app/security/redis_client.py` binds `cache` once, at import:

    cache: _MemoryStore | _RedisWrapper = _build_cache()

`_build_cache()` falls back to `_MemoryStore` when REDIS_URL is unset OR when
Redis is merely unreachable at that moment. The second path needs no flag:
production correctly fails closed on an unset REDIS_URL (config.py exits unless
ALLOW_DEGRADED_REDIS=true), but a deployment whose Redis happens to be down when
a worker boots silently gets a per-worker store.

`_MemoryStore.ping()` returns True unconditionally -- "always available". The
auto-repair engine's `_repair_redis_reconnect` called `cache.ping()` and, on
True, recorded ("redis_reconnect", "Redis ping OK", True). So the repair
reported a SUCCESSFUL Redis repair while Redis was down and nothing had been
repaired. Executed, with REDIS_URL pointing at a closed port: cache is
_MemoryStore, is_shared() is False, and ping() is True.

It is named "reconnect" and cannot reconnect: nothing rebinds `cache`, so a
worker that booted during an outage stays degraded for its whole lifetime, long
after Redis returns.

What that costs is not cosmetic. Token revocation runs on this cache --
security/auth.py blacklist_token/is_token_blacklisted -- so logout, and
revoking a compromised session, become worker-local. Executed: worker A revokes
a jti, worker A sees it revoked, worker B does not. Sessions, rate limiting, MFA
challenges, the API firewall and HTTP idempotency (NR-095) ride the same store.

A rebuild is deliberately NOT attempted here. Five modules bind `cache` at
module level -- services/idempotency.py, security/session.py,
security/rate_limit.py, routes/verification.py, firewall/api_firewall.py -- and
would keep the old object across a rebind, leaving revocation recovered while
rate limiting and idempotency silently were not. Partial recovery that looks
total is worse than honest degradation. The ledger below pins those five so the
cost of the real fix cannot grow unnoticed.
"""

from __future__ import annotations

import ast
import pathlib

from app.core.auto_repair import RepairEngine
from app.security import redis_client as rc


class _FakeSharedCache:
    """Stands in for a Redis-backed wrapper: anything that is not _MemoryStore."""

    def ping(self) -> bool:
        return True


def test_a_liveness_ping_cannot_answer_whether_the_cache_is_shared():
    """The exact confusion the repair action was built on."""
    store = rc._MemoryStore()
    assert store.ping() is True, (
        "_MemoryStore.ping() is expected to return True — that is precisely why "
        "it must not be used to decide whether Redis is healthy"
    )


def test_is_shared_is_false_for_the_in_memory_fallback(monkeypatch):
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())
    assert rc.is_shared() is False
    reason = rc.degraded_reason()
    assert reason, "a degraded cache must explain itself"
    assert "worker" in reason.lower(), f"the reason must say it is per-worker: {reason}"


def test_is_shared_is_true_for_a_redis_backed_cache(monkeypatch):
    monkeypatch.setattr(rc, "cache", _FakeSharedCache())
    assert rc.is_shared() is True
    assert rc.degraded_reason() == "", "a shared cache must report no degradation"


def test_the_repair_does_not_report_success_while_degraded(monkeypatch):
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())
    monkeypatch.setattr("app.core.auto_repair._guard_repair", lambda name: True)
    engine = RepairEngine()
    assert engine._repair_redis_reconnect() is False, (
        "the repair reported success for a Redis reconnect it did not and cannot "
        "perform — the process is on a per-worker in-memory store"
    )


def test_the_repair_reports_success_when_the_cache_really_is_shared(monkeypatch):
    """Positive proof: the guard must not just always fail."""
    monkeypatch.setattr(rc, "cache", _FakeSharedCache())
    monkeypatch.setattr("app.core.auto_repair._guard_repair", lambda name: True)
    engine = RepairEngine()
    assert engine._repair_redis_reconnect() is True


def test_the_degraded_reason_says_a_restart_is_needed(monkeypatch):
    """A worker that fell back does not recover on its own; the operator must know."""
    monkeypatch.setattr(rc, "REDIS_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())
    reason = rc.degraded_reason().lower()
    assert "restart" in reason, (
        f"the reason must say the process cannot self-recover: {reason}"
    )


#: Modules that bind `cache` at MODULE level. Each one would keep a stale store
#: across any future rebuild of the singleton, so each is a site the real fix
#: must convert to a late lookup or a proxy. MAY SHRINK, MAY NEVER GROW.
DECLARED_MODULE_LEVEL_CACHE_BINDERS = frozenset({
    "app/firewall/api_firewall.py",
    "app/routes/verification.py",
    "app/security/rate_limit.py",
    "app/security/session.py",
    "app/services/idempotency.py",
})

_APP = pathlib.Path(rc.__file__).resolve().parent.parent


def _module_level_cache_binders() -> set[str]:
    found: set[str] = set()
    files = sorted(_APP.rglob("*.py"))
    assert len(files) > 400, f"source scan looks vacuous ({len(files)} files)"
    for path in files:
        if path.name == "redis_client.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:  # module level only, not nested in a function
            if isinstance(node, ast.ImportFrom) and node.module:
                if "redis_client" not in node.module:
                    continue
                if any(a.name == "cache" for a in node.names):
                    found.add(str(path.relative_to(_APP.parent)))
    return found


def test_the_set_of_module_level_cache_binders_does_not_grow():
    current = _module_level_cache_binders()
    new = current - DECLARED_MODULE_LEVEL_CACHE_BINDERS
    assert not new, (
        "these modules bind `cache` at import, so they would keep a stale store "
        "if the singleton were ever rebuilt. Import it inside the function "
        "instead, or the eventual Redis-recovery fix cannot reach them:\n  "
        + "\n  ".join(sorted(new))
    )
    stale = DECLARED_MODULE_LEVEL_CACHE_BINDERS - current
    assert not stale, (
        "these no longer bind `cache` at module level and must leave the ledger:\n  "
        + "\n  ".join(sorted(stale))
    )
