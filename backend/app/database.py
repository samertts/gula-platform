import collections
import contextvars
import logging
import os
import threading
import time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL, IS_PRODUCTION

logger = logging.getLogger("gula.database")

# ── Request correlation context ───────────────────────────────────────────────
# Set by middleware / auth dependency so every DB error log carries full context:
#   request_id + endpoint   ← set by RequestIDMiddleware
#   user_id + lab_id        ← set by get_current_user dependency (authenticated routes)
_request_id_var: contextvars.ContextVar[str]       = contextvars.ContextVar("request_id", default="")
_endpoint_var:   contextvars.ContextVar[str]       = contextvars.ContextVar("endpoint",   default="")
_user_id_var:    contextvars.ContextVar[int | None] = contextvars.ContextVar("user_id",   default=None)
_lab_id_var:     contextvars.ContextVar[int | None] = contextvars.ContextVar("lab_id",    default=None)

# ── Sliding window event tracker ─────────────────────────────────────────────

class _SlidingWindow:
    """Thread-safe circular buffer of (timestamp, event_type) entries.

    Allows querying how many events of a given type occurred in the last
    N seconds — distinguishes a brief burst from a sustained outage.
    """
    def __init__(self, max_age_s: int = 300, max_size: int = 1000):
        self._lock      = threading.Lock()
        self._events: collections.deque = collections.deque()
        self._max_age   = max_age_s
        self._max_size  = max_size

    def record(self, event_type: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._events.append((now, event_type))
            if len(self._events) > self._max_size:
                self._events.popleft()

    def count(self, event_type: str, window_s: int | None = None) -> int:
        """Count events of a given type in the last window_s seconds."""
        cutoff = time.monotonic() - (window_s or self._max_age)
        with self._lock:
            return sum(1 for ts, t in self._events if ts >= cutoff and t == event_type)

    def rate_per_minute(self, event_type: str, window_s: int = 300) -> float:
        """Return events per minute for the given type over the last window."""
        n = self.count(event_type, window_s)
        return round(n / (window_s / 60), 2)

    # ── Redis persistence ─────────────────────────────────────────────────────

    def persist_to_redis(
        self,
        redis_client,
        key: str = "gula:db_window:events",
    ) -> None:
        """Serialize recent events (wall-clock times) to Redis.

        Uses wall-clock timestamps so events survive process restarts —
        monotonic clock resets to 0 on each new process.
        """
        import json
        wall_now  = time.time()
        mono_now  = time.monotonic()
        offset    = wall_now - mono_now          # monotonic → wall-clock
        cutoff    = mono_now - self._max_age
        with self._lock:
            payload = json.dumps([
                (ts + offset, etype)
                for ts, etype in self._events
                if ts >= cutoff
            ])
        try:
            redis_client.set(key, payload, ex=self._max_age + 60)
        except Exception:
            pass  # best-effort — never raise from persistence code

    def restore_from_redis(
        self,
        redis_client,
        key: str = "gula:db_window:events",
    ) -> None:
        """Load previously persisted events from Redis on startup.

        Converts stored wall-clock timestamps back to monotonic for
        internal use.  Silently no-ops if Redis is empty or unavailable.
        """
        import json
        wall_now = time.time()
        mono_now = time.monotonic()
        offset   = mono_now - wall_now           # wall-clock → monotonic
        cutoff   = mono_now - self._max_age
        try:
            raw = redis_client.get(key)
            if raw is None:
                return
            events = json.loads(raw)
            restored = 0
            with self._lock:
                for wall_ts, etype in events:
                    mono_ts = wall_ts + offset
                    if mono_ts >= cutoff:
                        self._events.append((mono_ts, etype))
                        restored += 1
            if restored:
                logger.info("[DB] Sliding window: restored %d events from Redis", restored)
        except Exception as exc:
            logger.warning("[DB] Could not restore sliding window from Redis: %s", exc)

    def snapshot(self, window_s: int = 300) -> dict[str, int]:
        """Return counts for all event types in the last window_s seconds."""
        cutoff = time.monotonic() - window_s
        counts: dict[str, int] = {}
        with self._lock:
            for ts, t in self._events:
                if ts >= cutoff:
                    counts[t] = counts.get(t, 0) + 1
        return counts


# Singleton sliding window for DB connection events (5-minute window)
db_window = _SlidingWindow(max_age_s=300)

# ── Per-error-type counters (thread-safe, process-lifetime) ──────────────────
_counter_lock = threading.Lock()
_db_error_counts: dict[str, int] = {
    "refused":    0,
    "auth_failed": 0,
    "timeout":    0,
    "error":      0,
}

def get_db_error_counts() -> dict[str, int]:
    """Return a snapshot of cumulative DB error counts by type."""
    with _counter_lock:
        return dict(_db_error_counts)

def get_db_window_snapshot(window_s: int = 300) -> dict:
    """Return sliding-window stats for the last window_s seconds."""
    snap = db_window.snapshot(window_s)
    return {
        "window_s":         window_s,
        "refused":          snap.get("refused",    0),
        "auth_failed":      snap.get("auth_failed", 0),
        "timeout":          snap.get("timeout",    0),
        "ok":               snap.get("ok",         0),
        "refused_per_min":  db_window.rate_per_minute("refused",   window_s),
        "timeout_per_min":  db_window.rate_per_minute("timeout",   window_s),
    }

# ── Error → Action mapping ────────────────────────────────────────────────────
_DB_ACTION_MAP: dict[str, str] = {
    "refused":     "retry",
    "timeout":     "retry_with_backoff",
    "auth_failed": "stop_and_alert",
    "error":       "retry_with_backoff",
}

# ── Circuit escalation thresholds ────────────────────────────────────────────
_CIRCUIT_OPEN_THRESHOLD    = int(os.getenv("DB_CIRCUIT_OPEN_THRESHOLD",    "20"))  # refused in 5min
_SYSTEM_DEGRADE_THRESHOLD  = int(os.getenv("DB_SYSTEM_DEGRADE_THRESHOLD",  "50"))  # refused in 5min

# ── Connection Pool Sizing ────────────────────────────────────────────────────
# PostgreSQL default max_connections = 100.
# We run --workers 2, so each worker gets its own pool.
# Total DB connections = workers × (pool_size + max_overflow).
# Keep total well under 100 to leave room for superuser + monitoring connections.
#
# Formula used: 2 workers × (5 base + 15 overflow) = 40 total.
# Configurable via env vars for larger deployments.
_WORKERS       = int(os.getenv("WEB_CONCURRENCY", "2"))
_POOL_SIZE     = max(2, int(os.getenv("DB_POOL_SIZE",    "5")))   # per worker
_MAX_OVERFLOW  = max(0, int(os.getenv("DB_MAX_OVERFLOW", "15")))  # per worker
_POOL_TIMEOUT  = int(os.getenv("DB_POOL_TIMEOUT",  "10"))
_POOL_RECYCLE  = int(os.getenv("DB_POOL_RECYCLE", "1800"))
_STMT_TIMEOUT  = os.getenv("DB_STMT_TIMEOUT", "30s")

logger.debug(
    "DB pool config: %d workers × (%d base + %d overflow) = %d max connections",
    _WORKERS, _POOL_SIZE, _MAX_OVERFLOW, _WORKERS * (_POOL_SIZE + _MAX_OVERFLOW),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,             # Drop and replace stale connections silently
    pool_size=_POOL_SIZE,
    max_overflow=_MAX_OVERFLOW,
    pool_timeout=_POOL_TIMEOUT,     # Raise TimeoutError if pool exhausted
    pool_recycle=_POOL_RECYCLE,     # Prevent 8-hour idle disconnect (Postgres)
    connect_args={"connect_timeout": 5},
    echo=False,
)

# Set statement timeout + work_mem per connection (PostgreSQL only)
@event.listens_for(engine, "connect")
def set_pg_session_config(dbapi_conn, connection_record):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET statement_timeout = '{_STMT_TIMEOUT}'")
        cursor.execute("SET work_mem = '16MB'")  # Limit sort/hash memory per query
        cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        cursor.close()
    except Exception:
        pass  # Non-fatal — SQLite / non-Postgres


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database session dependency with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Lightweight database connectivity check."""
    return check_db_connection_detail()[0] == "ok"


def check_db_connection_detail() -> tuple[str, str]:
    """
    Detailed connectivity check — returns (status, message).

    status values:
      "ok"          — connected and query succeeded
      "refused"     — TCP connection refused (postgres not listening / wrong host)
      "auth_failed" — connected but authentication rejected (wrong password)
      "timeout"     — connection timed out
      "error"       — other / unknown error

    Callers can use this to distinguish transient (refused/timeout) from
    permanent (auth_failed) errors and skip retrying the latter.
    """
    import os
    from urllib.parse import urlparse

    db_url = os.getenv("DATABASE_URL", "")
    parsed = urlparse(db_url)
    host = parsed.hostname or "unknown"
    port = parsed.port or 5432

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_window.record("ok")
        return "ok", f"connected to {host}:{port}"

    except Exception as exc:
        msg = str(exc).lower()

        if "connection refused" in msg or "could not connect" in msg:
            status = "refused"
            detail = f"TCP connection refused to {host}:{port} — postgres not listening or wrong host"
        elif "password authentication failed" in msg or "authentication failed" in msg:
            status = "auth_failed"
            detail = f"authentication rejected by {host}:{port} — check POSTGRES_PASSWORD"
        elif "no pg_hba.conf entry" in msg:
            status = "auth_failed"
            detail = f"pg_hba.conf rejected connection from this host — check pg_hba.conf subnet"
        elif "timeout" in msg or "timed out" in msg:
            status = "timeout"
            detail = f"connection to {host}:{port} timed out"
        else:
            status = "error"
            detail = f"{host}:{port} — {str(exc)[:120]}"

        with _counter_lock:
            _db_error_counts[status] = _db_error_counts.get(status, 0) + 1

        db_window.record(status)
        action = _DB_ACTION_MAP.get(status, "retry")

        # ── Full correlation context ──────────────────────────────────────────
        # Gathered from ContextVars — propagated by middleware (request_id,
        # endpoint) and by get_current_user dependency (user_id, lab_id).
        req_id   = _request_id_var.get("")
        endpoint = _endpoint_var.get("")
        user_id  = _user_id_var.get(None)
        lab_id   = _lab_id_var.get(None)

        logger.error(
            "[DB] connection %s — action=%s — %s",
            status, action, detail,
            extra={
                "db_host":    host,
                "db_port":    port,
                "db_status":  status,
                "action":     action,
                "request_id": req_id  or None,
                "endpoint":   endpoint or None,
                "user_id":    user_id,
                "lab_id":     lab_id,
            },
        )

        # ── Circuit escalation — open circuit on sustained refused storm ──────
        if status == "refused":
            refused_5m = db_window.count("refused", window_s=300)
            if refused_5m >= _SYSTEM_DEGRADE_THRESHOLD:
                _trigger_system_degradation(refused_5m)
            elif refused_5m >= _CIRCUIT_OPEN_THRESHOLD:
                _trigger_circuit_open(refused_5m)

        return status, detail


def _trigger_circuit_open(refused_count: int) -> None:
    """Force-open the DB circuit breaker + enter L2_READ_ONLY when refused storm hits threshold."""
    try:
        from .core.self_healing import health, CircuitState, DegradationLevel
        if health.db_circuit.state != CircuitState.OPEN:
            for _ in range(health.db_circuit._failure_threshold):
                health.db_circuit.record_failure()
            logger.error(
                "[DB] Circuit OPENED after %d refused errors in 5min (threshold=%d)",
                refused_count, _CIRCUIT_OPEN_THRESHOLD,
            )
        # Escalate to L2: writes blocked, reads still pass
        health.enter_degraded_mode(
            f"DB circuit opened — {refused_count} refused errors in 5min",
            level=DegradationLevel.L2_READ_ONLY,
        )
    except Exception:
        pass


def _trigger_system_degradation(refused_count: int) -> None:
    """Escalate to L3_CRITICAL_ONLY when DB is continuously unreachable (storm)."""
    try:
        from .core.self_healing import health, DegradationLevel
        health.enter_degraded_mode(
            f"DB refused {refused_count} times in 5min (threshold={_SYSTEM_DEGRADE_THRESHOLD}) "
            "— critical-only mode active",
            level=DegradationLevel.L3_CRITICAL_ONLY,
        )
        logger.critical(
            "[DB] L3_CRITICAL_ONLY — %d refused errors in 5min. "
            "Only health/auth/kill-switch endpoints reachable.",
            refused_count,
        )
    except Exception:
        pass


def restore_db_window_from_redis() -> None:
    """Called once at startup — rehydrates the sliding window from Redis
    so circuit escalation thresholds aren't reset on every container restart.
    """
    try:
        from .security.redis_client import cache
        db_window.restore_from_redis(cache)
    except Exception as exc:
        logger.warning("[DB] Sliding window restore skipped: %s", exc)


def persist_db_window_to_redis() -> None:
    """Snapshot the current sliding window to Redis.
    Called by the auto-repair engine periodically (every poll cycle).
    """
    try:
        from .security.redis_client import cache
        db_window.persist_to_redis(cache)
    except Exception as exc:
        logger.warning("[DB] Sliding window persist skipped: %s", exc)


def get_pool_status() -> dict:
    """Get connection pool metrics for monitoring."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
