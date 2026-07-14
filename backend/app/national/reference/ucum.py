from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class UCUMUnit(ReferenceEntity):
    __tablename__ = "ref_ucum_units"
    ucum_code = Column(String(20), nullable=False, unique=True, index=True)
    unit_system = Column(String(50), nullable=True)
    dimensionless = Column(String(1), default="0")
    si_unit = Column(String(50), nullable=True)
    conversion_factor = Column(String(50), nullable=True)
