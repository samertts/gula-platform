from pydantic import BaseModel
from datetime import date

class PatientCreate(BaseModel):
    full_name: str
    gender: str
    birth_date: date
    phone: str
    national_id: str

class PatientResponse(BaseModel):
    id: int
    full_name: str
    gender: str
    birth_date: date
    phone: str
    national_id: str

    class Config:
        from_attributes = True
