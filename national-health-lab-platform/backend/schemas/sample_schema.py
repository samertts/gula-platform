from pydantic import BaseModel
from datetime import datetime

class SampleCreate(BaseModel):
    patient_id: int
    sample_type: str
    status: str

class SampleResponse(BaseModel):
    id: int
    patient_id: int
    sample_type: str
    status: str
    collected_at: datetime

    class Config:
        orm_mode = True
