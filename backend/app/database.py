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
# Set by middleware on each request so DB errors carry request_id + endpoint.
_request_id_var:  contextvars.ContextVar[str] = contextvars.ContextVar("request_id",  default="")
_endpoint_var:    contextvars.ContextVar[str] = contextvars.ContextVar("endpoint",    default="")

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

        # ── Correlation context (request_id + endpoint from middleware) ───────
        req_id   = _request_id_var.get("")
        endpoint = _endpoint_var.get("")

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
    """Force-open the DB circuit breaker when refused storm crosses threshold."""
    try:
        from .core.self_healing import health, CircuitState
        if health.db_circuit.state != CircuitState.OPEN:
            for _ in range(health.db_circuit._failure_threshold):
                health.db_circuit.record_failure()
            logger.error(
                "[DB] Circuit OPENED after %d refused errors in 5min (threshold=%d)",
                refused_count, _CIRCUIT_OPEN_THRESHOLD,
            )
    except Exception:
        pass


def _trigger_system_degradation(refused_count: int) -> None:
    """Enter system degraded mode when DB is continuously unreachable."""
    try:
        from .core.self_healing import health
        health.enter_degraded_mode(
            f"DB refused {refused_count} times in 5min (threshold={_SYSTEM_DEGRADE_THRESHOLD}) "
            "— switching to read-only/cache mode"
        )
        logger.critical(
            "[DB] SYSTEM DEGRADED — %d refused errors in 5min. "
            "Write endpoints will return 503. Read-only mode active.",
            refused_count,
        )
    except Exception:
        pass


def get_pool_status() -> dict:
    """Get connection pool metrics for monitoring."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
