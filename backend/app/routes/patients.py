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
