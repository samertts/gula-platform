from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database
from database.db import engine, Base

# Models - import all to ensure tables are created
from models.user import User
from models.patient import Patient
from models.lab import Laboratory
from models.sample import Sample
from models.test_catalog import TestCatalog
from models.lab_order import LabOrder, LabOrderItem
from models.test_result import TestResult

# Routers
from routers.auth import router as auth_router
from routers.lab_workflow import router as lab_router
from routers.users import router as user_router
from routers import patients
from routers import samples

# App
app = FastAPI(
    title="National Health Lab Platform",
    version="1.0.0",
    description="منصة وطنية لإدارة المختبرات الصحية - NHOP Lab Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(auth_router)
app.include_router(lab_router)
app.include_router(user_router, prefix="/api", tags=["Users (Legacy)"])
app.include_router(patients.router, prefix="/api", tags=["Patients (Legacy)"])
app.include_router(samples.router, prefix="/api", tags=["Samples (Legacy)"])


@app.get("/")
def home():
    return {
        "status":      "National Health Lab Platform Running",
        "system":      "NHLP",
        "version":     "1.0.0",
        "description": "منصة المختبرات الصحية الوطنية"
    }


@app.get("/health")
def health():
    return {"status": "ok", "system": "NHLP"}
