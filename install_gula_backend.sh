#!/bin/bash

echo "Installing GULA backend API..."

BASE=~/gula-platform/backend

mkdir -p $BASE
mkdir -p $BASE/app
mkdir -p $BASE/app/routes
mkdir -p $BASE/app/models

########################################
echo "Creating requirements"
########################################

cat > $BASE/requirements.txt <<EOF
fastapi
uvicorn
psycopg2-binary
sqlalchemy
python-multipart
pydantic
EOF

########################################
echo "Creating database connection"
########################################

cat > $BASE/app/database.py <<EOF
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@host.docker.internal:5432/gula"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
EOF

########################################
echo "Creating models"
########################################

cat > $BASE/app/models/patient.py <<EOF
from sqlalchemy import Column,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Patient(Base):

    __tablename__ = "health_identity"

    patient_uuid = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)

    insurance_id = Column(String)

    health_card_number = Column(String)
EOF

########################################
echo "Creating routes"
########################################

cat > $BASE/app/routes/patients.py <<EOF
from fastapi import APIRouter
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.patient import Patient

router = APIRouter()

@router.get("/patients")

def list_patients():

    db:Session = SessionLocal()

    patients = db.query(Patient).all()

    return patients
EOF

########################################
echo "Creating main API"
########################################

cat > $BASE/app/main.py <<EOF
from fastapi import FastAPI
from .routes import patients

app = FastAPI(title="GULA API")

app.include_router(patients.router)

@app.get("/")
def root():

    return {"system":"GULA platform running"}
EOF

########################################
echo "Creating Dockerfile"
########################################

cat > $BASE/Dockerfile <<EOF
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
EOF

########################################
echo "Creating docker-compose service"
########################################

cat >> ~/gula-platform/docker-compose.yml <<EOF

  gula-backend:

    build: ./backend

    container_name: gula-backend

    ports:
      - "8000:8000"

EOF

########################################
echo "Building backend container"
########################################

cd ~/gula-platform

docker compose build gula-backend

docker compose up -d gula-backend

echo "GULA backend installed successfully"
