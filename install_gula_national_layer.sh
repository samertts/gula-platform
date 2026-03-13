#!/bin/bash

echo "Installing GULA National Health Layer..."

BASE=~/gula-platform/backend/app

mkdir -p $BASE/routes
mkdir -p $BASE/services
mkdir -p $BASE/legal
mkdir -p $BASE/notifications

########################################
echo "Legal consent system"
########################################

cat > $BASE/legal/consent.py <<'EOF'

from datetime import datetime

def record_consent(user_id,terms_version,privacy_version):

    return {
        "user_id":user_id,
        "terms_version":terms_version,
        "privacy_version":privacy_version,
        "timestamp":datetime.utcnow()
    }

EOF

########################################
echo "Citizen registration"
########################################

cat > $BASE/routes/register.py <<'EOF'

from fastapi import APIRouter
import uuid

router=APIRouter()

@router.post("/register")

def register():

    patient_uuid=str(uuid.uuid4())

    return {

        "patient_uuid":patient_uuid,

        "message":"account created"

    }

EOF

########################################
echo "National ID masking"
########################################

cat > $BASE/services/national_id.py <<'EOF'

def mask_national_id(nid):

    if len(nid)<8:

        return nid

    return nid[:4]+"********"+nid[-4:]

EOF

########################################
echo "Samir guidance engine"
########################################

cat > $BASE/services/samir_engine.py <<'EOF'

def samir(page):

    tips={

        "dashboard":"هذه لوحة التحكم في منصة GULA",

        "worklist":"هنا تظهر العينات التي تحتاج معالجة",

        "results":"يمكنك مراجعة النتائج الطبية هنا",

        "identity":"يمكنك التحقق من الهوية الصحية هنا"

    }

    return tips.get(page,"مرحبا أنا سامر مرشدك في المنصة")

EOF

########################################
echo "Ali Reza medical analysis"
########################################

cat > $BASE/services/ali_reza_engine.py <<'EOF'

def analyze(test,value):

    if test=="glucose":

        if value>180:

            return "ارتفاع شديد في سكر الدم"

        if value>140:

            return "ارتفاع محتمل في السكر"

    if test=="hb":

        if value<10:

            return "فقر دم محتمل"

    if test=="creatinine":

        if value>1.5:

            return "احتمال ضعف وظائف الكلى"

    return "القيمة ضمن الطبيعي"

EOF

########################################
echo "Telegram notification"
########################################

cat > $BASE/notifications/telegram.py <<'EOF'

import requests

def send_telegram(bot_token,chat_id,message):

    url=f"https://api.telegram.org/bot{bot_token}/sendMessage"

    requests.post(url,json={

        "chat_id":chat_id,

        "text":message

    })

EOF

########################################
echo "Health record API"
########################################

cat > $BASE/routes/ehr.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.get("/ehr")

def ehr():

    return {

        "records":[

            {"type":"lab","test":"CBC","result":"normal"},

            {"type":"lab","test":"glucose","result":"105"}

        ]

    }

EOF

########################################
echo "Epidemiology placeholder"
########################################

cat > $BASE/services/epidemiology.py <<'EOF'

def detect_outbreak(data):

    if len(data)>1000:

        return "possible outbreak"

    return "normal"

EOF

########################################
echo "Inject routes to API"
########################################

MAIN=~/gula-platform/backend/app/main.py

if ! grep -q "register" $MAIN; then

echo "from .routes import register" >> $MAIN
echo "from .routes import ehr" >> $MAIN

echo "app.include_router(register.router)" >> $MAIN
echo "app.include_router(ehr.router)" >> $MAIN

fi

########################################
echo "Restart backend"
########################################

cd ~/gula-platform

docker compose build gula-backend
docker compose up -d gula-backend

echo "GULA national layer installed successfully"
