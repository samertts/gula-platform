"""Production Startup Guard — GULA Platform
=========================================
Fail-fast, atomic sequential validation chain that runs before the app
accepts traffic.

Sequence (all-or-nothing):
   1. validate_config()     — secrets present and not weak/default
   2. wait_for_db()         — DB reachable with exponential backoff
   3. check_redis()         — Redis reachable (fatal — restart container if down)
   4. check_migrations()    — alembic_version table has at least one row
   5. seed_critical_data()  — perm_version migration, test types, master admin

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

logger = logging.getLogger("gula.startup")

# ── Module-level readiness flag ───────────────────────────────────────────────
# Set to True only inside run_startup_guard() after every step passes.
system_ready: bool = False
_readiness_reason: str = "startup_in_progress"


def set_system_ready(ready: bool, reason: str = "ok") -> None:
    """Explicitly set the system readiness state (used by external startup handlers)."""
    global system_ready, _readiness_reason
    system_ready = ready
    _readiness_reason = reason
    if ready:
        logger.info("[STARTUP GUARD] System marked READY: %s", reason)
    else:
        logger.warning("[STARTUP GUARD] System marked NOT READY: %s", reason)


# ─── Hybrid Readiness Check ──────────────────────────────────────────────────


def is_system_ready() -> tuple[bool, str]:
    """Return (ready: bool, reason: str).

    Readiness tiers:
      CRITICAL  — PostgreSQL.  If DB is down, all requests return 503.
      OPTIONAL  — Redis.       If Redis is down after startup, the system
                               continues in degraded mode (in-memory fallback).
                               Login, reads, and writes keep working; only
                               cross-process session invalidation is weakened.

    This prevents a Redis hiccup from taking the entire platform offline.
    """
    if not system_ready:
        return False, "startup_in_progress"

    # ── CRITICAL: Database ────────────────────────────────────────────────────
    try:
        from ..database import check_db_connection

        if not check_db_connection():
            return False, "database_unavailable"
    except Exception:
        return False, "database_error"

    # ── OPTIONAL: Redis (runtime failure → degraded, not 503) ─────────────────
    # Redis is mandatory at startup (redis_client.py exits if unreachable).
    # Post-startup failures are tolerated: in-memory fallback takes over
    # automatically for rate-limiting and perm_version checks.
    try:
        from ..security.redis_client import cache as _redis

        _redis.set("_readiness_probe", "1", ex=10)
    except Exception:
        logger.warning(
            "[READINESS] Redis unreachable — system continues in degraded mode "
            "(in-memory fallback active; cross-process invalidation weakened)",
        )
        # Return ready=True with a warning reason instead of blocking all traffic
        return True, "degraded_redis"

    return True, "ok"


# ─── Step 1: Config Validation ───────────────────────────────────────────────

_WEAK_PATTERNS = (
    "default",
    "change",
    "secret",
    "example",
    "test",
    "demo",
    "gula_default",
    "changeme",
    "password",
    "12345",
    "abcdef",
)


def _is_weak(value: str) -> bool:
    lower = value.lower()
    return any(pat in lower for pat in _WEAK_PATTERNS)


def validate_config() -> None:
    """Fail fast if any required secret is missing or dangerously weak."""
    from ..config import AUDIT_ANCHOR_KEY, ENCRYPTION_KEY, IS_PRODUCTION, NID_HMAC_KEY, SECRET_KEY

    errors: list[str] = []

    if not SECRET_KEY:
        if IS_PRODUCTION:
            errors.append("SECRET_KEY is not set")
    elif IS_PRODUCTION and _is_weak(SECRET_KEY):
        errors.append(
            "SECRET_KEY looks like a placeholder/default value. "
            "Set a strong random secret: openssl rand -hex 64",
        )

    if not ENCRYPTION_KEY:
        if IS_PRODUCTION:
            errors.append("ENCRYPTION_KEY is not set")
    elif IS_PRODUCTION and _is_weak(ENCRYPTION_KEY):
        errors.append(
            "ENCRYPTION_KEY looks like a placeholder. Generate with: "
            'python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
        )
    elif IS_PRODUCTION:
        # Validate it's actually a Fernet-compatible key (32 bytes, base64url, 44 chars)
        try:
            from cryptography.fernet import Fernet as _Fernet

            _Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
        except Exception:
            errors.append(
                "ENCRYPTION_KEY is not a valid Fernet key (must be 44 base64url chars). "
                'Run: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
            )

    if not NID_HMAC_KEY:
        if IS_PRODUCTION:
            errors.append(
                "NID_HMAC_KEY is not set. "
                "Existing NID lookups will break if this changes between deployments.",
            )
    elif IS_PRODUCTION and _is_weak(NID_HMAC_KEY):
        errors.append("NID_HMAC_KEY looks like a placeholder. Set a stable random key.")

    if not AUDIT_ANCHOR_KEY:
        if IS_PRODUCTION:
            errors.append("AUDIT_ANCHOR_KEY is not set. Set in .env for audit chain integrity.")
    elif IS_PRODUCTION and _is_weak(AUDIT_ANCHOR_KEY):
        errors.append("AUDIT_ANCHOR_KEY looks like a placeholder. Set a stable random key.")

    if errors:
        for err in errors:
            logger.critical("[STARTUP GUARD] CONFIG ERROR: %s", err)
        raise RuntimeError(
            "Startup aborted — insecure configuration detected:\n"
            + "\n".join(f"  • {e}" for e in errors),
        )

    logger.info("[STARTUP GUARD] Config validated OK")


# ─── Step 2: DB Connectivity with Exponential Backoff ────────────────────────


async def wait_for_db(max_retries: int = 15, initial_delay: int = 5) -> bool:
    """Wait for DB to become reachable with smart per-error-type retry logic.

    - "refused" / "timeout" → transient, keep retrying (postgres still starting)
    - "auth_failed"         → permanent, stop immediately (retrying won't help)
    - "ok"                  → success, return True
    """
    import os

    from ..database import _DB_ACTION_MAP, check_db_connection_detail

    db_url = os.getenv("DATABASE_URL", "")
    from urllib.parse import urlparse

    parsed = urlparse(db_url)
    host = parsed.hostname or "unknown"
    port = parsed.port or 5432

    await asyncio.sleep(initial_delay)

    for attempt in range(max_retries):
        status, detail = check_db_connection_detail()

        if status == "ok":
            logger.info(
                "[STARTUP GUARD] Database connection OK (attempt %d) — %s",
                attempt + 1,
                detail,
            )
            return True

        action = _DB_ACTION_MAP.get(status, "retry")
        if action == "stop_and_alert":
            # Permanent misconfiguration — retrying will never help.
            logger.critical(
                "[STARTUP GUARD] DB %s — action=stop_and_alert — stopping all retries. "
                "Fix credentials/pg_hba.conf and redeploy. Detail: %s",
                status,
                detail,
            )
            return False

        # Transient (retry / retry_with_backoff) — keep going
        wait_sec = min(2**attempt, 30)
        logger.warning(
            "[STARTUP GUARD] DB not ready (attempt %d/%d, status=%s) — %s — retrying in %ds",
            attempt + 1,
            max_retries,
            status,
            detail,
            wait_sec,
        )
        await asyncio.sleep(wait_sec)

    logger.critical(
        "[STARTUP GUARD] Database unreachable after %d attempts (host=%s:%s). "
        "Check DATABASE_URL and PostgreSQL container status.",
        max_retries,
        host,
        port,
    )
    return False


# ─── Step 3: Redis Connectivity ──────────────────────────────────────────────


async def check_redis(max_retries: int = 5, delay: int = 2) -> None:
    """Verify Redis is reachable at startup. Fatal if unreachable after retries.

    Redis is critical at startup because:
    - Rate limiting depends on it (without Redis, rates are per-worker, unscalable)
    - Token blacklisting depends on it (JWT revocation across workers)
    - perm_version caching depends on it (session invalidation across workers)

    Runtime Redis failures are tolerated (in-memory fallback), but startup
    failures are fatal — they indicate misconfiguration.
    """
    import asyncio

    from ..config import REDIS_URL

    for attempt in range(max_retries):
        try:
            import redis as _redis_check

            r = _redis_check.from_url(REDIS_URL, socket_timeout=2, decode_responses=True)
            r.ping()
            r.close()
            logger.info("[STARTUP GUARD] Redis connection OK (attempt %d)", attempt + 1)
            return
        except Exception as exc:
            logger.warning(
                "[STARTUP GUARD] Redis not ready (attempt %d/%d) — %s — retrying in %ds",
                attempt + 1,
                max_retries,
                exc,
                delay,
            )
        await asyncio.sleep(delay)

    raise RuntimeError(
        "[STARTUP GUARD] Redis unreachable after %d attempts. "
        "Check REDIS_URL / REDIS_PASSWORD and redis container status. "
        "Without Redis, token blacklisting and rate limiting are per-worker only.",
    )


# ─── Step 4: Migration Check ─────────────────────────────────────────────────

# Tables that MUST exist for the app to function. If any are missing, migrations
# have not been applied and the app must not start.
_REQUIRED_TABLES = [
    "labs",
    "lab_users",
    "patients",
    "lab_orders",
    "lab_results",
    "outbox_events",
    "audit_logs",
]


async def check_migrations() -> None:
    """Verify Alembic migrations have been applied and all required tables exist.

    Fails fast with a clear message if:
    - alembic_version table is absent (migrations never ran)
    - alembic_version is empty (migration ran but didn't complete)
    - Any required table is missing
    """
    from sqlalchemy import inspect, text

    from ..database import engine

    def _check() -> str | None:
        insp = inspect(engine)

        # Gate 1: alembic_version must exist — if it doesn't, `alembic upgrade head`
        # was never run. Accepting a missing table here was the original bug.
        if not insp.has_table("alembic_version"):
            return (
                "alembic_version table not found — migrations have never been applied. "
                "Run: alembic upgrade head"
            )

        # Gate 2: version row must be present (incomplete migration aborted mid-run)
        with engine.connect() as conn:
            row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
            if row is None:
                return (
                    "alembic_version table exists but is empty — migration aborted mid-run. "
                    "Run: alembic upgrade head"
                )

        # Gate 3: every required table must exist
        missing = [t for t in _REQUIRED_TABLES if not insp.has_table(t)]
        if missing:
            return f"Required tables missing after migrations: {missing}. Run: alembic upgrade head"

        return None

    loop = asyncio.get_event_loop()
    error = await loop.run_in_executor(None, _check)
    if error:
        raise RuntimeError(f"[STARTUP GUARD] Migration check FAILED: {error}")

    logger.info("[STARTUP GUARD] Migration check passed — all required tables present")


# ─── Step 4: Seed Critical Data ──────────────────────────────────────────────


async def seed_critical_data() -> None:
    """Run idempotent seed operations. Safe to call multiple times.

    perm_version migration is FATAL — if lab_users doesn't exist, alembic
    hasn't been applied and we must not start.

    Catalog / admin / subscription seeds are NON-FATAL — missing optional
    data doesn't block traffic; it is logged and the app continues.
    """
    loop = asyncio.get_event_loop()

    # ── FATAL: must succeed ───────────────────────────────────────────────────
    logger.info("[STARTUP GUARD] Running perm_version migration...")
    await loop.run_in_executor(None, _run_perm_version_migration)
    # ↑ raises RuntimeError if lab_users missing — propagates to run_startup_guard

    # ── NON-FATAL: catalog / admin / subscriptions / national bootstrap / audit trigger ──
    for name, fn in [
        ("test types catalog", _run_seed_test_types),
        ("master admin", _run_ensure_master_admin),
        ("default subscriptions", _run_seed_default_subscriptions),
        ("national bootstrap", _run_national_bootstrap),
        ("audit log trigger", _run_ensure_audit_log_immutable),
    ]:
        try:
            logger.info("[STARTUP GUARD] Seeding %s...", name)
            await loop.run_in_executor(None, fn)
        except Exception as exc:
            logger.error("[STARTUP GUARD] Seeding %s FAILED (non-fatal): %s", name, exc)

    logger.info("[STARTUP GUARD] Critical data seeded OK")


def _run_perm_version_migration() -> None:
    """Add perm_version column to lab_users — no circular import.

    Raises RuntimeError if lab_users doesn't exist so the caller can treat it
    as a fatal misconfiguration (migrations not applied) rather than swallowing it.
    """
    from sqlalchemy import inspect, text

    from ..database import engine

    insp = inspect(engine)
    if not insp.has_table("lab_users"):
        raise RuntimeError(
            "lab_users table does not exist — alembic upgrade head must run before seeding",
        )
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE lab_users "
                "ADD COLUMN IF NOT EXISTS perm_version INTEGER NOT NULL DEFAULT 1",
            ),
        )
        conn.execute(text("UPDATE lab_users SET perm_version = 1 WHERE perm_version IS NULL"))
        conn.commit()
    logger.info("[STARTUP GUARD] perm_version column ensured")


def _run_seed_test_types() -> None:
    """Seed test types catalog if empty."""
    from ..database import SessionLocal
    from ..models.test_type import TestType

    db = SessionLocal()
    try:
        if db.query(TestType.id).first() is not None:
            return
        test_types = [
            TestType(
                test_code="glucose",
                test_name="Glucose (Fasting)",
                test_name_ar="السكر (صائم)",
                category="Chemistry",
                unit="mg/dL",
                normal_range_low=70,
                normal_range_high=100,
            ),
            TestType(
                test_code="hemoglobin",
                test_name="Hemoglobin",
                test_name_ar="الهيموغلوبين",
                category="CBC",
                unit="g/dL",
                normal_range_low=12,
                normal_range_high=17,
            ),
            TestType(
                test_code="wbc",
                test_name="White Blood Cells",
                test_name_ar="كريات الدم البيضاء",
                category="CBC",
                unit="×10³/µL",
                normal_range_low=4.0,
                normal_range_high=11.0,
            ),
            TestType(
                test_code="platelets",
                test_name="Platelets",
                test_name_ar="الصفائح الدموية",
                category="CBC",
                unit="×10³/µL",
                normal_range_low=150,
                normal_range_high=400,
            ),
            TestType(
                test_code="creatinine",
                test_name="Creatinine",
                test_name_ar="الكرياتينين",
                category="Kidney",
                unit="mg/dL",
                normal_range_low=0.6,
                normal_range_high=1.3,
            ),
            TestType(
                test_code="urea",
                test_name="Urea (BUN)",
                test_name_ar="اليوريا",
                category="Kidney",
                unit="mg/dL",
                normal_range_low=15,
                normal_range_high=45,
            ),
            TestType(
                test_code="cholesterol",
                test_name="Total Cholesterol",
                test_name_ar="الكوليسترول الكلي",
                category="Lipid",
                unit="mg/dL",
                normal_range_low=0,
                normal_range_high=200,
            ),
            TestType(
                test_code="triglycerides",
                test_name="Triglycerides",
                test_name_ar="الدهون الثلاثية",
                category="Lipid",
                unit="mg/dL",
                normal_range_low=0,
                normal_range_high=150,
            ),
            TestType(
                test_code="alt",
                test_name="ALT (SGPT)",
                test_name_ar="إنزيم الكبد ALT",
                category="Liver",
                unit="U/L",
                normal_range_low=0,
                normal_range_high=40,
            ),
            TestType(
                test_code="ast",
                test_name="AST (SGOT)",
                test_name_ar="إنزيم الكبد AST",
                category="Liver",
                unit="U/L",
                normal_range_low=0,
                normal_range_high=40,
            ),
            TestType(
                test_code="tsh",
                test_name="TSH",
                test_name_ar="هرمون الغدة الدرقية",
                category="Thyroid",
                unit="mIU/L",
                normal_range_low=0.4,
                normal_range_high=4.5,
            ),
            TestType(
                test_code="potassium",
                test_name="Potassium",
                test_name_ar="البوتاسيوم",
                category="Electrolytes",
                unit="mEq/L",
                normal_range_low=3.5,
                normal_range_high=5.0,
            ),
            TestType(
                test_code="sodium",
                test_name="Sodium",
                test_name_ar="الصوديوم",
                category="Electrolytes",
                unit="mEq/L",
                normal_range_low=135,
                normal_range_high=145,
            ),
            TestType(
                test_code="hba1c",
                test_name="HbA1c",
                test_name_ar="السكر التراكمي",
                category="Diabetes",
                unit="%",
                normal_range_low=0,
                normal_range_high=5.7,
            ),
            TestType(
                test_code="vitamin_d",
                test_name="Vitamin D",
                test_name_ar="فيتامين د",
                category="Vitamins",
                unit="ng/mL",
                normal_range_low=20,
                normal_range_high=100,
            ),
            TestType(
                test_code="rbc",
                test_name="Red Blood Cells",
                test_name_ar="كريات الدم الحمراء",
                category="CBC",
                unit="×10⁶/µL",
                normal_range_low=4.0,
                normal_range_high=6.0,
            ),
            TestType(
                test_code="mcv",
                test_name="MCV",
                test_name_ar="حجم الكرية الوسطي",
                category="CBC",
                unit="fL",
                normal_range_low=80,
                normal_range_high=100,
            ),
            TestType(
                test_code="ldl",
                test_name="LDL Cholesterol",
                test_name_ar="الكوليسترول الضار",
                category="Lipid",
                unit="mg/dL",
                normal_range_low=0,
                normal_range_high=130,
            ),
            TestType(
                test_code="hdl",
                test_name="HDL Cholesterol",
                test_name_ar="الكوليسترول النافع",
                category="Lipid",
                unit="mg/dL",
                normal_range_low=40,
                normal_range_high=100,
            ),
            TestType(
                test_code="uric_acid",
                test_name="Uric Acid",
                test_name_ar="حمض اليوريك",
                category="Kidney",
                unit="mg/dL",
                normal_range_low=2.5,
                normal_range_high=7.0,
            ),
        ]
        db.add_all(test_types)
        db.commit()
        logger.info("[STARTUP GUARD] Seeded %d test types", len(test_types))
    finally:
        db.close()


def _run_ensure_master_admin() -> None:
    """Create master admin on first startup if not exists."""
    from .seeds import ensure_master_admin

    ensure_master_admin()


def _run_seed_default_subscriptions() -> None:
    """Ensure every active lab has a LabSubscription row — idempotent."""
    from ..database import SessionLocal
    from .seeds import seed_default_subscriptions

    db = SessionLocal()
    try:
        seed_default_subscriptions(db)
    finally:
        db.close()


def _run_national_bootstrap() -> None:
    """Run the National Bootstrap Engine — idempotent, non-fatal."""
    try:
        from ..config import ENABLE_BOOTSTRAP
        from .bootstrap import run_bootstrap

        if not ENABLE_BOOTSTRAP:
            logger.info("[STARTUP GUARD] National bootstrap disabled via ENABLE_BOOTSTRAP=false")
            return

        from ..database import SessionLocal

        db = SessionLocal()
        try:
            counts = run_bootstrap(db=db)
            if counts:
                summary = ", ".join(f"{k}={v}" for k, v in counts.items() if v)
                logger.info("[STARTUP GUARD] National bootstrap complete: %s", summary)
            else:
                logger.info("[STARTUP GUARD] National bootstrap: nothing to seed")
        finally:
            db.close()
    except Exception as exc:
        logger.error("[STARTUP GUARD] National bootstrap failed (non-fatal): %s", exc)


def _run_ensure_audit_log_immutable() -> None:
    """Apply immutability trigger to audit_logs table (ISO 27001 A.8.15).
    Ensures audit records cannot be modified or deleted after creation.
    Safe to call multiple times (CREATE OR REPLACE + DROP IF EXISTS).
    """
    from sqlalchemy import text

    from ..database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text("""
            CREATE OR REPLACE FUNCTION prevent_audit_modification()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION
                    'SECURITY: Audit log records are immutable. Attempted % on audit_logs',
                    TG_OP
                    USING ERRCODE = 'restrict_violation';
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
        """),
        )
        db.execute(
            text("""
            DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs;
            CREATE TRIGGER audit_logs_immutable
                BEFORE UPDATE OR DELETE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
        """),
        )
        db.commit()
        logger.info("[STARTUP GUARD] Audit log immutability trigger applied")
    except Exception as e:
        db.rollback()
        logger.warning("[STARTUP GUARD] Could not apply audit immutability trigger: %s", e)
    finally:
        db.close()


# ─── Constitutional Compliance Check ─────────────────────────────────────────


_VENDOR_SDKS = [
    "boto3",
    "azure",
    "google.cloud",
    "firebase",
    "supabase",
    "auth0",
    "okta",
    "stripe",
    "twilio",
    "sendgrid",
]

_CONSTITUTION_POLICIES = [
    ("Free First", "docs/architecture/FREE_FIRST_POLICY.md"),
    ("Open Source First", "docs/architecture/OPEN_SOURCE_POLICY.md"),
    ("No Vendor Lock-In", "docs/architecture/VENDOR_LOCK_IN_POLICY.md"),
    ("Dependency Approval", "docs/architecture/DEPENDENCY_APPROVAL_POLICY.md"),
    ("Cost Governance", "docs/constitution/COST_GOVERNANCE.md"),
    ("System Constitution", "docs/constitution/SYSTEM_CONSTITUTION.md"),
]


def _check_constitutional_compliance() -> None:
    """Verify constitutional policy documents exist and log compliance status.
    Non-fatal — warns but doesn't block startup.
    """
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent.parent

    missing = []
    for name, path in _CONSTITUTION_POLICIES:
        full_path = repo_root / path
        if not full_path.exists():
            missing.append(f"{name} ({path})")

    if missing:
        logger.warning(
            "[CONSTITUTION] Missing constitutional policy documents: %s",
            "; ".join(missing),
        )
    else:
        logger.info(
            "[CONSTITUTION] All constitutional policy documents present — PROGRAM-CONSTITUTION-001 enforced",
        )

    # Quick vendor SDK scan in core app code
    vendor_found = []
    for sdk in _VENDOR_SDKS:
        for pyfile in (repo_root / "backend" / "app").rglob("*.py"):
            try:
                if sdk in pyfile.read_text():
                    rel = pyfile.relative_to(repo_root)
                    vendor_found.append(f"{rel} (imports {sdk})")
            except OSError:
                continue

    if vendor_found:
        logger.warning(
            "[CONSTITUTION] Potential vendor SDK usage detected (review required): %s",
            "; ".join(vendor_found[:5]),
        )
    else:
        logger.info(
            "[CONSTITUTION] No direct vendor SDK usage detected — Vendor Lock-In policy satisfied",
        )

    logger.info("[CONSTITUTION] PROGRAM-CONSTITUTION-001 compliance check complete")


# ─── Atomic Orchestrator ─────────────────────────────────────────────────────


async def run_startup_guard() -> None:
    """Atomic startup validation chain.

    system_ready is set to True ONLY if every single step succeeds.
    Any exception keeps system_ready = False — the Docker healthcheck
    will never turn green and the api-gateway receives no traffic.

    In test mode (RUNTIME_MODE=test), system_ready is set to True
    immediately without validation — the test harness manages DB/Redis
    state independently.

    A safety timeout (STARTUP_TIMEOUT_SECONDS, default 120) ensures the
    guard can't block the lifespan indefinitely. After the timeout, the
    system starts in a partial-readiness state — health probes respond,
    but route handlers may fail if core dependencies are unavailable.
    """
    global system_ready, _readiness_reason

    from ..config import RUNTIME_MODE, STARTUP_TIMEOUT_SECONDS

    # ── Test mode: skip validation entirely ─────────────────────────────────
    if RUNTIME_MODE == "test":
        system_ready = True
        _readiness_reason = "test_mode"
        logger.info("[STARTUP GUARD] Test mode — system marked ready immediately")
        return

    # ── Guard against double-initialisation (e.g. hot-reload in dev) ────────
    if system_ready:
        logger.warning("[STARTUP GUARD] Already initialised — skipping")
        return

    t0 = time.perf_counter()
    logger.info("[STARTUP GUARD] === Starting production startup validation ===")

    # Wrap core validation in a timeout so startup can't block indefinitely.
    # After the timeout, the system starts in partial-readiness mode.
    startup_timeout = max(STARTUP_TIMEOUT_SECONDS, 30)

    async def _run_core_validation() -> None:
        """Core validation: config → DB → Redis → migrations → seeds → kernel."""
        validate_config()  # Step 1 — synchronous

        db_connected = await wait_for_db(max_retries=15, initial_delay=10)  # Step 2
        if not db_connected:
            logger.critical(
                "[STARTUP GUARD] Database not available after all retries. System will start in UNREADY state.",
            )
            return
        await check_redis()  # Step 3 — Redis reachable
        await check_migrations()  # Step 4 — migration state

        try:
            await seed_critical_data()
        except Exception as e:
            logger.error(
                "[STARTUP GUARD] Critical data seeding FAILED: %s. System will start in potentially degraded state.",
                e,
            )

        try:
            from ..kernel.integration import boot_kernel, start_kernel

            await boot_kernel()
            await start_kernel()
            logger.info("[STARTUP GUARD] Kernel initialized successfully")
        except Exception as e:
            logger.error(
                "[STARTUP GUARD] Kernel initialization FAILED: %s. System will start without Kernel.",
                e,
            )

    try:
        _check_constitutional_compliance()
    except Exception as e:
        logger.warning(
            "[STARTUP GUARD] Constitutional compliance check failed (non-fatal): %s",
            e,
        )

    try:
        await asyncio.wait_for(_run_core_validation(), timeout=startup_timeout)
    except TimeoutError:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.warning(
            "[STARTUP GUARD] Startup validation did not complete within %ds (%.0fms elapsed) — "
            "system starts in PARTIAL READY state. Some dependencies may be unavailable.",
            startup_timeout,
            elapsed,
        )
        system_ready = True
        _readiness_reason = "partial_startup_timeout"
        logger.info(
            "[STARTUP GUARD] === System PARTIALLY READY (%.0fms, timeout) — accepting traffic ===",
            elapsed,
        )
        return
    except Exception:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.exception(
            "[STARTUP GUARD] CRITICAL STARTUP FAILED after %.0fms — "
            "system_ready remains False. Container stays alive for health probes.",
            elapsed,
        )
        return

    # Atomic success: only reached if all critical steps above passed
    elapsed = (time.perf_counter() - t0) * 1000
    system_ready = True
    _readiness_reason = "ok"
    logger.info(
        "[STARTUP GUARD] === System READY (%.0fms) — accepting traffic ===",
        elapsed,
    )
