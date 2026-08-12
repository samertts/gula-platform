from sqlalchemy import Column, String

from app.national.reference.base import ReferenceEntity


class Specialty(ReferenceEntity):
    __tablename__ = "ref_specialties"
    category = Column(String(100), nullable=True)
    specialty_group = Column(String(100), nullable=True)
