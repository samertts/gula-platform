# GULA Platform — Reliability Report (PROGRAM-BETA Phase 3)

**Date:** 2026-08-06
**Status:** VERIFIED — resilience primitives present, tested, and wired.

---

## 1. Executive Summary

Reliability engineering was verified across retries, circuit breaking, bulkheading,
timeouts, graceful degradation, and the outbox pattern. All primitives exist in
`shared/` and the backend core, are exercised by unit tests (28 reliability tests
pass), and are wired into the Kernel/control plane.

**Verdict: PASS.**

## 2. Resilience Primitives (verified)

| Primitive | Location | Behavior |
|---|---|---|
| Exponential-backoff retry (sync + async) | `shared/retry/decorators.py` | 3 attempts, 0.5 s base, 2.0× backoff, 30 s cap; `on_retry` hook |
| Safe call (graceful fallback) | `shared/retry/decorators.py` `safe_call` / `safe_call_async` | Returns default on exception |
| Timeout guard | `call_with_timeout` | ThreadPool + `future.result(timeout=5)` |
| Bulkhead (isolation) | `Bulkhead` | Max-concurrent slot guard, raises `BulkheadFullError` |
| Circuit breaker | `shared/circuit_breaker.py` | Closed→Open→Half-open, threshold 5, half-open max 3, concurrent-safe |
| Kernel gateway breaker | `app/kernel/gateway/circuit_breaker.py` | Per-dependency `CircuitBreakerManager` |
| Outbox pattern | backend + `scripts/auto_repair.py` | Transactional outbox with 2 s poll, auto-restore |

## 3. Graceful Degradation (verified)

- **Redis down:** `redis_client.py` falls back to a thread-safe in-memory store with
  TTL — rate limiting and session blacklist degrade, never crash.
- **DB down:** lazy engines; `/health` reflects degraded mode; `DegradedModeMiddleware`
  serves degraded responses instead of 5xx storms.
- **AI provider down:** stub mode (`No AI API key configured — using stub mode`).
- **Queue down:** `_LazyTaskQueue` defers Redis connection to first `enqueue()`.

## 4. Autonomous recovery (see Phase 8 report)
- `scripts/self_heal.py` (ASHS): signal detection → risk classification → action with
  600 s cooldown → recovery verification. Runs in `--dry-run` correctly in this env.
- `app/core/auto_repair.py` (RepairEngine): idempotent, decision-guarded, logged
  repair actions incl. pool recycle + outbox backlog restore.
- `app/core/self_healing.py`: circuit breakers + degraded mode.

## 5. Tests (all passing)
| Suite | Tests | Covers |
|---|---|---|
| `test_circuit_breaker.py` | 8 | open/half-open/close, reset, concurrency, protocol |
| `test_outbox_auto_repair.py` | 12 | outbox poll, backlog repair, auto-restore |
| `test_self_heal_cooldown.py` | 8 | ASHS signal cooldown + persistence |
| `test_niam_session_security.py` | 9 | session revocation, workspace binding, max concurrent |

## 6. Residual / Tracked
| Item | Priority | Notes |
|---|---|---|
| Self-heal incident log writes to `/var/log/` (permission-dependent) | Low | Correctly degrades with warning; logrotate configured for prod |
| `call_with_timeout` spawns a thread per call | Low | For low-frequency ops; keep out of per-request hot path |

## 7. Conclusion

**PASS.** Retry/backoff, circuit breaking, bulkheading, timeouts, graceful degradation,
and outbox-backed reliability are implemented, tested, and wired. The platform is
designed to survive dependency outages without crashing.
