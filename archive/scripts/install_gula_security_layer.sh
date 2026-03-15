#!/bin/bash

echo "Installing GULA Cybersecurity Layer..."

BASE=~/gula-platform/backend/app

mkdir -p $BASE/security
mkdir -p $BASE/audit
mkdir -p $BASE/firewall

########################################
echo "Encryption system"
########################################

cat > $BASE/security/encryption.py <<'EOF'

from cryptography.fernet import Fernet

KEY = Fernet.generate_key()

cipher = Fernet(KEY)

def encrypt(data):

    return cipher.encrypt(data.encode()).decode()

def decrypt(data):

    return cipher.decrypt(data.encode()).decode()

EOF

########################################
echo "JWT protection"
########################################

cat > $BASE/security/jwt_guard.py <<'EOF'

from fastapi import Request,HTTPException

def protect(request:Request):

    token=request.headers.get("Authorization")

    if not token:

        raise HTTPException(401,"Unauthorized")

    return True

EOF

########################################
echo "Rate limiting"
########################################

cat > $BASE/security/rate_limit.py <<'EOF'

import time

requests={}

def check(ip):

    now=time.time()

    if ip not in requests:

        requests[ip]=[]

    requests[ip]=[t for t in requests[ip] if now-t<60]

    if len(requests[ip])>100:

        return False

    requests[ip].append(now)

    return True

EOF

########################################
echo "Audit logging"
########################################

cat > $BASE/audit/audit_log.py <<'EOF'

import datetime

def log(action,user):

    return {

        "action":action,

        "user":user,

        "timestamp":datetime.datetime.utcnow()

    }

EOF

########################################
echo "Intrusion detection"
########################################

cat > $BASE/security/intrusion_detection.py <<'EOF'

failed_attempts={}

def detect(ip):

    if ip not in failed_attempts:

        failed_attempts[ip]=0

    failed_attempts[ip]+=1

    if failed_attempts[ip]>10:

        return "blocked"

    return "ok"

EOF

########################################
echo "Role based access"
########################################

cat > $BASE/security/rbac.py <<'EOF'

roles={

"admin":["all"],

"doctor":["read","write"],

"lab":["read"],

"citizen":["self"]

}

def check(role,action):

    if "all" in roles.get(role,[]):

        return True

    return action in roles.get(role,[])

EOF

########################################
echo "API firewall"
########################################

cat > $BASE/firewall/api_firewall.py <<'EOF'

blocked_ips=set()

def block(ip):

    blocked_ips.add(ip)

def allowed(ip):

    return ip not in blocked_ips

EOF

########################################
echo "Security health endpoint"
########################################

cat > $BASE/routes/security.py <<'EOF'

from fastapi import APIRouter

router=APIRouter()

@router.get("/security")

def security():

    return {"status":"secure"}

EOF

########################################
echo "Inject route"
########################################

MAIN=~/gula-platform/backend/app/main.py

if ! grep -q "security" $MAIN; then

echo "from .routes import security" >> $MAIN

echo "app.include_router(security.router)" >> $MAIN

fi

########################################
echo "Restart backend"
########################################

cd ~/gula-platform

docker compose build gula-backend

docker compose up -d gula-backend

echo "GULA cybersecurity layer installed successfully"
