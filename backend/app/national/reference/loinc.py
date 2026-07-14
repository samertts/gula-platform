from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String, Text


class LOINCCode(ReferenceEntity):
    __tablename__ = "ref_loinc_codes"
    loinc_num = Column(String(10), nullable=False, unique=True, index=True)
    component = Column(Text, nullable=True)
    property = Column(String(50), nullable=True)
    time_aspect = Column(String(10), nullable=True)
    system = Column(String(100), nullable=True)
    scale_type = Column(String(20), nullable=True)
    method_type = Column(String(100), nullable=True)
    classification = Column(String(50), nullable=True)
    status = Column(String(20), nullable=True)
