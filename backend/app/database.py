import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL, IS_PRODUCTION

logger = logging.getLogger("gula.database")

# Production-tuned connection pool
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,         # Verify connections before use
    pool_size=20,               # Base connections (up from 10)
    max_overflow=40,            # Burst capacity (up from 20)
    pool_timeout=15,            # Fail fast if pool exhausted (down from 30)
    pool_recycle=1800,          # Recycle every 30 min (prevent stale)
    connect_args={"connect_timeout": 5},  # Faster failure detection (down from 10)
    echo=False,                 # No SQL logging in production
)

# Set statement timeout to prevent runaway queries (30 seconds)
@event.listens_for(engine, "connect")
def set_pg_timeout(dbapi_conn, connection_record):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SET statement_timeout = '30s'")
        cursor.close()
    except Exception:
        pass  # Non-fatal - some DBs don't support this


# Pool event logging for monitoring
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    logger.debug("Connection returned to pool")


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
