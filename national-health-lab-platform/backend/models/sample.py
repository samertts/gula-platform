from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database.db import Base

class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"))

    sample_type = Column(String)
    status = Column(String)

    collected_at = Column(DateTime, default=datetime.utcnow)
