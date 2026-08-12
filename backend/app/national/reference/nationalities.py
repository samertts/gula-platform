from sqlalchemy import Column, String

from app.national.reference.base import ReferenceEntity


class Nationality(ReferenceEntity):
    __tablename__ = "ref_nationalities"
    country_code = Column(String(2), nullable=False)
    demonym = Column(String(100), nullable=True)
    demonym_ar = Column(String(100), nullable=True)
