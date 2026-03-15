#!/bin/bash

echo "Installing GULA National Gateways..."

BASE=~/gula-platform/backend/app

mkdir -p $BASE/gateways
mkdir -p $BASE/routes

########################################
echo "National Identity Gateway"
########################################

cat > $BASE/gateways/national_identity_gateway.py <<'EOF'
"""
Gateway placeholder for Iraqi National ID system
(Prepared for future Ministry of Interior API integration)
"""

def verify_national_id(national_id):

    if len(national_id) not in [12,16]:
        return {"valid":False}

    return {
        "valid":True,
        "source":"local_validation",
        "message":"Awaiting government registry integration"
    }
EOF

########################################
echo "Health Insurance Gateway"
########################################

cat > $BASE/gateways/insurance_gateway.py <<'EOF'
"""
Gateway placeholder for Iraqi Health Insurance system
Law No.22 of 2020
"""

def check_insurance(insurance_id):

    if not insurance_id:
        return {"insured":False}

    return {
        "insured":True,
        "provider":"national_health_insurance",
        "status":"pending_verification"
    }
EOF

########################################
echo "Laboratory Device Gateway"
########################################

cat > $BASE/gateways/lab_device_gateway.py <<'EOF'
"""
Interface layer for laboratory analyzers
HL7 / ASTM / LIS integration
"""

def receive_device_result(sample_id,test,value):

    return {
        "sample":sample_id,
        "test":test,
        "value":value,
        "status":"received"
    }
EOF

########################################
echo "Identity API route"
########################################

cat > $BASE/routes/national_identity.py <<'EOF'
from fastapi import APIRouter
from ..gateways.national_identity_gateway import verify_national_id

router = APIRouter()

@router.post("/national-id/verify")
def verify(data:dict):

    national_id=data.get("national_id")

    return verify_national_id(national_id)
EOF

########################################
echo "Insurance API route"
########################################

cat > $BASE/routes/insurance.py <<'EOF'
from fastapi import APIRouter
from ..gateways.insurance_gateway import check_insurance

router=APIRouter()

@router.get("/insurance/{insurance_id}")

def insurance(insurance_id:str):

    return check_insurance(insurance_id)
EOF

########################################
echo "Device API route"
########################################

cat > $BASE/routes/device_results.py <<'EOF'
from fastapi import APIRouter
from ..gateways.lab_device_gateway import receive_device_result

router=APIRouter()

@router.post("/device/result")

def device_result(data:dict):

    return receive_device_result(
        data.get("sample"),
        data.get("test"),
        data.get("value")
    )
EOF

########################################
echo "Inject routes into main API"
########################################

MAIN=~/gula-platform/backend/app/main.py

if ! grep -q "national_identity" $MAIN; then

echo "from .routes import national_identity" >> $MAIN
echo "from .routes import insurance" >> $MAIN
echo "from .routes import device_results" >> $MAIN

echo "app.include_router(national_identity.router)" >> $MAIN
echo "app.include_router(insurance.router)" >> $MAIN
echo "app.include_router(device_results.router)" >> $MAIN

fi

########################################
echo "Restart backend"
########################################

cd ~/gula-platform

docker compose build gula-backend
docker compose up -d gula-backend

echo "GULA National Gateways installed successfully"
