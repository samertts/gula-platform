from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import SessionLocal
from services.sample_service import create_sample, get_samples
from schemas.sample_schema import SampleCreate, SampleResponse
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/samples", response_model=List[SampleResponse])
def list_samples(db: Session = Depends(get_db)):
    return get_samples(db)

@router.post("/samples")
def add_sample(sample: SampleCreate, db: Session = Depends(get_db)):
    return create_sample(db, sample)
