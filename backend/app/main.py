import os
import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
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

# ===== ROUTES =====
from .routes import login, register, patients, results, dashboard, labs
from .routes import identity, notifications, ehr, security
from .routes import national_identity, insurance, device_results
from .routes import qr, id_scan, admin, samples
from .routes import quality_control, critical_alerts, batch
from .routes import mobile, compliance

# Core routes
app.include_router(login.router)
app.include_router(register.router)
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


# ===== STARTUP WARMUP =====
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
    Health check endpoint for load balancers and monitoring.
    Returns system status and version information.
    """
    db_ok = check_db_connection()
    pool = get_pool_status()
    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "platform": APP_NAME,
        "platform_ar": PLATFORM_NAME_AR,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "production"),
        "database": "connected" if db_ok else "disconnected",
        "pool": pool,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }


@app.get("/health/ready", tags=["system"])
def readiness():
    """Kubernetes-style readiness probe - returns 503 if not ready to serve traffic."""
    from .security.redis_client import cache

    db_ok = check_db_connection()
    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database_unavailable"},
        )

    redis_ok = True
    try:
        cache.set("_health", "1", ex=10)
    except Exception:
        redis_ok = False

    if not redis_ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "redis_unavailable"},
        )

    return {"status": "ready", "database": "ok", "cache": "ok"}


@app.get("/health/live", tags=["system"])
def liveness():
    """Kubernetes-style liveness probe - always returns 200 if process is alive."""
    return {"status": "alive", "version": APP_VERSION}


@app.get("/r/{token}/pdf")
def serve_result_pdf_redirect(token: str, request: Request):
    """Direct PDF download for result."""
    from .routes.results import download_result_pdf
    from .database import SessionLocal
    db = SessionLocal()
    try:
        return download_result_pdf(token, request, db)
    finally:
        db.close()


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
def on_startup():
    """Bootstrap the system on first run."""
    logger.info("GULA Platform %s starting up...", APP_VERSION)

    # Verify database connectivity before accepting requests
    if not check_db_connection():
        logger.error("DATABASE CONNECTION FAILED at startup!")
    else:
        logger.info("Database connection verified")

    _migrate_perm_version()
    _seed_test_types()
    _ensure_master_admin()
    logger.info("GULA Platform %s ready", APP_VERSION)


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
        if True:
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
