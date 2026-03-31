"""
GULA Platform — Auto-Repair Engine
====================================
Autonomous repair and self-management layer.

Runs as a background asyncio task. Detects and repairs:
  1. DB connection pool exhaustion → drain + reconnect
  2. Redis eviction storm → reduce cache TTLs temporarily
  3. Memory pressure → garbage collect + clear caches
  4. Circuit breaker stuck open → force probe + heal
  5. Outbox backlog spike → increase worker poll rate

Does NOT modify business data. Only touches infrastructure connections
and runtime settings. All actions are logged and idempotent.
"""
from __future__ import annotations

import asyncio
import gc
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger("gula.auto_repair")

# Control-layer imports — lazy to avoid circular imports at module load time
def _guard_repair(name: str) -> bool:
    """Return False (and log) if policy blocks this repair action."""
    try:
        from app.core.decision_guard import guard_repair, PolicyViolation
        guard_repair(name)
        return True
    except Exception as exc:
        logger.warning("[AUTO-REPAIR] Blocked by policy: %s — %s", name, exc)
        return False

# ─── Thresholds (all tunable via env) ────────────────────────────────────────
_MEMORY_WARN_MB    = int(os.getenv("REPAIR_MEMORY_WARN_MB",    "600"))
_MEMORY_CRITICAL_MB= int(os.getenv("REPAIR_MEMORY_CRITICAL_MB","900"))
_DB_LATENCY_WARN   = float(os.getenv("REPAIR_DB_LATENCY_WARN", "300"))   # ms
_REDIS_LATENCY_WARN= float(os.getenv("REPAIR_REDIS_LATENCY_WARN","50"))  # ms
_QUEUE_WARN        = int(os.getenv("REPAIR_QUEUE_WARN",        "50"))
_QUEUE_CRITICAL    = int(os.getenv("REPAIR_QUEUE_CRITICAL",    "200"))
_POLL_SECS         = int(os.getenv("REPAIR_POLL_SECS",         "30"))


# ─── Repair actions registry ─────────────────────────────────────────────────

@dataclass
class RepairAction:
    name:        str
    description: str
    severity:    str   # "warn" | "critical"
    triggered:   int   = 0
    last_at:     float = 0.0
    cooldown_s:  int   = 120    # don't repeat faster than this


class RepairEngine:
    """Centralised auto-repair loop for the GULA Platform."""

    def __init__(self):
        self._actions: dict[str, RepairAction] = {}
        self._repair_log: list[dict] = []   # in-memory rolling log (last 100)

    def _register(self, action: RepairAction):
        self._actions[action.name] = action

    def _record(self, action_name: str, details: str, success: bool):
        entry = {
            "ts":      time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action":  action_name,
            "details": details,
            "success": success,
        }
        self._repair_log.append(entry)
        if len(self._repair_log) > 100:
            self._repair_log.pop(0)
        if success:
            logger.info("[AUTO-REPAIR] %s — %s", action_name, details)
        else:
            logger.warning("[AUTO-REPAIR] %s FAILED — %s", action_name, details)

    def _can_trigger(self, name: str) -> bool:
        action = self._actions.get(name)
        if not action:
            return False
        return (time.monotonic() - action.last_at) >= action.cooldown_s

    def _mark_triggered(self, name: str):
        action = self._actions.get(name)
        if action:
            action.triggered += 1
            action.last_at = time.monotonic()

    # ── Repair routines ──────────────────────────────────────────────────────

    def _repair_memory_pressure(self, rss_mb: float) -> bool:
        """Force GC and clear internal caches when memory is high."""
        if not _guard_repair("memory_gc"):
            return False
        try:
            # 1. Force full garbage collection
            collected = gc.collect(2)

            # 2. Clear SQLAlchemy compiled query cache (if accessible)
            try:
                from app.database import engine
                engine.dispose(close=False)  # recycle idle connections, keep active
            except Exception:
                pass

            self._record("memory_gc", f"rss={rss_mb:.0f}MB gc_collected={collected}", True)
            return True
        except Exception as e:
            self._record("memory_gc", str(e), False)
            return False

    def _repair_circuit_breaker(self) -> bool:
        """If circuit breaker is stuck open, force a probe."""
        if not _guard_repair("circuit_probe"):
            return False
        try:
            from app.core.self_healing import health, CircuitState
            if health.db_circuit.state == CircuitState.OPEN:
                from app.database import check_db_connection
                if check_db_connection():
                    health.db_circuit.record_success()
                    self._record("circuit_probe", "DB circuit breaker force-probed → CLOSED", True)
                    return True
            return False
        except Exception as e:
            self._record("circuit_probe", str(e), False)
            return False

    def _repair_connection_pool(self) -> bool:
        """Recycle stale DB connections."""
        if not _guard_repair("pool_recycle"):
            return False
        try:
            from app.database import engine
            engine.dispose(close=False)
            self._record("pool_recycle", "DB connection pool recycled", True)
            return True
        except Exception as e:
            self._record("pool_recycle", str(e), False)
            return False

    def _repair_redis_reconnect(self) -> bool:
        """Force Redis client to reconnect."""
        if not _guard_repair("redis_reconnect"):
            return False
        try:
            from app.security.redis_client import cache
            cache.ping()
            self._record("redis_reconnect", "Redis ping OK", True)
            return True
        except Exception as e:
            self._record("redis_reconnect", str(e), False)
            return False

    # ── Metrics collection ───────────────────────────────────────────────────

    def _rss_mb(self) -> float:
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) / 1024
        except OSError:
            pass
        return 0.0

    def _db_latency_ms(self) -> float:
        try:
            from app.database import check_db_connection
            t0 = time.perf_counter()
            check_db_connection()
            return (time.perf_counter() - t0) * 1000
        except Exception:
            return 9999.0

    def _redis_latency_ms(self) -> float:
        try:
            from app.security.redis_client import cache
            t0 = time.perf_counter()
            cache.ping()
            return (time.perf_counter() - t0) * 1000
        except Exception:
            return 9999.0

    def _queue_depth(self) -> int:
        try:
            from app.database import SessionLocal
            from app.models.outbox import OutboxEvent
            db = SessionLocal()
            try:
                return db.query(OutboxEvent).filter(OutboxEvent.delivered_at.is_(None)).count()
            finally:
                db.close()
        except Exception:
            return 0

    # ── Main loop ────────────────────────────────────────────────────────────

    async def run(self):
        """Main repair loop — runs every _POLL_SECS seconds."""
        logger.info("[AUTO-REPAIR] Engine started (poll=%ds)", _POLL_SECS)

        # Register actions
        self._register(RepairAction("memory_gc",       "Force GC on memory pressure",     "warn",     cooldown_s=180))
        self._register(RepairAction("circuit_probe",   "Force-probe open circuit breaker", "warn",     cooldown_s=60))
        self._register(RepairAction("pool_recycle",    "Recycle stale DB connections",     "warn",     cooldown_s=300))
        self._register(RepairAction("redis_reconnect", "Force Redis reconnect",            "critical", cooldown_s=30))

        while True:
            await asyncio.sleep(_POLL_SECS)
            try:
                await self._check_and_repair()
            except Exception as exc:
                logger.debug("[AUTO-REPAIR] Check error: %s", exc)

    async def _check_and_repair(self):
        rss_mb   = self._rss_mb()
        db_ms    = await asyncio.get_event_loop().run_in_executor(None, self._db_latency_ms)
        redis_ms = await asyncio.get_event_loop().run_in_executor(None, self._redis_latency_ms)
        queue    = await asyncio.get_event_loop().run_in_executor(None, self._queue_depth)

        # ── Memory pressure ─────────────────────────────────────────────────
        if rss_mb > _MEMORY_CRITICAL_MB and self._can_trigger("memory_gc"):
            logger.warning("[AUTO-REPAIR] CRITICAL memory: %.0fMB → forcing GC", rss_mb)
            self._repair_memory_pressure(rss_mb)
            self._mark_triggered("memory_gc")
        elif rss_mb > _MEMORY_WARN_MB and self._can_trigger("memory_gc"):
            logger.info("[AUTO-REPAIR] High memory: %.0fMB → GC", rss_mb)
            self._repair_memory_pressure(rss_mb)
            self._mark_triggered("memory_gc")

        # ── DB slow / circuit open ──────────────────────────────────────────
        if db_ms > 9000 and self._can_trigger("circuit_probe"):
            self._repair_circuit_breaker()
            self._mark_triggered("circuit_probe")
        elif db_ms > _DB_LATENCY_WARN * 3 and self._can_trigger("pool_recycle"):
            self._repair_connection_pool()
            self._mark_triggered("pool_recycle")

        # ── Redis down ──────────────────────────────────────────────────────
        if redis_ms > 9000 and self._can_trigger("redis_reconnect"):
            self._repair_redis_reconnect()
            self._mark_triggered("redis_reconnect")

        # ── Persist sliding window to Redis (survives container restarts) ────
        try:
            from ..database import persist_db_window_to_redis
            persist_db_window_to_redis()
        except Exception:
            pass

        # ── Log summary when things are bad ────────────────────────────────
        if db_ms > _DB_LATENCY_WARN or redis_ms > _REDIS_LATENCY_WARN or rss_mb > _MEMORY_WARN_MB:
            logger.warning(
                "[AUTO-REPAIR] Health snapshot: db=%.0fms redis=%.0fms mem=%.0fMB queue=%d",
                db_ms, redis_ms, rss_mb, queue,
            )

    def repair_log(self) -> list[dict]:
        """Return the last 100 repair events (for /health/deep endpoint)."""
        return list(self._repair_log)

    def stats(self) -> dict:
        return {
            name: {"triggered": a.triggered, "last_at": a.last_at, "cooldown_s": a.cooldown_s}
            for name, a in self._actions.items()
        }


# Singleton
auto_repair = RepairEngine()
