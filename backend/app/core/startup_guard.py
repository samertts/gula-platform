"""
Production Startup Guard — GULA Platform
=========================================
Fail-fast, atomic sequential validation chain that runs before the app
accepts traffic.

Sequence (all-or-nothing):
  1. validate_config()     — secrets present and not weak/default
  2. wait_for_db()         — DB reachable with exponential backoff
  3. check_migrations()    — alembic_version table has at least one row
  4. seed_critical_data()  — perm_version migration, test types, master admin

Only if every step above passes does system_ready become True.
A single failure keeps system_ready = False and crashes the process so the
Docker healthcheck never turns green and the api-gateway receives no traffic.

Hybrid Readiness (is_system_ready):
  system_ready (startup completed) AND db_pool healthy AND redis alive.
  This means the /health/ready probe stays red even after startup if the DB
  or Redis later disconnects — triggering a container restart automatically.
"""
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger("gula.startup")

# ── Module-level readiness flag ───────────────────────────────────────────────
# Set to True only inside run_startup_guard() after every step passes.
# Never set to True anywhere else.
system_ready: bool = False


# ─── Hybrid Readiness Check ──────────────────────────────────────────────────

def is_system_ready() -> tuple[bool, str]:
    """Return (ready: bool, reason: str).

    Combines the startup-completed flag with live connectivity checks so
    /health/ready stays accurate after startup (DB/Redis failures post-startup
    will flip the probe back to 503 and trigger a container restart).
    """
    if not system_ready:
        return False, "startup_in_progress"

    # Live DB check
    try:
        from ..database import check_db_connection
        if not check_db_connection():
            return False, "database_unavailable"
    except Exception:
        return False, "database_error"

    # Live Redis check
    try:
        from ..security.redis_client import cache as _redis
        _redis.set("_readiness_probe", "1", ex=10)
    except Exception:
        return False, "redis_unavailable"

    return True, "ok"


# ─── Step 1: Config Validation ───────────────────────────────────────────────

_WEAK_PATTERNS = (
    "default", "change", "secret", "example", "test", "demo",
    "gula_default", "changeme", "password", "12345", "abcdef",
)


def _is_weak(value: str) -> bool:
    lower = value.lower()
    return any(pat in lower for pat in _WEAK_PATTERNS)


def validate_config() -> None:
    """Fail fast if any required secret is missing or dangerously weak."""
    from ..config import SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, IS_PRODUCTION

    errors: list[str] = []

    if not SECRET_KEY:
        errors.append("SECRET_KEY is not set")
    elif IS_PRODUCTION and _is_weak(SECRET_KEY):
        errors.append(
            "SECRET_KEY looks like a placeholder/default value. "
            "Set a strong random secret: openssl rand -hex 64"
        )

    if not ENCRYPTION_KEY:
        if IS_PRODUCTION:
            errors.append("ENCRYPTION_KEY is not set")
    elif IS_PRODUCTION and _is_weak(ENCRYPTION_KEY):
        errors.append(
            "ENCRYPTION_KEY looks like a placeholder. Generate with: "
            "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    if not NID_HMAC_KEY:
        if IS_PRODUCTION:
            errors.append(
                "NID_HMAC_KEY is not set. "
                "Existing NID lookups will break if this changes between deployments."
            )
    elif IS_PRODUCTION and _is_weak(NID_HMAC_KEY):
        errors.append("NID_HMAC_KEY looks like a placeholder. Set a stable random key.")

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
    """Wait for DB to become reachable. Raises RuntimeError after all retries."""
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
    """Verify Alembic migrations are not in a partial state."""
    from ..database import engine
    from sqlalchemy import text, inspect

    def _check() -> Optional[str]:
        insp = inspect(engine)
        if not insp.has_table("alembic_version"):
            # Schema built via create_all — acceptable for current deployment model
            return None
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).fetchone()
            if row is None:
                return "alembic_version table exists but is empty (incomplete migration)"
        return None

    loop = asyncio.get_event_loop()
    error = await loop.run_in_executor(None, _check)
    if error:
        raise RuntimeError(f"[STARTUP GUARD] Migration check failed: {error}")

    logger.info("[STARTUP GUARD] Migration check passed")


# ─── Step 4: Seed Critical Data ──────────────────────────────────────────────

async def seed_critical_data() -> None:
    """Run idempotent seed operations. Safe to call multiple times."""
    from ..main import _migrate_perm_version, _seed_test_types, _ensure_master_admin

    loop = asyncio.get_event_loop()

    logger.info("[STARTUP GUARD] Running perm_version migration...")
    await loop.run_in_executor(None, _migrate_perm_version)

    logger.info("[STARTUP GUARD] Seeding test types catalog...")
    await loop.run_in_executor(None, _seed_test_types)

    logger.info("[STARTUP GUARD] Ensuring master admin exists...")
    await loop.run_in_executor(None, _ensure_master_admin)

    logger.info("[STARTUP GUARD] Critical data seeded OK")


# ─── Atomic Orchestrator ─────────────────────────────────────────────────────

async def run_startup_guard() -> None:
    """Atomic startup validation chain.

    system_ready is set to True ONLY if every single step succeeds.
    Any exception keeps system_ready = False and re-raises — the process
    will crash and the Docker healthcheck will never turn green.

    There is no partial success: either everything passes or nothing does.
    """
    global system_ready

    # Guard against double-initialisation (e.g. hot-reload in dev)
    if system_ready:
        logger.warning("[STARTUP GUARD] Already initialised — skipping")
        return

    t0 = time.perf_counter()
    logger.info("[STARTUP GUARD] === Starting production startup validation ===")

    try:
        validate_config()          # Step 1 — synchronous
        await wait_for_db(max_retries=5)   # Step 2 — async retry
        await check_migrations()           # Step 3 — migration state
        await seed_critical_data()         # Step 4 — seed

    except Exception:
        elapsed = (time.perf_counter() - t0) * 1000
        # logger.exception captures full traceback automatically
        logger.exception(
            "[STARTUP GUARD] STARTUP FAILED after %.0fms — system_ready remains False",
            elapsed,
        )
        # system_ready stays False — readiness probe keeps returning 503
        raise  # crash the process so Docker restarts the container

    # Atomic success: only reached if no exception above
    elapsed = (time.perf_counter() - t0) * 1000
    system_ready = True
    logger.info(
        "[STARTUP GUARD] === System READY (%.0fms) — accepting traffic ===",
        elapsed,
    )
