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
