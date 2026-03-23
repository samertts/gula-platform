"""
Production Startup Guard — GULA Platform
=========================================
Fail-fast sequential validation chain that runs before the app accepts traffic.

Sequence:
  1. validate_config()     — secrets present and not weak
  2. wait_for_db()         — DB reachable with exponential backoff
  3. check_migrations()    — alembic_version table has at least one row
  4. seed_critical_data()  — perm_version migration, test types, master admin
  5. mark system ready     — set module-level flag consumed by readiness probe

If any step fails the guard raises RuntimeError, uvicorn logs the traceback
and the process exits with a non-zero code — the Docker healthcheck never
turns green, so the api-gateway never receives traffic.
"""
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger("gula.startup")

# ── Module-level readiness flag ───────────────────────────────────────────────
# Set to True only after run_startup_guard() completes successfully.
# Consumed by /health/ready endpoint and the ReadinessMiddleware in main.py.
system_ready: bool = False


# ─── Step 1: Config Validation ───────────────────────────────────────────────

# Patterns that indicate a developer left in a placeholder / default value.
_WEAK_PATTERNS = (
    "default", "change", "secret", "example", "test", "demo",
    "gula_default", "changeme", "password", "12345", "abcdef",
)


def _is_weak(value: str) -> bool:
    """Return True if value looks like an insecure placeholder."""
    lower = value.lower()
    return any(pat in lower for pat in _WEAK_PATTERNS)


def validate_config() -> None:
    """Fail fast if any required secret is missing or dangerously weak.

    Called synchronously at import-time by run_startup_guard so errors
    are visible immediately in container logs.
    """
    from ..config import SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, IS_PRODUCTION

    errors: list[str] = []

    if not SECRET_KEY:
        errors.append("SECRET_KEY is not set")
    elif IS_PRODUCTION and _is_weak(SECRET_KEY):
        errors.append(
            f"SECRET_KEY looks like a placeholder/default value "
            f"(contains weak pattern). Set a strong random secret in .env."
        )

    if not ENCRYPTION_KEY:
        if IS_PRODUCTION:
            errors.append("ENCRYPTION_KEY is not set")
    elif IS_PRODUCTION and _is_weak(ENCRYPTION_KEY):
        errors.append(
            "ENCRYPTION_KEY looks like a placeholder. "
            "Generate with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    if not NID_HMAC_KEY:
        if IS_PRODUCTION:
            errors.append(
                "NID_HMAC_KEY is not set. "
                "Existing NID lookups will break if this changes between deployments."
            )
    elif IS_PRODUCTION and _is_weak(NID_HMAC_KEY):
        errors.append("NID_HMAC_KEY looks like a placeholder. Set a stable random key in .env.")

    if errors:
        for err in errors:
            logger.critical("[STARTUP GUARD] CONFIG ERROR: %s", err)
        raise RuntimeError(
            "Startup aborted — insecure configuration detected:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )

    logger.info("[STARTUP GUARD] Config validated OK")


# ─── Step 2: DB Connectivity with Exponential Backoff ────────────────────────

async def wait_for_db(max_retries: int = 5) -> None:
    """Wait for the database to become reachable.

    Retries with exponential backoff: 2, 4, 8, 16, 32 seconds.
    Raises RuntimeError if DB is still unreachable after all retries.
    """
    from ..database import check_db_connection

    for attempt in range(max_retries):
        if check_db_connection():
            logger.info("[STARTUP GUARD] Database connection OK (attempt %d)", attempt + 1)
            return

        wait_sec = 2 ** attempt
        logger.warning(
            "[STARTUP GUARD] Database not ready (attempt %d/%d) — retrying in %ds",
            attempt + 1, max_retries, wait_sec,
        )
        await asyncio.sleep(wait_sec)

    raise RuntimeError(
        f"Database unreachable after {max_retries} attempts. "
        "Check DATABASE_URL and PostgreSQL container status."
    )


# ─── Step 3: Migration Check ─────────────────────────────────────────────────

async def check_migrations() -> None:
    """Verify that Alembic migrations have been applied.

    We check for the existence of the alembic_version table and at least
    one row.  A fresh DB with only create_all (no alembic) is still OK —
    we only fail if the table exists but is empty (partial migration state).
    """
    from ..database import engine
    from sqlalchemy import text, inspect

    def _check() -> Optional[str]:
        """Returns None if OK, or an error message string."""
        insp = inspect(engine)
        if not insp.has_table("alembic_version"):
            # No alembic table — schema was built via create_all, which is
            # acceptable for the current deployment model.
            return None
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
            if row is None:
                return "alembic_version table exists but is empty (incomplete migration)"
            return None

    # Run the synchronous SQLAlchemy call in a thread pool
    loop = asyncio.get_event_loop()
    error = await loop.run_in_executor(None, _check)

    if error:
        raise RuntimeError(f"[STARTUP GUARD] Migration check failed: {error}")

    logger.info("[STARTUP GUARD] Migration check passed")


# ─── Step 4: Seed Critical Data ──────────────────────────────────────────────

async def seed_critical_data() -> None:
    """Run idempotent seed operations required for the system to function.

    Delegates to the existing functions in main.py to avoid duplication.
    Each function is safe to call multiple times.
    """
    from ..main import _migrate_perm_version, _seed_test_types, _ensure_master_admin

    loop = asyncio.get_event_loop()

    logger.info("[STARTUP GUARD] Running perm_version migration...")
    await loop.run_in_executor(None, _migrate_perm_version)

    logger.info("[STARTUP GUARD] Seeding test types catalog...")
    await loop.run_in_executor(None, _seed_test_types)

    logger.info("[STARTUP GUARD] Ensuring master admin exists...")
    await loop.run_in_executor(None, _ensure_master_admin)

    logger.info("[STARTUP GUARD] Critical data seeded OK")


# ─── Orchestrator ────────────────────────────────────────────────────────────

async def run_startup_guard() -> None:
    """Run the full startup validation chain.

    Call this from the FastAPI @app.on_event("startup") handler.
    On success, sets module-level `system_ready = True`.
    On failure, raises RuntimeError which crashes the process.
    """
    global system_ready

    t0 = time.perf_counter()
    logger.info("[STARTUP GUARD] === Starting production startup validation ===")

    try:
        # Step 1 — synchronous, must run first
        validate_config()

        # Step 2 — async with retry
        await wait_for_db(max_retries=5)

        # Step 3 — migration state
        await check_migrations()

        # Step 4 — seed
        await seed_critical_data()

    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.critical(
            "[STARTUP GUARD] STARTUP FAILED after %.0fms: %s",
            elapsed, exc,
        )
        raise

    elapsed = (time.perf_counter() - t0) * 1000
    system_ready = True
    logger.info(
        "[STARTUP GUARD] === System READY (%.0fms) — accepting traffic ===",
        elapsed,
    )
