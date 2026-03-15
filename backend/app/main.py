import os
import traceback
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse

from .database import Base, engine
from .config import APP_NAME, APP_VERSION

# Import all models so they are registered with Base
from .models import Lab, LabUser, User, Patient, TestType, LabOrder, LabResult, AuditLog, Sample

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="GULA - Smart Health Platform for Labs",
)

# ===== GLOBAL ERROR HANDLER =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled errors - return friendly JSON instead of 500 stack trace."""
    print(f"[GULA ERROR] {request.method} {request.url}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong. Please try again.",
            "detail_ar": "حدث خطأ. يرجى المحاولة مرة أخرى.",
        },
    )


# CORS - use explicit origins from env, fallback to same-origin only
_allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins or ["*"],
    allow_credentials=bool(_allowed_origins),
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ===== ROUTES =====
from .routes import login, register, patients, results, dashboard, labs
from .routes import identity, notifications, ehr, security
from .routes import national_identity, insurance, device_results
from .routes import qr, id_scan, admin, samples

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

# Admin routes
app.include_router(admin.router)

# Legacy routes (national_identity, insurance - kept for API compatibility)
app.include_router(national_identity.router)
app.include_router(insurance.router)


# ===== FRONTEND SERVING =====
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", "/app/static_frontend"))
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).parent.parent.parent.parent / "frontend"


@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Serve the main SPA."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return JSONResponse({"system": "GULA Platform", "version": APP_VERSION, "status": "running"})


@app.get("/r/{token}", response_class=HTMLResponse)
def serve_result_page(token: str):
    """Serve result HTML page for public result links."""
    result_file = FRONTEND_DIR / "result.html"
    if result_file.exists():
        return HTMLResponse(content=result_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Result page not found</h1>", status_code=404)


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


@app.get("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION}


# Static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


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


# ===== STARTUP =====
@app.on_event("startup")
def on_startup():
    """Bootstrap the system on first run."""
    _seed_test_types()
    _ensure_master_admin()


def _seed_test_types():
    """Seed test types catalog if empty."""
    from .database import SessionLocal
    from .models.test_type import TestType

    db = SessionLocal()
    try:
        if db.query(TestType).count() == 0:
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
            print(f"[GULA] Seeded {len(test_types)} test types")
    finally:
        db.close()


def _ensure_master_admin():
    """Create master admin on first startup if not exists."""
    from .routes.admin import ensure_master_admin
    ensure_master_admin()
