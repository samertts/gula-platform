from app.national.reference.base import ReferenceEntity
from sqlalchemy import Column, String


class ICD10Code(ReferenceEntity):
    __tablename__ = "ref_icd10_codes"
    icd_code = Column(String(10), nullable=False, unique=True, index=True)
    category = Column(String(5), nullable=True)
    chapter = Column(String(10), nullable=True)
    chapter_name = Column(String(200), nullable=True)
    block = Column(String(10), nullable=True)
    block_name = Column(String(200), nullable=True)
    who_status = Column(String(20), nullable=True)
