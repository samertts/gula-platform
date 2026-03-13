#!/bin/bash

echo "Installing full GULA system..."

BASE=~/gula-platform/backend

mkdir -p $BASE/app/routes
mkdir -p $BASE/app/services
mkdir -p $BASE/app/security

########################################
echo "Auth system"
########################################

cat > $BASE/app/security/auth.py <<'EOF'

from fastapi import HTTPException
from datetime import datetime,timedelta
import jwt

SECRET="GULA_SECRET"

def create_token(user):

    payload={
        "user":user,
        "exp":datetime.utcnow()+timedelta(hours=24)
    }

    return jwt.encode(payload,SECRET,algorithm="HS256")

def verify_token(token):

    try:

        return jwt.decode(token,SECRET,algorithms=["HS256"])

    except:

        raise HTTPException(401,"Invalid token")

EOF

########################################
echo "Login route"
########################################

cat > $BASE/app/routes/login.py <<'EOF'

from fastapi import APIRouter
from pydantic import BaseModel
from ..security.auth import create_token

router=APIRouter()

class Login(BaseModel):

    username:str
    password:str

@router.post("/login")

def login(data:Login):

    token=create_token(data.username)

    return {"token":token}

EOF

########################################
echo "Identity API"
########################################

cat > $BASE/app/routes/identity.py <<'EOF'

from fastapi import APIRouter
import uuid

router=APIRouter()

@router.post("/identity/create")

def create_identity():

    return {

        "patient_uuid":str(uuid.uuid4())

    }

EOF

########################################
echo "Lab API"
########################################

cat > $BASE/app/routes/labs.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.get("/labs")

def labs():

    return [

        {"name":"CBC","status":"available"},
        {"name":"Glucose","status":"available"}

    ]

EOF

########################################
echo "Results API"
########################################

cat > $BASE/app/routes/results.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.get("/results")

def results():

    return [

        {"test":"CBC","value":"Normal"},
        {"test":"Glucose","value":"105"}

    ]

EOF

########################################
echo "Notification API"
########################################

cat > $BASE/app/routes/notifications.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.post("/notify")

def notify():

    return {"status":"sent"}

EOF

########################################
echo "Samir AI"
########################################

cat > $BASE/app/services/samir.py <<'EOF'

def samir_help(page):

    tips={

        "dashboard":"هذه لوحة التحكم",

        "worklist":"هذه قائمة العينات",

        "results":"يمكنك مراجعة نتائجك هنا"

    }

    return tips.get(page,"مرحبا انا سامر")

EOF

########################################
echo "Ali Reza AI"
########################################

cat > $BASE/app/services/ali_reza.py <<'EOF'

def analyze(test,value):

    if test=="glucose":

        if value>140:

            return "ارتفاع محتمل في السكر"

    if test=="hb":

        if value<11:

            return "قد يكون فقر دم"

    return "القيمة ضمن الطبيعي"

EOF

########################################
echo "Dashboard API"
########################################

cat > $BASE/app/routes/dashboard.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.get("/dashboard")

def dashboard():

    return {

        "patients":1200,
        "samples":300,
        "tests":850,
        "critical":3

    }

EOF

########################################
echo "Main API"
########################################

cat > $BASE/app/main.py <<'EOF'

from fastapi import FastAPI

from .routes import login
from .routes import identity
from .routes import labs
from .routes import results
from .routes import notifications
from .routes import dashboard

app=FastAPI(title="GULA Platform API")

app.include_router(login.router)
app.include_router(identity.router)
app.include_router(labs.router)
app.include_router(results.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)

@app.get("/")

def root():

    return {"system":"GULA running"}

EOF

########################################
echo "Rebuild backend"
########################################

cd ~/gula-platform

docker compose build gula-backend

docker compose up -d gula-backend

echo "GULA full system installed"
