import os
import time
import uuid
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .database import Base, engine, check_db_connection, get_pool_status
from .config import (
    APP_NAME, APP_VERSION, IS_PRODUCTION, ENABLE_API_DOCS,
    MAX_REQUEST_BODY_MB, PLATFORM_NAME_AR,
)

# Configure structured logging
logging.basicConfig(
    level=logging.WARNING if IS_PRODUCTION else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gula")

# Import all models so they are registered with Base
from .models import Lab, LabUser, User, Patient, TestType, LabOrder, LabResult, AuditLog, Sample, QualityControl
from .models.outbox import OutboxEvent  # register OutboxEvent with Base metadata

# Schema management: create_all is safe and idempotent (checkfirst=True by default).
# It creates missing tables without touching existing data.
# Production Alembic migrations can be added later; until then this is the safe path.
Base.metadata.create_all(bind=engine)

# ─── API Documentation ─────────────────────────────────────────────────────
# Enabled by default in non-production, or when ENABLE_API_DOCS=true in .env
# Government testers and mobile developers need the docs
_docs_url = None
_redoc_url = None
if not IS_PRODUCTION or ENABLE_API_DOCS:
    _docs_url = "/docs"
    _redoc_url = "/redoc"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    default_response_class=ORJSONResponse,
    description=(
        "**GULA** - منصة غولا الصحية الذكية للمختبرات\n\n"
        "Smart Health Platform for Medical Laboratories in Iraq.\n\n"
        "**Authentication:** Use `Bearer <token>` header (obtain token from `POST /login`).\n\n"
        "**Mobile:** Refresh tokens available via `POST /auth/refresh`.\n\n"
        "**Version:** " + APP_VERSION
    ),
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    contact={
        "name": "GULA Platform Support",
        "url": "https://gula-platform.org",
        "email": "support@gula-platform.org",
    },
    license_info={
        "name": "Proprietary - Ministry of Health Iraq Compliant",
    },
)


# ===== GLOBAL ERROR HANDLER =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors - return friendly JSON instead of 500 stack trace."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("[%s] %s %s: %s", request_id, request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong. Please try again.",
            "detail_ar": "حدث خطأ. يرجى المحاولة مرة أخرى.",
            "request_id": request_id,
        },
    )


# ===== REQUEST BODY SIZE LIMIT =====
class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies to prevent DoS attacks."""
    def __init__(self, app, max_size_mb: int = 10):
        super().__init__(app)
        self._max_bytes = max_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large (max {MAX_REQUEST_BODY_MB}MB)",
                    "detail_ar": f"حجم البيانات أكبر من المسموح به ({MAX_REQUEST_BODY_MB} ميغابايت)",
                },
            )
        return await call_next(request)


app.add_middleware(MaxBodySizeMiddleware, max_size_mb=MAX_REQUEST_BODY_MB)


# ===== REQUEST ID MIDDLEWARE =====
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign a unique ID to every request for tracing."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)


# ===== CORS =====
# Allow configured origins + mobile app schemes
_allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]
if not _allowed_origins:
    _allowed_origins = [
        "https://gula-platform.org",
        "http://gula-platform.org",
    ]
    if os.getenv("ENV", "production") in ("development", "test"):
        _allowed_origins += ["http://localhost:8080", "http://localhost:80", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Device-ID", "X-App-Version", "Idempotency-Key"],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-API-Version"],
)


# ===== REQUEST TIMING & LOGGING MIDDLEWARE =====
class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log request timing for performance monitoring."""
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Log slow requests (>2 seconds)
        if elapsed_ms > 2000:
            logger.warning(
                "SLOW REQUEST [%s]: %s %s took %.0fms (status=%d)",
                getattr(request.state, "request_id", "?"),
                request.method, request.url.path, elapsed_ms, response.status_code,
            )

        response.headers["X-Response-Time"] = f"{elapsed_ms:.0f}ms"
        response.headers["X-API-Version"] = APP_VERSION
        return response


app.add_middleware(RequestTimingMiddleware)


# ===== SECURITY HEADERS MIDDLEWARE =====
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Skip security headers for static assets (handled by nginx in production)
        path = request.url.path
        if path.startswith("/assets/") or path.endswith((".css", ".js", ".png", ".ico")):
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' https://gula-platform.org; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ===== READINESS ENFORCEMENT MIDDLEWARE =====
# Explicit whitelist — paths that are ALWAYS reachable regardless of readiness.
# Do NOT use startswith("/health") — that could be accidentally bypassed by
# adding new /health-adjacent routes later.
_ALWAYS_ALLOWED_PATHS: frozenset[str] = frozenset({
    "/health",
    "/health/ready",
    "/health/live",
    "/health/status",  # diagnostic — always visible so you can see WHY startup failed
})


class ReadinessMiddleware(BaseHTTPMiddleware):
    """Reject all non-whitelisted requests with 503 until startup guard passes.

    Uses an explicit path whitelist (not prefix matching) so new routes
    cannot accidentally bypass the readiness check.
    """

    async def dispatch(self, request: Request, call_next):
        from .core.startup_guard import system_ready
        if not system_ready and request.url.path not in _ALWAYS_ALLOWED_PATHS:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service is starting up. Please retry in a moment.",
                    "detail_ar": "الخدمة تبدأ التشغيل. يرجى المحاولة بعد لحظة.",
                },
            )
        return await call_next(request)


app.add_middleware(ReadinessMiddleware)


# ===== DEGRADED MODE MIDDLEWARE =====
# Rejects write operations when DB circuit breaker opens (post-startup failure).
# Works in conjunction with RecoveryWorker which probes and auto-heals.
from .core.self_healing import DegradedModeMiddleware
app.add_middleware(DegradedModeMiddleware)


# ===== CONCURRENCY LIMIT (BACKPRESSURE) MIDDLEWARE =====
# Sheds load when too many requests are simultaneously in-flight.
# Each uvicorn worker has its own counter (per-process, not shared across workers).
# Health-check paths AND clinical write paths are always exempt so patient care
# operations can never be shed even under extreme load.
_MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_REQUESTS", "200"))

# Clinical write operations that must NEVER be rejected by the backpressure limiter.
# These paths modify patient records or results — blocking them risks patient harm.
_CRITICAL_PATH_PREFIXES: tuple = (
    "/results",       # entering / updating lab results
    "/orders",        # creating orders, adding results, validating
    "/samples",       # sample lifecycle (collection, processing)
    "/critical-alerts",  # critical value notifications
)


def _is_critical_write(method: str, path: str) -> bool:
    return method in ("POST", "PUT", "PATCH") and any(
        path.startswith(p) for p in _CRITICAL_PATH_PREFIXES
    )


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Return 503 immediately when the server is already handling too many requests.

    Clinical write operations (results, orders, samples, critical alerts) are
    always allowed through regardless of the current load level.
    """
    _active: int = 0

    def __init__(self, app, max_concurrent: int = _MAX_CONCURRENT):
        super().__init__(app)
        self._max = max_concurrent

    async def dispatch(self, request: Request, call_next):
        # Health checks — always allowed
        if request.url.path in _ALWAYS_ALLOWED_PATHS:
            return await call_next(request)
        # Critical clinical writes — always allowed (patient safety)
        if _is_critical_write(request.method, request.url.path):
            return await call_next(request)
        if ConcurrencyLimitMiddleware._active >= self._max:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Server busy — try again shortly",
                    "detail_ar": "الخادم مشغول — حاول مرة أخرى بعد لحظة",
                    "retry_after": 5,
                },
                headers={"Retry-After": "5"},
            )
        ConcurrencyLimitMiddleware._active += 1
        try:
            return await call_next(request)
        finally:
            ConcurrencyLimitMiddleware._active -= 1


app.add_middleware(ConcurrencyLimitMiddleware)

# ===== ROUTES =====
from .routes import login, register, patients, results, dashboard, labs
from .routes import identity, notifications, ehr, security
from .routes import national_identity, insurance, device_results
from .routes import qr, id_scan, admin, samples
from .routes import quality_control, critical_alerts, batch
from .routes import mobile, compliance
from .routes import setup, metrics
from .routes import ai as ai_routes

# Core routes
app.include_router(login.router)
app.include_router(register.router)
app.include_router(setup.router)
app.include_router(metrics.router)
app.include_router(patients.router)
app.include_router(results.router)
app.include_router(dashboard.router)
app.include_router(labs.router)
app.include_router(samples.router)

# Feature routes
app.include_router(qr.router)
app.include_router(id_scan.router)
app.include_router(identity.router)
app.include_router(notifications.router)
app.include_router(ehr.router)
app.include_router(security.router)
app.include_router(device_results.router)

# Advanced lab features
app.include_router(quality_control.router)
app.include_router(critical_alerts.router)
app.include_router(batch.router)

# Admin routes
app.include_router(admin.router)

# Mobile API routes (Android + iOS)
app.include_router(mobile.router)

# Government compliance routes
app.include_router(compliance.router)

# Legacy routes (kept for API compatibility)
app.include_router(national_identity.router)
app.include_router(insurance.router)

# AI Safety Layer
app.include_router(ai_routes.router)


# ===== STARTUP WARMUP =====
@app.on_event("startup")
async def start_background_workers():
    """Launch background workers for outbox delivery and self-healing recovery."""
    import asyncio
    from .services.outbox_service import OutboxWorker
    from .core.self_healing import RecoveryWorker

    asyncio.create_task(OutboxWorker.background_loop())
    logger.info("Outbox worker started")

    asyncio.create_task(RecoveryWorker.background_loop())
    logger.info("Recovery worker started")


@app.on_event("startup")
async def warmup():
    """Pre-load hot-path modules so first real request is fast."""
    import time as _t
    t0 = _t.perf_counter()
    try:
        # Resolve deferred import inside get_flag → check_critical
        from .routes.critical_alerts import check_critical
        from .services.interpretation import interpret_result, get_flag
        # Warm function caches
        check_critical("Potassium", 4.0)
        interpret_result("glucose", 85, 70, 100)
        get_flag(85, 70, 100, "Glucose")
        elapsed = (_t.perf_counter() - t0) * 1000
        logger.info("Startup warmup complete in %.0fms", elapsed)
    except Exception as exc:
        logger.warning("Startup warmup skipped: %s", exc)


# ===== HEALTH & STATUS =====
@app.get("/health", tags=["system"])
def health():
    """
    Liveness probe — always returns 200 if the process is alive.
    Includes circuit breaker state and pool info for observability.
    """
    from .core.self_healing import health as sys_health
    from .core.startup_guard import system_ready
    db_ok = check_db_connection()
    pool = get_pool_status()
    return {
        "status": "healthy" if db_ok else "degraded",
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "system_ready": system_ready,
        "database": "connected" if db_ok else "disconnected",
        "degraded_mode": sys_health.degraded,
        "circuits": sys_health.to_dict()["circuits"],
        "pool": pool,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready", tags=["system"])
def readiness():
    """Hybrid readiness probe — startup completed AND services still alive.

    Returns 200 only when:
      1. Startup guard completed successfully (all steps passed), AND
      2. Database is currently reachable, AND
      3. Redis cache is currently reachable.

    If DB or Redis fail after startup, this probe turns 503 again — the
    Docker healthcheck will detect it and trigger a container restart.
    """
    from .core.startup_guard import is_system_ready
    ready, reason = is_system_ready()
    if not ready:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": reason},
        )
    return {"status": "ready"}


@app.get("/health/live", tags=["system"])
def liveness():
    """Kubernetes-style liveness probe - always returns 200 if process is alive."""
    return {"status": "alive", "version": APP_VERSION}


@app.get("/health/status", tags=["system"])
def health_status():
    """
    Full diagnostic status — shows exactly why the system is or isn't ready.
    Useful for debugging startup failures without needing server access.
    Always returns 200 — check 'ready' field for actual state.
    """
    from .core.startup_guard import system_ready, is_system_ready
    from .core.self_healing import health as sys_health

    # Individual component checks
    db_ok = False
    db_error = None
    try:
        db_ok = check_db_connection()
    except Exception as e:
        db_error = str(e)

    redis_ok = False
    redis_error = None
    try:
        from .security.redis_client import cache as _redis
        _redis.set("_status_probe", "1", ex=10)
        redis_ok = True
    except Exception as e:
        redis_error = str(e)

    ready, reason = is_system_ready()
    pool = get_pool_status()
    sys_h = sys_health.to_dict()

    return {
        "ready": ready,
        "reason": reason,
        "system_ready_flag": system_ready,
        "database": {
            "connected": db_ok,
            "error": db_error,
            "pool": pool,
        },
        "redis": {
            "connected": redis_ok,
            "error": redis_error,
        },
        "circuits": sys_h.get("circuits", {}),
        "degraded_mode": sys_h.get("degraded", False),
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }



# ===== PUBLIC ENDPOINTS =====
_test_types_cache: dict = {"data": None, "at": 0.0}

@app.get("/test-types", tags=["system"])
def list_test_types():
    """
    Returns all available test types and their reference ranges.
    Cached in-memory for 5 minutes to reduce database load.
    """
    import time
    cache = _test_types_cache
    if cache["data"] is not None and (time.time() - cache["at"]) < 300:
        return cache["data"]

    from .database import SessionLocal
    from .models.test_type import TestType
    db = SessionLocal()
    try:
        types = db.query(TestType).order_by(TestType.category, TestType.test_name).all()
        result = [
            {
                "id": t.id,
                "code": t.test_code,
                "name": t.test_name,
                "name_ar": t.test_name_ar,
                "category": t.category,
                "unit": t.unit,
                "normal_low": t.normal_range_low,
                "normal_high": t.normal_range_high,
            }
            for t in types
        ]
        cache["data"] = result
        cache["at"] = time.time()
        return result
    finally:
        db.close()


# ===== STARTUP & SHUTDOWN =====
@app.on_event("startup")
async def on_startup():
    """Run the production startup guard then mark the system ready."""
    from .core.startup_guard import run_startup_guard
    logger.info("GULA Platform %s starting up...", APP_VERSION)
    await run_startup_guard()
    # system_ready flag is set to True inside run_startup_guard on success


@app.on_event("shutdown")
def on_shutdown():
    """Graceful shutdown - close database connections."""
    logger.info("GULA Platform shutting down gracefully...")
    engine.dispose()
    logger.info("Database connections closed")


def _migrate_perm_version():
    """Add perm_version column to lab_users if it does not exist (safe idempotent migration)."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # Step 1: add the column if absent
            conn.execute(text(
                "ALTER TABLE lab_users "
                "ADD COLUMN IF NOT EXISTS perm_version INTEGER NOT NULL DEFAULT 1"
            ))
            # Step 2: back-fill any NULL values left by a partial previous migration
            conn.execute(text(
                "UPDATE lab_users SET perm_version = 1 WHERE perm_version IS NULL"
            ))
            conn.commit()
        logger.info("perm_version column ensured on lab_users")
    except Exception as exc:
        logger.error("perm_version migration FAILED: %s — login will fail until resolved", exc)
        raise  # re-raise so startup logs clearly show the error


def _seed_test_types():
    """Seed test types catalog if empty (fast: single COUNT check)."""
    from .database import SessionLocal
    from .models.test_type import TestType

    db = SessionLocal()
    try:
        # Fast existence check - avoids full count
        if db.query(TestType.id).first() is not None:
            return
        test_types = [
            TestType(test_code="glucose", test_name="Glucose (Fasting)", test_name_ar="السكر (صائم)", category="Chemistry", unit="mg/dL", normal_range_low=70, normal_range_high=100),
            TestType(test_code="hemoglobin", test_name="Hemoglobin", test_name_ar="الهيموغلوبين", category="CBC", unit="g/dL", normal_range_low=12, normal_range_high=17),
            TestType(test_code="wbc", test_name="White Blood Cells", test_name_ar="كريات الدم البيضاء", category="CBC", unit="×10³/µL", normal_range_low=4.0, normal_range_high=11.0),
            TestType(test_code="platelets", test_name="Platelets", test_name_ar="الصفائح الدموية", category="CBC", unit="×10³/µL", normal_range_low=150, normal_range_high=400),
            TestType(test_code="creatinine", test_name="Creatinine", test_name_ar="الكرياتينين", category="Kidney", unit="mg/dL", normal_range_low=0.6, normal_range_high=1.3),
            TestType(test_code="urea", test_name="Urea (BUN)", test_name_ar="اليوريا", category="Kidney", unit="mg/dL", normal_range_low=15, normal_range_high=45),
            TestType(test_code="cholesterol", test_name="Total Cholesterol", test_name_ar="الكوليسترول الكلي", category="Lipid", unit="mg/dL", normal_range_low=0, normal_range_high=200),
            TestType(test_code="triglycerides", test_name="Triglycerides", test_name_ar="الدهون الثلاثية", category="Lipid", unit="mg/dL", normal_range_low=0, normal_range_high=150),
            TestType(test_code="alt", test_name="ALT (SGPT)", test_name_ar="إنزيم الكبد ALT", category="Liver", unit="U/L", normal_range_low=0, normal_range_high=40),
            TestType(test_code="ast", test_name="AST (SGOT)", test_name_ar="إنزيم الكبد AST", category="Liver", unit="U/L", normal_range_low=0, normal_range_high=40),
            TestType(test_code="tsh", test_name="TSH", test_name_ar="هرمون الغدة الدرقية", category="Thyroid", unit="mIU/L", normal_range_low=0.4, normal_range_high=4.5),
            TestType(test_code="potassium", test_name="Potassium", test_name_ar="البوتاسيوم", category="Electrolytes", unit="mEq/L", normal_range_low=3.5, normal_range_high=5.0),
            TestType(test_code="sodium", test_name="Sodium", test_name_ar="الصوديوم", category="Electrolytes", unit="mEq/L", normal_range_low=135, normal_range_high=145),
            TestType(test_code="hba1c", test_name="HbA1c", test_name_ar="السكر التراكمي", category="Diabetes", unit="%", normal_range_low=0, normal_range_high=5.7),
            TestType(test_code="vitamin_d", test_name="Vitamin D", test_name_ar="فيتامين د", category="Vitamins", unit="ng/mL", normal_range_low=20, normal_range_high=100),
            TestType(test_code="rbc", test_name="Red Blood Cells", test_name_ar="كريات الدم الحمراء", category="CBC", unit="×10⁶/µL", normal_range_low=4.0, normal_range_high=6.0),
            TestType(test_code="mcv", test_name="MCV", test_name_ar="حجم الكرية الوسطي", category="CBC", unit="fL", normal_range_low=80, normal_range_high=100),
            TestType(test_code="ldl", test_name="LDL Cholesterol", test_name_ar="الكوليسترول الضار", category="Lipid", unit="mg/dL", normal_range_low=0, normal_range_high=130),
            TestType(test_code="hdl", test_name="HDL Cholesterol", test_name_ar="الكوليسترول النافع", category="Lipid", unit="mg/dL", normal_range_low=40, normal_range_high=100),
            TestType(test_code="uric_acid", test_name="Uric Acid", test_name_ar="حمض اليوريك", category="Kidney", unit="mg/dL", normal_range_low=2.5, normal_range_high=7.0),
        ]
        db.add_all(test_types)
        db.commit()
        logger.info(f"Seeded {len(test_types)} test types")
    finally:
        db.close()


def _ensure_master_admin():
    """Create master admin on first startup if not exists."""
    from .routes.admin import ensure_master_admin
    ensure_master_admin()
