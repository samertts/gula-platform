# Database
from database.db import engine, Base

# Models
from models.user import User
from models.patient import Patient
from models.lab import Laboratory
from models.sample import Sample

# Routers
from routers.users import router as user_router
from routers import patients
from routers import samples

# إنشاء التطبيق
app = FastAPI(
    title="National Health Lab Platform",
    version="0.1.0",
    description="National platform for laboratory information management and epidemiological surveillance"
)

# إنشاء الجداول في قاعدة البيانات
Base.metadata.create_all(bind=engine)

# ربط الـ Routers
app.include_router(user_router, tags=["Users"])
app.include_router(patients.router, tags=["Patients"])
app.include_router(samples.router, tags=["samples"])

# Endpoint رئيسي للنظام
@app.get("/")
def home():
    return {
        "status": "National Health Lab Platform Running",
        "system": "NHLP",
        "version": "0.1.0"
    }
