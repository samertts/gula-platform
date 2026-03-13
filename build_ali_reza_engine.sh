#!/bin/bash

BASE=~/gula-platform
AI=$BASE/ai

mkdir -p $AI

echo "Installing Ali Reza Medical AI..."

########################################
# Medical analysis engine
########################################

cat > $AI/ali_reza_engine.py <<'EOF'

def analyze(test,value):

    advice=None

    if test=="glucose":

        if value>180:
            advice="ارتفاع شديد في سكر الدم"

        elif value>140:
            advice="ارتفاع محتمل في مستوى السكر"

    if test=="hb":

        if value<10:
            advice="فقر دم محتمل"

    if test=="creatinine":

        if value>1.5:
            advice="قد يكون هناك ضعف في وظائف الكلى"

    return advice

EOF

########################################
# API medical endpoint
########################################

mkdir -p $BASE/api/routes

cat > $BASE/api/routes/medical.py <<'EOF'

from fastapi import APIRouter
from ai.ali_reza_engine import analyze

router=APIRouter()

@router.post("/api/medical/analyze")
def medical_analysis(data:dict):

    test=data.get("test")
    value=data.get("value")

    advice=analyze(test,value)

    return {
        "doctor":"Ali Reza",
        "analysis":advice
    }

EOF

########################################
# Inject route into main API
########################################

if ! grep -q "medical" $BASE/api/main.py; then

echo "" >> $BASE/api/main.py
echo "from routes.medical import router as medical_router" >> $BASE/api/main.py
echo "app.include_router(medical_router)" >> $BASE/api/main.py

fi

########################################
# Restart API
########################################

cd $BASE

docker compose restart gula-api

echo "Ali Reza AI installed successfully"
