import asyncio
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager, suppress
from datetime import datetime

from app._compat import UTC

# Ensure canonical shared library is on the Python path
_SHARED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "shared"
)
if os.path.isdir(_SHARED_PATH) and _SHARED_PATH not in sys.path:
    sys.path.insert(0, os.path.dirname(_SHARED_PATH))  # parent dir so 'import shared' works

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import (
    APP_NAME,
    APP_VERSION,
    ENABLE_API_DOCS,
    IS_PRODUCTION,
    MAX_REQUEST_BODY_MB,
    PLATFORM_NAME_AR,
    RUNTIME_MODE,
    background_tasks_enabled,
)

# Configure structured JSON logging (production) or text logging (dev)
from .core.logging_config import bind_log_context, configure_logging
from .database import check_db_connection, engine, get_pool_status

configure_logging(
    is_production=IS_PRODUCTION,
    log_level="INFO",
)
logger = logging.getLogger("gula")

# ── Optional Sentry error tracking ─────────────────────────────────────────
# Activates only when SENTRY_DSN is set in the environment.
_SENTRY_DSN = os.getenv("SENTRY_DSN")
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "production"),
            release=os.getenv("APP_VERSION", "unknown"),
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR),
            ],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.05")),
        )
        logger.info(
            "Sentry error tracking initialized (env=%s)", os.getenv("ENVIRONMENT", "production")
        )
    except ImportError:
        logger.warning("SENTRY_DSN set but sentry-sdk not installed; skipping")

# Import all models so they are registered with Base.metadata (needed for create_all + alembic)
from .models import (  # noqa: F401, E402
    AuditLog,
    Lab,
    LabOrder,
    LabResult,
    LabUser,
    Patient,
    QualityControl,
    Sample,
    TestType,
    User,
)
from .models.outbox import OutboxEvent  # noqa: E402  register OutboxEvent with Base metadata

# Schema management: create_all is safe and idempotent (checkfirst=True by default).
# It creates missing tables without touching existing data.
# Production Alembic migrations can be added later; until then this is the safe path.


# ─── API Documentation ─────────────────────────────────────────────────────
# Enabled by default in non-production, or when ENABLE_API_DOCS=true in .env
# Government testers and mobile developers need the docs
_docs_url = None
_redoc_url = None
if not IS_PRODUCTION or ENABLE_API_DOCS:
    _docs_url = "/docs"
    _redoc_url = "/redoc"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Unified startup / shutdown lifecycle (replaces deprecated @app.on_event)."""
    # ── startup ──────────────────────────────────────────────────────────────
    # Functions are defined later in this module; Python resolves them at call
    # time (after full module load), so forward references are safe here.
    await start_background_workers()
    await warmup()
    from .core.startup_guard import run_startup_guard

    logger.info("GULA Platform %s starting up...", APP_VERSION)
    await run_startup_guard()

    # ── kernel warmup (kernel is booted inside run_startup_guard Step 5) ─────
    try:
        from .kernel.integration import warmup_kernel

        await warmup_kernel()
    except Exception as exc:
        logger.warning("Kernel warmup skipped: %s", exc)

    yield  # ← application running

    # ── shutdown ─────────────────────────────────────────────────────────────
    logger.info(
        "GULA Platform shutting down — cancelling %d background task(s)...",
        len(_bg_tasks),
    )
    from .kernel.integration import stop_kernel

    try:
        await stop_kernel()
        logger.info("Kernel stopped")
    except Exception as exc:
        logger.error("Kernel shutdown error: %s", exc)

    for task in list(_bg_tasks):
        task.cancel()
    if _bg_tasks:
        await asyncio.gather(*list(_bg_tasks), return_exceptions=True)
    logger.info("All background tasks stopped")
    engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=_lifespan,
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
    from .core.startup_guard import is_system_ready

    ready, reason = is_system_ready()

    if not ready and IS_PRODUCTION:
        logger.error(
            "[%s] Unhandled exception during unready state: %s %s (Reason: %s)",
            request_id,
            request.method,
            request.url.path,
            reason,
        )
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Service Unavailable: System not ready. Reason: {reason}",
                "detail_ar": f"الخدمة غير متاحة: النظام غير جاهز. السبب: {reason}",
                "request_id": request_id,
            },
        )
    if IS_PRODUCTION:
        logger.error(
            "[%s] Unhandled exception: %s %s", request_id, request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "detail_ar": "حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.",
                "request_id": request_id,
            },
        )
    # In development, log full exception and return more details
    logger.exception("[%s] %s %s: %s", request_id, request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "detail_ar": "حدث خطأ: " + str(exc),
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
    """Assign a unique ID to every request for tracing and bind it to the log context.

    Also sets DB correlation context vars so any DB failure during this request
    is automatically tagged with request_id + endpoint in the structured log.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        bind_log_context(request_id=request_id)

        # Inject into DB correlation context vars (read by check_db_connection_detail)
        from .database import _endpoint_var, _request_id_var

        rid_token = _request_id_var.set(request_id)
        ep_token = _endpoint_var.set(request.url.path)
        try:
            response = await call_next(request)
        finally:
            _request_id_var.reset(rid_token)
            _endpoint_var.reset(ep_token)

        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)


# ===== DOCS PROTECTION =====
# /docs and /redoc are protected in production — accessible only to admins/master_admins.
# This prevents unauthenticated exposure of API internals to the public internet.
if IS_PRODUCTION and ENABLE_API_DOCS:
    from .security.auth import decode_token

    class DocsAuthMiddleware(BaseHTTPMiddleware):
        """Require valid admin JWT to access /docs and /redoc in production."""

        _PROTECTED = {"/docs", "/redoc", "/openapi.json"}

        async def dispatch(self, request: Request, call_next):
            if request.url.path not in self._PROTECTED:
                return await call_next(request)

            # Accept token from cookie or Authorization header
            token = request.cookies.get("access_token")
            if not token:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]

            if not token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required to access API documentation"},
                )

            payload = decode_token(token)
            if not payload or payload.get("role") not in ("admin", "master_admin"):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Admin access required for API documentation"},
                )

            return await call_next(request)

    app.add_middleware(DocsAuthMiddleware)


# ===== CORS =====
# Allow configured origins + mobile app schemes
_allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]
if not _allowed_origins:
    # Production: HTTPS only
    _allowed_origins = [
        "https://gula-platform.org",
    ]
    if os.getenv("ENV", "production") in ("development", "test"):
        _allowed_origins += [
            "http://localhost:8080",
            "http://localhost:80",
            "http://localhost:3000",
            "http://localhost:5173",  # Vite dev server
            "http://localhost:4173",  # Vite preview
            "http://localhost:8000",  # FastAPI self (Swagger UI)
            # Frontend design tools — used for UI prototyping against this API.
            # Google AI Studio and Claude design send requests from these origins.
            "https://aistudio.google.com",
            "https://claude.ai",
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Device-ID",
        "X-App-Version",
        "Idempotency-Key",
    ],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-API-Version"],
)


# ===== REQUEST TIMING & LOGGING MIDDLEWARE =====
# Paths excluded from per-request access logs to avoid health-check noise.
_SILENT_PATHS: frozenset[str] = frozenset({"/health", "/health/ready", "/health/live"})


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Emit a structured access-log line (path, latency_ms, status) per request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        status = response.status_code
        path = request.url.path

        if path not in _SILENT_PATHS:
            log_fn = logger.warning if elapsed_ms > 2000 or status >= 500 else logger.info
            log_fn(
                "%s %s %d",
                request.method,
                path,
                status,
                extra={"path": path, "latency_ms": elapsed_ms, "status": status},
            )

        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
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
        # Health probes are scraped by Prometheus every 15s — a short public
        # cache reduces backend pressure without hiding state changes.
        if request.method == "GET" and request.url.path in _ALWAYS_ALLOWED_PATHS:
            response.headers["Cache-Control"] = "public, max-age=10, stale-while-revalidate=5"
        else:
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
_ALWAYS_ALLOWED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/health/live",
        "/health/status",  # diagnostic — always visible so you can see WHY startup failed
        "/health/deep",  # deep diagnostics — always accessible for monitoring
        "/health/kernel",  # kernel health — always visible
    }
)


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
from .core.self_healing import DegradedModeMiddleware  # noqa: E402

app.add_middleware(DegradedModeMiddleware)


# ===== KERNEL MIDDLEWARE =====
# Attaches kernel context to every request and enforces kernel-first dependency.
# Runs after degraded-mode so it can observe system health state.
class KernelMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        from .kernel.integration import kernel_middleware

        return await kernel_middleware(request, call_next)


app.add_middleware(KernelMiddleware)


# ===== CONCURRENCY LIMIT (BACKPRESSURE) MIDDLEWARE =====
# Sheds load when too many requests are simultaneously in-flight.
# Each uvicorn worker has its own counter (per-process, not shared across workers).
# Health-check paths AND clinical write paths are always exempt so patient care
# operations can never be shed even under extreme load.
_MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_REQUESTS", "200"))

# Clinical write operations that must NEVER be rejected by the backpressure limiter.
# These paths modify patient records or results — blocking them risks patient harm.
_CRITICAL_PATH_PREFIXES: tuple = (
    "/results",  # entering / updating lab results
    "/orders",  # creating orders, adding results, validating
    "/samples",  # sample lifecycle (collection, processing)
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
    _instance: "ConcurrencyLimitMiddleware | None" = None

    def __init__(self, app, max_concurrent: int = _MAX_CONCURRENT):
        super().__init__(app)
        self._max = max_concurrent
        # Store the instance reference for adaptive concurrency adjustment
        ConcurrencyLimitMiddleware._instance = self

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
from .models.subscription import (  # noqa: F401, E402  register with Base
    FeatureFlag,
    LabSubscription,
    UpgradeDemandScore,
    UpgradeRequest,
)
from .routes import (  # noqa: E402
    admin,
    batch,
    compliance,
    critical_alerts,
    dashboard,
    device_results,
    ehr,
    id_scan,
    identity,
    insurance,
    labs,
    login,
    metrics,
    mobile,
    national_identity,
    notifications,
    patients,
    qr,
    quality_control,
    register,
    results,
    samples,
    security,
    setup,
    test_results,
)
from .routes import ai as ai_routes  # noqa: E402
from .routes import citizen_portal as citizen_portal_routes  # noqa: E402
from .routes import optimizer as optimizer_routes  # noqa: E402
from .routes import tiers as tiers_routes  # noqa: E402

# Core routes
app.include_router(login.router)
app.include_router(register.router)
app.include_router(setup.router)
app.include_router(metrics.router)
app.include_router(patients.router)
app.include_router(results.router)
app.include_router(test_results.router)
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

# Subscription tier management
app.include_router(tiers_routes.router)

# Citizen / patient portal
app.include_router(citizen_portal_routes.router)

# Claims / Insurance module
from .routes import claims as claims_routes  # noqa: E402

app.include_router(claims_routes.router)

# Legacy routes (kept for API compatibility)
app.include_router(national_identity.router)
app.include_router(insurance.router)

# AI Safety Layer
app.include_router(ai_routes.router)

# AI System Optimizer (admin-only, read-only performance monitoring)
app.include_router(optimizer_routes.router)

# Statistics & Trends — cached time-series analytics
from .routes import stats as stats_routes  # noqa: E402

app.include_router(stats_routes.router)

# Master Patient Index — national-layer identity (canonical citizen registry)
from .services.mpi import router as mpi_router  # noqa: E402

app.include_router(mpi_router)

# Consent layer — governing access control for reads of citizen data
from .routes import consent as consent_routes  # noqa: E402

app.include_router(consent_routes.router)

# External integrations health + probe (gov NID, insurance, residency, Cloudflare)
from .routes import integrations as integrations_routes  # noqa: E402

app.include_router(integrations_routes.router)

# Edge AI Platform — managed edge nodes (device registry, task scheduler, model governance)
from .routes import edge as edge_routes  # noqa: E402

app.include_router(edge_routes.router)

# Digital Patient Card — QR-backed identity card + full-history aggregator
from .routes import patient_card as patient_card_routes  # noqa: E402

app.include_router(patient_card_routes.router)
from .models.edge import (  # noqa: E402, F401  register edge tables with Base metadata
    EdgeDevice,
    EdgeEvent,
    EdgeModel,
    EdgeModelAssignment,
    EdgePolicy,
    EdgeTask,
    EdgeTelemetry,
)

# AI Interaction Dataset (Phase 3 + 4) — operational medical-intelligence
# collection pipeline introduced for the 2026-05-11 production launch.
# All endpoints are flag-gated (ENABLE_AI_DATASET); registration is
# unconditional so /api/ai/dataset/status remains visible for operators.
from .routes import ai_telemetry as ai_telemetry_routes  # noqa: E402

app.include_router(ai_telemetry_routes.router)

# ===== KERNEL MANAGEMENT ROUTES =====
# The Kernel is the permanent runtime foundation. These routes expose kernel
# internals for observability without requiring direct process access.
from .kernel import routes as kernel_routes  # noqa: E402

app.include_router(kernel_routes.router)
from .models.ai_interaction import (  # noqa: E402, F401  register with Base metadata
    AIFeedback,
    AIInteraction,
    AIRetrievalRef,
    AIUnresolvedQuestion,
    MedicalTerminologyNormalized,
)


# ===== HEALTH ALERT WATCHDOG =====
async def _health_alert_loop():
    """Background coroutine: comprehensive health monitoring with thresholds.

    Checks every HEALTH_ALERT_interval_SECONDS (default 60s).
    When grade is RED, retries every 10s for fast recovery detection.
    Fires webhook on EVERY grade change (GREEN↔YELLOW↔RED) + periodic RED reminder.

    Thresholds:
      RED    — DB down OR Redis down
      YELLOW — DB slow (>200ms) OR Redis slow (>50ms) OR memory >600MB
               OR queue backlog >100 OR degraded mode
      GREEN  — all clear

    Set ALERT_webhook_URL in .env (Telegram, Discord, Slack, or any HTTP POST sink).
    """
    import asyncio as _aio
    import os
    import time as _t

    _interval = int(os.getenv("HEALTH_ALERT_INTERVAL_SECONDS", "60"))
    _retry_fast = 10  # seconds between checks when in RED state
    _remind_secs = 300  # re-alert every 5 min if still RED
    _webhook = os.getenv("ALERT_WEBHOOK_URL", "")

    _prev_grade = "GREEN"
    _red_since = 0.0  # monotonic timestamp when RED started
    _last_alert = 0.0  # monotonic timestamp of last webhook send

    await _aio.sleep(30)  # Let startup complete before first check

    while True:
        try:
            from .core.self_healing import health as _sh
            from .database import check_db_connection as _db_check
            from .security.redis_client import cache as _r

            # ── Component checks (run blocking ops in executor) ──────────
            loop = _aio.get_event_loop()

            t0 = _t.perf_counter()
            db_ok = await loop.run_in_executor(None, _db_check)
            db_ms = round((_t.perf_counter() - t0) * 1000, 1)

            red_ok, red_ms = False, -1.0
            try:
                t0 = _t.perf_counter()
                await loop.run_in_executor(None, _r.ping)
                red_ms = round((_t.perf_counter() - t0) * 1000, 1)
                red_ok = True
            except Exception:
                pass

            def _read_rss() -> float:
                try:
                    with open("/proc/self/status") as _f:
                        for line in _f:
                            if line.startswith("VmRSS:"):
                                return round(int(line.split()[1]) / 1024, 1)
                except OSError:
                    pass
                return 0.0

            rss_mb = await loop.run_in_executor(None, _read_rss)

            sh_dict = _sh.to_dict()
            degraded = sh_dict.get("degraded", False)

            def _get_queue_backlog() -> int:
                try:
                    from .database import SessionLocal
                    from .models.outbox import OutboxEvent

                    _db2 = SessionLocal()
                    try:
                        return (
                            _db2.query(OutboxEvent)
                            .filter(OutboxEvent.processed_at.is_(None))
                            .count()
                        )
                    finally:
                        _db2.close()
                except Exception:
                    return 0

            queue_backlog = await loop.run_in_executor(None, _get_queue_backlog)

            # ── Grade determination ───────────────────────────────────────
            issues = []
            if not db_ok:
                issues.append("database_down")
            if not red_ok:
                issues.append("redis_down")
            if db_ok and db_ms > 200:
                issues.append(f"database_slow_{db_ms}ms")
            if red_ok and red_ms > 50:
                issues.append(f"redis_slow_{red_ms}ms")
            if rss_mb > 600:
                issues.append(f"memory_high_{rss_mb}MB")
            if queue_backlog > 100:
                issues.append(f"queue_backlog_{queue_backlog}")
            if degraded:
                issues.append("degraded_mode")

            critical = [i for i in issues if "down" in i]
            grade = "RED" if critical else ("YELLOW" if issues else "GREEN")

            # ── Track RED duration ────────────────────────────────────────
            now_mono = _t.monotonic()
            if grade == "RED" and _prev_grade != "RED":
                _red_since = now_mono
            elif grade != "RED":
                _red_since = 0.0

            # ── Alert logic: transition OR periodic RED reminder ──────────
            transition = grade != _prev_grade
            red_reminder = (
                grade == "RED" and (now_mono - _last_alert) >= _remind_secs and _red_since > 0
            )
            should_alert = (transition or red_reminder) and _webhook

            if should_alert:
                from datetime import datetime

                import httpx as _hx

                emoji = "🔴" if grade == "RED" else ("🟡" if grade == "YELLOW" else "✅")
                red_dur = ""
                if grade == "RED" and _red_since > 0:
                    red_dur = f" ({int(now_mono - _red_since)}s in RED)"
                payload = {
                    "text": (
                        f"{emoji} *GULA Platform* — `{_prev_grade}` → `{grade}`{red_dur}\n"
                        f"Issues: {', '.join(issues) or 'none'}\n"
                        f"DB: {db_ms}ms  Redis: {red_ms}ms  "
                        f"Mem: {rss_mb}MB  Queue: {queue_backlog}\n"
                        f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    ),
                    "grade": grade,
                    "prev_grade": _prev_grade,
                    "issues": issues,
                    "metrics": {
                        "db_ms": db_ms,
                        "redis_ms": red_ms,
                        "memory_mb": rss_mb,
                        "queue_backlog": queue_backlog,
                    },
                }
                try:
                    async with _hx.AsyncClient(timeout=10) as _c:
                        await _c.post(_webhook, json=payload)
                    _last_alert = now_mono
                    logger.info("Health alert sent: %s → %s issues=%s", _prev_grade, grade, issues)
                except Exception as _e:
                    logger.warning("Health alert webhook failed: %s", _e)

            _prev_grade = grade

        except Exception as exc:
            logger.debug("Health watchdog error: %s", exc)

        # Faster retry when system is degraded, normal interval when healthy
        sleep_s = _retry_fast if _prev_grade == "RED" else _interval
        await _aio.sleep(sleep_s)


# ===== ADAPTIVE CONCURRENCY =====
async def _adaptive_concurrency_loop():
    """Dynamically tighten the concurrency cap when the DB is under stress.

    Logic:
    - Poll DB latency every 30s.
    - 2 consecutive slow readings (>300ms): halve _max to shed non-critical load.
    - 3 consecutive fast readings (<150ms): restore original _max.

    Prevents a slow DB from cascading into a full request pile-up:
    fewer in-flight requests → shorter queue → DB recovers faster.
    """
    import asyncio as _aio
    import time as _t

    from .database import check_db_connection as _db_check

    _orig = _MAX_CONCURRENT
    _slow_streak = 0
    _fast_streak = 0
    _slow_ms = 300
    _fast_ms = 150
    _slow_trig = 2
    _fast_trig = 3
    _poll = 30

    await _aio.sleep(45)  # let startup complete

    while True:
        try:
            loop = _aio.get_event_loop()
            t0 = _t.perf_counter()
            await loop.run_in_executor(None, _db_check)
            db_ms = (_t.perf_counter() - t0) * 1000

            if db_ms > _slow_ms:
                _slow_streak += 1
                _fast_streak = 0
            elif db_ms < _fast_ms:
                _fast_streak += 1
                _slow_streak = max(0, _slow_streak - 1)
            else:
                _slow_streak = max(0, _slow_streak - 1)
                _fast_streak = max(0, _fast_streak - 1)

            # Tighten when DB is consistently slow
            if _slow_streak >= _slow_trig:
                new_max = max(10, _orig // 2)
                if new_max != _orig:
                    logger.warning(
                        "Adaptive concurrency: DB slow %.0fms ×%d → cap %d→%d",
                        db_ms,
                        _slow_streak,
                        _orig,
                        new_max,
                    )
                    # Use the stored middleware instance instead of gc.get_objects()
                    if ConcurrencyLimitMiddleware._instance is not None:
                        ConcurrencyLimitMiddleware._instance._max = new_max
                    _orig = new_max

            # Restore when DB recovers
            elif _fast_streak >= _fast_trig and _orig < _MAX_CONCURRENT:
                logger.info(
                    "Adaptive concurrency: DB recovered %.0fms ×%d → restore to %d",
                    db_ms,
                    _fast_streak,
                    _MAX_CONCURRENT,
                )
                # Use the stored middleware instance instead of gc.get_objects()
                if ConcurrencyLimitMiddleware._instance is not None:
                    ConcurrencyLimitMiddleware._instance._max = _MAX_CONCURRENT
                _orig = _MAX_CONCURRENT
                _fast_streak = 0

        except Exception as exc:
            logger.debug("Adaptive concurrency check error: %s", exc)

        await _aio.sleep(_poll)


# ===== STARTUP WARMUP =====

# Tracks all background tasks so shutdown can cancel them cleanly.
_bg_tasks: set = set()


def _spawn(coro) -> "asyncio.Task":
    """Create a tracked background task that is auto-cancelled on shutdown."""
    task = asyncio.create_task(coro)
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


async def start_background_workers():
    """Launch background workers — only when this process is the worker runtime.

    Runtime isolation rules (see config.background_tasks_enabled):
      - API runtime         → never launches maintenance loops
      - Worker runtime      → launches all loops
      - Test / CLI runtime  → never launches anything

    The double-gate (FEATURE_BACKGROUND_TASKS + RUNTIME_MODE=worker) ensures
    a misconfigured env var alone can't promote an API process into a worker.
    """
    if not background_tasks_enabled():
        logger.info(
            "Background tasks disabled (RUNTIME_MODE=%s). "
            "Maintenance loops will NOT start in this process.",
            RUNTIME_MODE,
        )
        return

    from .core.self_healing import RecoveryWorker
    from .services.outbox_service import OutboxWorker

    _spawn(OutboxWorker.background_loop())
    logger.info("Outbox worker started")

    _spawn(RecoveryWorker.background_loop())
    logger.info("Recovery worker started")

    _spawn(_health_alert_loop())
    logger.info("Health alert watchdog started")

    _spawn(_adaptive_concurrency_loop())
    logger.info("Adaptive concurrency monitor started")

    from .core.auto_repair import auto_repair as _auto_repair

    _spawn(_auto_repair.run())
    logger.info("Auto-repair engine started")

    # Edge AI maintenance — reaps stale tasks, marks offline devices, prunes telemetry.
    # Skipped under ENV=test so the loop's SessionLocal() calls (which target the
    # production engine, not the test fixture session) can't touch a Postgres DB
    # whose edge_* tables aren't created by the test fixture.
    if os.getenv("ENV") != "test":
        from .edge.maintenance import edge_maintenance_loop

        _spawn(edge_maintenance_loop())
        logger.info("Edge maintenance loop started")

    # ── Restore sliding window from Redis (DB error history survives restarts) ─
    from .database import restore_db_window_from_redis

    restore_db_window_from_redis()
    logger.info("DB sliding window restored from Redis")


async def warmup():
    """Pre-load hot-path modules so first real request is fast."""
    import time as _t

    t0 = _t.perf_counter()
    try:
        # Resolve deferred import inside get_flag → check_critical
        from .routes.critical_alerts import check_critical
        from .services.interpretation import get_flag, interpret_result

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
    from .database import check_db_connection_detail

    db_status, db_detail = check_db_connection_detail()
    pool = get_pool_status()
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "system_ready": system_ready,
        "database": db_status,  # "ok" | "refused" | "auth_failed" | "timeout" | "error"
        "database_detail": db_detail,  # human-readable reason for failures
        "degraded_mode": sys_health.degraded,
        "degradation_level": sys_health.degradation_level.name,
        "circuits": sys_health.to_dict()["circuits"],
        "pool": pool,
        "timestamp": datetime.now(UTC).isoformat(),
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
    from .core.self_healing import health as sys_health
    from .core.startup_guard import is_system_ready, system_ready

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
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/health/deep", tags=["system"])
def health_deep():
    """
    Deep diagnostic endpoint — comprehensive latency + queue + memory snapshot.
    Designed for monitoring dashboards and alerting (Prometheus, Grafana, etc.).

    Returns overall health grade:
      GREEN   — all components healthy, latencies normal
      YELLOW  — degraded performance, some components slow
      RED     — one or more critical components failing

    Always returns HTTP 200 — check 'grade' field for actual state.
    Accessible without authentication (all values are non-sensitive metrics).
    """
    import time as _t

    t_start = _t.perf_counter()

    # ── 1. Database latency ──────────────────────────────────────────────────
    db_ok, db_ms, db_err = False, -1.0, None
    try:
        from sqlalchemy import text as _text

        from .database import SessionLocal

        _db = SessionLocal()
        try:
            t0 = _t.perf_counter()
            _db.execute(_text("SELECT 1"))
            db_ms = round((_t.perf_counter() - t0) * 1000, 1)
            db_ok = True
        finally:
            _db.close()
    except Exception as e:
        db_err = str(e)[:120]

    # ── 2. Redis latency ─────────────────────────────────────────────────────
    red_ok, red_ms, red_err = False, -1.0, None
    try:
        from .security.redis_client import cache as _r

        t0 = _t.perf_counter()
        _r.ping()
        red_ms = round((_t.perf_counter() - t0) * 1000, 1)
        red_ok = True
    except Exception as e:
        red_err = str(e)[:80]

    # ── 3. Queue backlog (OutboxEvent undelivered rows) ──────────────────────
    queue_backlog, queue_err = 0, None
    try:
        from .database import SessionLocal

        _db2 = SessionLocal()
        try:
            queue_backlog = (
                _db2.query(OutboxEvent).filter(OutboxEvent.processed_at.is_(None)).count()
            )
        finally:
            _db2.close()
    except Exception as e:
        queue_err = str(e)[:80]

    # ── 4. Memory RSS ────────────────────────────────────────────────────────
    rss_mb = 0.0
    try:
        with open("/proc/self/status") as _f:
            for line in _f:
                if line.startswith("VmRSS:"):
                    rss_mb = round(int(line.split()[1]) / 1024, 1)
                    break
    except OSError:
        pass

    # ── 5. Circuit breaker state ─────────────────────────────────────────────
    circuits = {}
    degraded = False
    try:
        from .core.self_healing import health as _sh

        sh = _sh.to_dict()
        circuits = sh.get("circuits", {})
        degraded = sh.get("degraded", False)
    except Exception:
        pass

    # ── 6. Uptime ────────────────────────────────────────────────────────────
    from .routes.metrics import _START as PROC_START

    uptime_s = int(_t.time() - PROC_START)

    # ── 7. Active concurrent requests (from ConcurrencyLimitMiddleware) ─────────
    active_requests = 0
    with suppress(Exception):
        active_requests = ConcurrencyLimitMiddleware._active

    # ── 8. Determine health grade ─────────────────────────────────────────────
    issues = []
    if not db_ok:
        issues.append("database_down")
    elif db_ms > 200:
        issues.append("database_slow")
    if not red_ok:
        issues.append("redis_down")
    elif red_ms > 50:
        issues.append("redis_slow")
    if queue_backlog > 100:
        issues.append("queue_backlog_high")
    if rss_mb > 800:
        issues.append("memory_high")
    if degraded:
        issues.append("degraded_mode")
    if any("down" in i for i in issues):
        grade = "RED"
    elif issues:
        grade = "YELLOW"
    else:
        grade = "GREEN"

    total_ms = round((_t.perf_counter() - t_start) * 1000, 1)

    return {
        "grade": grade,
        "issues": issues,
        "components": {
            "database": {"ok": db_ok, "latency_ms": db_ms, "error": db_err},
            "redis": {"ok": red_ok, "latency_ms": red_ms, "error": red_err},
            "queue": {"backlog": queue_backlog, "error": queue_err},
        },
        "process": {
            "memory_rss_mb": rss_mb,
            "uptime_s": uptime_s,
            "uptime_h": round(uptime_s / 3600, 2),
            "active_requests": active_requests,
            "degraded_mode": degraded,
        },
        "circuits": circuits,
        "check_duration_ms": total_ms,
        "version": APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "auto_repair": (
            lambda: __import__("app.core.auto_repair", fromlist=["auto_repair"]).auto_repair.stats()
        )(),
    }


# ===== KERNEL HEALTH =====
@app.get("/health/kernel", tags=["system"])
async def kernel_health():
    """
    Kernel health and diagnostics.
    Returns the Kernel's internal state, component status, and uptime.
    Bypasses all middlewares so it is always reachable.
    """
    try:
        from .kernel.integration import get_kernel_health

        return await get_kernel_health()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "kernel_initialized": False,
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
