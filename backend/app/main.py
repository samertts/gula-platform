from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .database import Base, engine
from .config import APP_NAME, APP_VERSION

# Import all models so they are registered with Base
from .models import Lab, LabUser, Patient, TestType, LabOrder, LabResult, AuditLog

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="GULA - Smart Health Platform for Labs",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
from .routes import login, register, patients, results, dashboard, labs
from .routes import identity, notifications, ehr, security
from .routes import national_identity, insurance, device_results
from .routes import qr, id_scan

app.include_router(login.router)
app.include_router(register.router)
app.include_router(patients.router)
app.include_router(results.router)
app.include_router(dashboard.router)
app.include_router(labs.router)
app.include_router(qr.router)
app.include_router(id_scan.router)
app.include_router(identity.router)
app.include_router(notifications.router)
app.include_router(ehr.router)
app.include_router(security.router)
app.include_router(national_identity.router)
app.include_router(insurance.router)
app.include_router(device_results.router)


@app.get("/")
def root():
    return {
        "system": "GULA Platform",
        "version": APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# Test types listing (public)
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


# Seed test types on startup
@app.on_event("startup")
def seed_test_types():
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
            ]
            db.add_all(test_types)
            db.commit()
    finally:
        db.close()
