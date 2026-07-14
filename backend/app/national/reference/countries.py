from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class Country(ReferenceEntity):
    __tablename__ = "ref_countries"
    alpha2 = Column(String(2), nullable=False)
    alpha3 = Column(String(3), nullable=False)
    numeric_code = Column(String(3), nullable=True)
    phone_code = Column(String(5), nullable=True)
