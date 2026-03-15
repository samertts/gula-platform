
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GULA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.get("/api/dashboard")
def dashboard():

    return {
        "patients":1200,
        "samples":320,
        "tests":890,
        "critical":5
    }

@app.get("/api/worklist")
def worklist():

    return [

        {
            "sample":"A101",
            "patient":"Ali",
            "test":"CBC",
            "status":"Pending"
        },

        {
            "sample":"A102",
            "patient":"Sara",
            "test":"Glucose",
            "status":"Processing"
        }

    ]

@app.get("/api/patients")
def patients():

    return [

        {"name":"Ali Hassan"},
        {"name":"Sara Ahmed"},
        {"name":"Omar Khalid"}

    ]

@app.get("/api/results")
def results():

    return [

        {
            "patient":"Ali Hassan",
            "test":"Glucose",
            "value":160
        },

        {
            "patient":"Sara Ahmed",
            "test":"HB",
            "value":9
        }

    ]


from routes.medical import router as medical_router
app.include_router(medical_router)
