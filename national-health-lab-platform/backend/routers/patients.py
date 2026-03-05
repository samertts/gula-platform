from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.db import SessionLocal
from schemas.patient_schema import PatientCreate, PatientResponse
from services.patient_service import create_patient, get_patients

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/patients", response_model=List[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    return get_patients(db)

@router.post("/patients", response_model=PatientResponse)
def add_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    return create_patient(db, patient)
