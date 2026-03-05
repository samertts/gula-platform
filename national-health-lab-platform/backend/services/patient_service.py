from sqlalchemy.orm import Session
from models.patient import Patient

def create_patient(db: Session, patient):
    new_patient = Patient(**patient.dict())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

def get_patients(db: Session):
    return db.query(Patient).all()
