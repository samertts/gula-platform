import logging
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL, IS_PRODUCTION

logger = logging.getLogger("gula.database")

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
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_pool_status() -> dict:
    """Get connection pool metrics for monitoring."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }
