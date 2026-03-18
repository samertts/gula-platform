import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .database import Base, engine, check_db_connection, get_pool_status
from .config import APP_NAME, APP_VERSION, IS_PRODUCTION

# Configure structured logging
logging.basicConfig(
    level=logging.WARNING if IS_PRODUCTION else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gula")

# Import all models so they are registered with Base
from .models import Lab, LabUser, User, Patient, TestType, LabOrder, LabResult, AuditLog, Sample, QualityControl

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="GULA - Smart Health Platform for Labs",
    docs_url=None if IS_PRODUCTION else "/docs",       # Disable docs in production
    redoc_url=None if IS_PRODUCTION else "/redoc",
)


# ===== GLOBAL ERROR HANDLER =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors - return friendly JSON instead of 500 stack trace."""
    logger.exception(f"{request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong. Please try again.",
            "detail_ar": "حدث خطأ. يرجى المحاولة مرة أخرى.",
        },
    )


# CORS - use explicit origins from env; default to platform domain (never wildcard)
_allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]
if not _allowed_origins:
    _allowed_origins = [
        "https://gula-platform.org",
        "http://gula-platform.org",
    ]
    # Only allow localhost in development
    if os.getenv("ENV", "production") == "development":
        _allowed_origins += ["http://localhost:8080", "http://localhost:80"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
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
                "SLOW REQUEST: %s %s took %.0fms (status=%d)",
                request.method, request.url.path, elapsed_ms, response.status_code
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
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ===== ROUTES =====
from .routes import login, register, patients, results, dashboard, labs
from .routes import identity, notifications, ehr, security
from .routes import national_identity, insurance, device_results
from .routes import qr, id_scan, admin, samples
from .routes import quality_control, critical_alerts, batch

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

# Legacy routes (national_identity, insurance - kept for API compatibility)
app.include_router(national_identity.router)
app.include_router(insurance.router)


# ===== HEALTH & STATUS =====
@app.get("/health")
def health():
    """Health check with database connectivity verification - lightweight."""
    db_ok = check_db_connection()
    pool = get_pool_status()
    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "version": APP_VERSION,
        "database": "connected" if db_ok else "disconnected",
        "pool": pool,
    }


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
@app.get("/test-types")
def list_test_types():
    from .database import SessionLocal
    from .models.test_type import TestType
    db = SessionLocal()
    try:
        types = db.query(TestType).all()
        return [
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

    _seed_test_types()
    _ensure_master_admin()
    logger.info("GULA Platform %s ready", APP_VERSION)


@app.on_event("shutdown")
def on_shutdown():
    """Graceful shutdown - close database connections."""
    logger.info("GULA Platform shutting down gracefully...")
    engine.dispose()
    logger.info("Database connections closed")


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
