#!/bin/bash

BASE=~/gula-platform
API=$BASE/api

echo "Installing GULA API..."

mkdir -p $API

########################################
echo "Creating FastAPI backend"
########################################

cat > $API/main.py <<'EOF'

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

EOF

########################################
echo "Creating Dockerfile"
########################################

cat > $API/Dockerfile <<'EOF'

FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]

EOF

########################################
echo "Updating docker-compose"
########################################

if ! grep -q "gula-api" $BASE/docker-compose.yml; then

cat >> $BASE/docker-compose.yml <<'EOF'

  gula-api:
    build: ./api
    container_name: gula-api
    ports:
      - "8000:8000"
    restart: unless-stopped

EOF

fi

########################################
echo "Starting API container"
########################################

cd $BASE

docker compose up -d --build

echo "GULA API installed successfully"

echo "Test endpoints:"

echo "http://SERVER_IP:8000/api/health"
echo "http://SERVER_IP:8000/api/dashboard"
