from sqlalchemy import Column, Integer, String, Date
from database.db import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    gender = Column(String)
    birth_date = Column(Date)
    phone = Column(String)
    national_id = Column(String, unique=True)
